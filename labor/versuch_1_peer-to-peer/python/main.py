
import os
import asyncio
import socket
import json
import sys
import tty
import termios
import time

from src.register import register
from src.msg_templates import move_msg, join_msg, join_reject_msg, join_ack_msg, player_entry, announce_msg, eliminated_msg
from src.msg_handles import handle_join, handle_join_ack, handle_join_reject, handle_announce, handle_move, handle_eliminated
from src.send_join import send_join
from src.viz import viz


GRID_SIZE = 16
MAX_LEN = 3
CLOCK = 0 # Lamport Clock
MAX_TIME = 3 # max allowed time of inactivity
TIMESTAMP_LAST_KEY_PRESS = None

PEERS = [
    ("127.0.0.1", 5000),
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002),
    ("127.0.0.1", 5003),
]

# players incl traces etc.
players = {}
    
 
async def on_key(sock):
    """
    function to receive from other peers
    """
    def update_and_send_move_msg():
        user_input = os.read(fd, 10).decode(errors="ignore")
        # input validation
        if user_input == "\x1b[A": user_input = "up"
        elif user_input == "\x1b[B": user_input = "down"
        elif user_input == "\x1b[D": user_input = "left"
        elif user_input == "\x1b[C": user_input = "right"
        else: 
            print("Falsche Taste.")
            return
        
        # clock
        global CLOCK
        CLOCK += 1

        global TIMESTAMP_LAST_KEY_PRESS
        if TIMESTAMP_LAST_KEY_PRESS and (time.time()-TIMESTAMP_LAST_KEY_PRESS > MAX_TIME):
            # max time exceeded - game over
            elim = eliminated_msg(CLOCK, f"MAX_TIME {MAX_TIME} exceeded.", players["me"]["move_no"])
            elim = json.dumps(elim).encode("utf-8")
            for player in players:
                if player != "me":
                    print(f"ELIMINATE sent to {players[player]["ip"]}_{players[player]["port"]}")
                    sock.sendto(elim, (players[player]["ip"], players[player]["port"]))
            # game over
            return

        TIMESTAMP_LAST_KEY_PRESS = time.time()
        
        # direction
        direction = user_input
        # move_no
        move_no = players["me"]["move_no"] 
        move_no += 1
        # update trail
        trail = players["me"]["trail"]
        if len(trail) == 0:
            print("No start position for trail found.")
            return
        
        # append new position
        if user_input == "up":
            trail.append((trail[-1][0], trail[-1][1]+1))
        if user_input == "down":
            trail.append((trail[-1][0], trail[-1][1]-1))
        if user_input == "left":
            trail.append((trail[-1][0]-1, trail[-1][1]))
        if user_input == "right":
            trail.append((trail[-1][0]+1, trail[-1][1]))

        # cut to MAX_LEN (if required)
        if len(trail) >= MAX_LEN:
            trail = trail[-MAX_LEN::]

        # send move_msg
        move = move_msg(CLOCK, trail, direction, move_no)
        move = json.dumps(move).encode("utf-8")

        # update my player
        players["me"]["trail"] = trail
        players["me"]["move_no"] = move_no

        # debug print
        print(move)

        for peer in PEERS:
            if peer == (players["me"]["ip"], players["me"]["port"]):
                continue
            sock.sendto(move, peer)

    # local time
    local_time = time.time()
    loop = asyncio.get_running_loop()
    fd = sys.stdin.fileno()
    loop.add_reader(fd, update_and_send_move_msg)


def get_start_position(players):
    players["me"]["trail"] = [(3,3)]


async def receiver_loop(sock):
    """
    game tick
    """
    loop = asyncio.get_running_loop()
    while(True):
        # recvfrom
        msg, addr = await loop.sock_recvfrom(sock, 1000)
        peer_msg = json.loads(msg.decode("utf-8"))

        # check Lamport clock
        global CLOCK
        rec_clock = peer_msg["clock"]
        CLOCK = max(CLOCK, rec_clock) + 1

        msg_type = peer_msg["type"]
        if msg_type == "JOIN":
            handle_join(sock, addr, peer_msg, players, CLOCK)
        elif msg_type == "ANNOUNCE":
            handle_announce(addr, peer_msg, players, CLOCK)
        elif msg_type == "MOVE":
            handle_move(addr, peer_msg, players, CLOCK)
        elif msg_type == "ELIMINATED":
            handle_eliminated(addr, peer_msg, players, CLOCK)
        else:
            print(f"Message tpye {msg_type} unknown.")

        # update viz
        viz(players)




async def main():

    # Start
    print(f"Welcome to the Snake Game...")

    global CLOCK

    # Register
    me, friend = register()
    players["me"] = me

    # Create UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    
    # Bind Socket
    print(f"Bind Addr: {(me["ip"], me["port"])}")
    sock.bind((me["ip"], me["port"]))

    # 2. JOIN
    # debug
    if me["port"] == 5002:
        friend = ("127.0.0.1", 5000) 

    if friend:
        await send_join(sock, players, friend, CLOCK)

    # 3. Startposition wählen
    get_start_position(players)

    # 4. send ANNOUNCE
    announce = announce_msg(CLOCK, players["me"]["nickname"], players["me"]["color"], players["me"]["trail"])
    announce = json.dumps(announce).encode("utf-8")

    for player in players:
        if player != "me":
            print(f"ANNOUNCE sent to {players[player]["ip"]}_{players[player]["port"]}")
            sock.sendto(announce, (players[player]["ip"], players[player]["port"]))

    # 4. Jetzt erst Tasten annehmen  
    # allow for continous inputs with pressing Enter all the time
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)   # alte Einstellungen sichern
    tty.setcbreak(fd)                      # Tasten sofort lesen, ohne Enter

    try:
        await asyncio.gather(
            receiver_loop(sock),
            on_key(sock),
        )
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)   # Terminal wiederherstellen

# start
asyncio.run(main())
