
import os
import asyncio
import socket
import json
import sys
import tty
import termios
import time
import random

from src.register import register
from src.msg_templates import move_msg, join_msg, join_reject_msg, join_ack_msg, player_entry, announce_msg, eliminated_msg
from src.msg_handles import handle_join, handle_join_ack, handle_join_reject, handle_announce, handle_move, handle_eliminated
from src.send_join import send_join
from src.viz import viz
from src.helper_functions import send_to_all, check_collision, get_start_position, inactivity_check
from src import state
from src.config import PEERS, GRID_SIZE, MAX_TIME


    
 
async def on_key(sock):
    """
    function to receive from other peers
    """
    def update_and_send_move_msg():
        user_input = os.read(fd, 10).decode(errors="ignore")

        # check if player is still in the game
        if state.players["me"]["out"]:
            return

        # input validation
        if user_input == "\x1b[A": user_input = "up"
        elif user_input == "\x1b[B": user_input = "down"
        elif user_input == "\x1b[D": user_input = "left"
        elif user_input == "\x1b[C": user_input = "right"
        else: 
            print("Falsche Taste.")
            return
        
        # direction
        direction = user_input
        # update trail
        trail = state.players["me"]["trail"]
        if len(trail) == 0:
            print("No start position for trail found.")
            return
        
        # append new position
        if user_input == "up":
            new_pos = (trail[-1][0], trail[-1][1]+1)
        if user_input == "down":
            new_pos = (trail[-1][0], trail[-1][1]-1)
        if user_input == "left":
            new_pos = (trail[-1][0]-1, trail[-1][1])
        if user_input == "right":
            new_pos = (trail[-1][0]+1, trail[-1][1])

        # check for collision
        reason = check_collision(new_pos, state.players)

        if reason:
            state.players["me"]["out"] = True
            state.players["me"]["out_at"] = time.time()
            send_to_all(sock, eliminated_msg(tick(), reason, state.players["me"]["move_no"]))
        else:
            state.players["me"]["trail"].append(new_pos)
            state.players["me"]["move_no"] += 1
            state.players["me"]["last_move"] = time.time()
            move = move_msg(tick(), players["me"]["trail"], direction, state.players["me"]["move_no"])
            send_to_all(sock, move)

    loop = asyncio.get_running_loop()
    fd = sys.stdin.fileno()
    loop.add_reader(fd, update_and_send_move_msg)



async def receiver_loop(sock):
    """
    game tick
    """
    loop = asyncio.get_running_loop()
    while(True):
        # recvfrom
        msg, addr = await loop.sock_recvfrom(sock, 65535)
        peer_msg = json.loads(msg.decode("utf-8"))

        msg_type = peer_msg["type"]
        if msg_type == "JOIN":
            handle_join(sock, addr)
        elif msg_type == "ANNOUNCE":
            handle_announce(addr)
        elif msg_type == "MOVE":
            handle_move(addr, peer_msg)
        elif msg_type == "ELIMINATED":
            handle_eliminated(addr, peer_msg)
        else:
            print(f"Message tpye {msg_type} unknown.")

        # update viz
        viz(state.players, GRID_SIZE)



async def main():

    # Start
    print(f"Welcome to the Snake Game...")

    # Register
    me, friend = register()
    state.players["me"] = me

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
        if not await send_join(sock, players, friend, tick()):
            return

    # 3. Startposition wählen
    get_start_position()
    state.players["me"]["last_move"] = time.time()

    # 4. send ANNOUNCE
    send_to_all(sock, announce_msg(state.players["me"]["nickname"], state.players["me"]["color"], state.players["me"]["trail"]))

    # 4. Jetzt erst Tasten annehmen  
    # allow for continous inputs with pressing Enter all the time
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)   # alte Einstellungen sichern
    tty.setcbreak(fd)                      # Tasten sofort lesen, ohne Enter
    sys.stdout.write("\x1b[?1049h\x1b[?25l")        # Alternate Screen an, Cursor aus
    try:
        await asyncio.gather(
            receiver_loop(sock),
            on_key(sock),
            inactivity_check(sock),
        )
    finally:
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)   # Terminal wiederherstellen

# start
asyncio.run(main())
