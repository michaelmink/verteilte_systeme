
import os
import asyncio
import socket
import json
import sys
import tty
import termios
import time


from src.register import register
from src.msg_templates import move_msg, announce_msg, eliminated_msg, leave_msg
from src.msg_handles import handle_join, handle_join_ack, handle_announce, handle_move, handle_eliminated, handle_heartbeat, handle_leave, touch
from src.send_join import send_join
from src.viz import viz
from src.helper_functions import send_to_all, check_collision, get_start_position, inactivity_check, game_over, heartbeat_loop
from src import state
from src.config import GRID_SIZE, DEBUG

    
 
async def on_key(sock):
    """
    function to receive from other peers
    """
    def update_and_send_move_msg():
        user_input = os.read(fd, 10).decode(errors="ignore")

        if user_input == "q":
            send_to_all(sock, leave_msg(state.tick()))
            raise SystemExit

        # check if player is still in the game
        if state.players["me"]["out"] or game_over():
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
        reason = check_collision(new_pos)

        if reason:
            state.players["me"]["out"] = True
            state.players["me"]["out_at"] = time.time()
            send_to_all(sock, eliminated_msg(state.tick(), reason, state.players["me"]["move_no"]))
        else:
            state.players["me"]["trail"].append(new_pos)
            state.players["me"]["move_no"] += 1
            state.players["me"]["last_move"] = time.time()
            move = move_msg(state.tick(), state.players["me"]["trail"], direction, state.players["me"]["move_no"])
            send_to_all(sock, move)

    loop = asyncio.get_running_loop()
    fd = sys.stdin.fileno()
    loop.add_reader(fd, update_and_send_move_msg)



async def receiver_loop(sock):
    """
    receiver loop
    """
    loop = asyncio.get_running_loop()
    while(True):
        # recvfrom
        msg, addr = await loop.sock_recvfrom(sock, 65535)
        peer_msg = json.loads(msg.decode("utf-8"))
        state.on_receive(peer_msg["clock"])
        touch(addr)

        msg_type = peer_msg["type"]
        if msg_type == "JOIN":
            handle_join(sock, addr, peer_msg)
        elif msg_type == "ANNOUNCE":
            handle_announce(addr, peer_msg)
        elif msg_type == "MOVE":
            handle_move(addr, peer_msg)
        elif msg_type == "ELIMINATED":
            handle_eliminated(addr, peer_msg)
        elif msg_type == "HEARTBEAT":
            handle_heartbeat(addr, peer_msg)
        elif msg_type == "LEAVE":
            handle_leave(addr, peer_msg)
        else:
            print(f"Message type {msg_type} unknown.")

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
    sock.bind(("0.0.0.0", me["port"]))

    # 2. JOIN
    # debug
    if DEBUG:
        if me["port"] == 5002:
            friend = ("127.0.0.1", 5000)

    if friend:
        if not await send_join(sock, friend):
            return

    # 3. Startposition wählen
    get_start_position()
    state.players["me"]["last_move"] = time.time()

    # 4. send ANNOUNCE
    send_to_all(sock, announce_msg(
        state.tick(), state.players["me"]["nickname"], state.players["me"]["color"], state.players["me"]["trail"])
        )

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
            inactivity_check(),
            heartbeat_loop(sock)
        )
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        send_to_all(sock, leave_msg(state.tick()))
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)   # Terminal wiederherstellen

# start
asyncio.run(main())
