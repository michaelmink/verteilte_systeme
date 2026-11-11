
import os
import asyncio
import socket
import json
import sys
import tty
import termios


# Parameter
ip_dest = "127.0.0.1" # lo ip adresses of recipient
port_dest = 5000
port_recv = 5000

# start positions
start_pos = [(4,3),(4,4),(5,3),(5,4)]

# connected peers
con_peers = []

# message types
#enum MSG_TYPES:
#    MOVE
#    REGISTER

MAX_LEN = 3

# message definition (incl. default values)
msg_move = {
    "msg_type": "MOVE",
    "msg_id": 1,
    "nickname": None,
    "m": 16,
    "occupied": [],
    "max_len": 3,
    "direction": "up",
    "clock": 0,
    "collision": False,
    "color": "red",
}

msg_register_req = {
    "msg_type": "REGISTER",
    "nickname": None,
    "farbe": None,
    "ip": None,
    "port": None,
}

msg_register_ack = {
    "msg_type": "REGISTER_ACK",
    "my_nickname": None,
    "your_nickname": None,
    "ack": False
}


def register(my_state) -> bool:
    """
    register
    """
    fd = sys.stdin.fileno()
    for i in ["nickname", "farbe", "port"]:
        print(f"enter {i}: ")
        input = os.read(fd, 100).decode(errors="ignore")
        msg_move[i] = input

    return msg_move

async def update_and_send_state(my_state, sock):
    """
    function to send next action
    """
    loop = asyncio.get_running_loop()
    address = (ip_dest, port_dest)
    while True:
        await asyncio.sleep(1)
        # increment clock
        my_state["clock"] += 1
        # update positions
        if len(my_state["occupied"]) == 0:
            my_state["occupied"].append((3,3))
            continue

        # update pos
        if my_state["direction"] == "right":
            my_state["occupied"].append((my_state["occupied"][-1][0]+1, my_state["occupied"][-1][1]))
        elif my_state["direction"] == "left":
            my_state["occupied"].append((my_state["occupied"][-1][0]-1, my_state["occupied"][-1][1]))
        elif my_state["direction"] == "up":
            my_state["occupied"].append((my_state["occupied"][-1][0], my_state["occupied"][-1][1]+1))
        elif my_state["direction"] == "down":
            my_state["occupied"].append((my_state["occupied"][-1][0], my_state["occupied"][-1][1]-1))

        # check len
        if len(my_state["occupied"]) > MAX_LEN:
            my_state["occupied"] = my_state["occupied"][-MAX_LEN::]


        data = json.dumps(my_state).encode("utf-8") # sendto erwartet bytes
        await loop.sock_sendto(sock, data, address)
 
async def on_key(msg):
    """
    function to receive from other peers
    """
    def update_msg():
        user_input = os.read(fd, 10).decode(errors="ignore")
        # input validation
        if user_input == "\x1b[A": user_input = "up"
        elif user_input == "\x1b[B": user_input = "down"
        elif user_input == "\x1b[D": user_input = "left"
        elif user_input == "\x1b[C": user_input = "right"
        else: user_input = msg["direction"]

        msg["direction"] = user_input

    loop = asyncio.get_running_loop()
    fd = sys.stdin.fileno()
    loop.add_reader(fd, update_msg)

async def game_tick(sock, my_state):
    """
    game tick
    """
    loop = asyncio.get_running_loop()
    while(True):
        # recvfrom
        msg, addr = await loop.sock_recvfrom(sock, 1000)
        peer_msg = json.loads(msg.decode("utf-8"))

        # read msg type and decide what to do
        msg_type = peer_msg["msg_type"]
        if msg_type == "REGISTER":
            pass
        elif msg_type == "MOVE":
            pass

        # merge single states into a global joint state
        name = peer_msg["nickname"]
        col = peer_msg["color"]
        occ = peer_msg["occupied"]

        # visualize snake (i.e. occupied, color, direction)

        print(peer_msg)   




async def main():

    # init state
    my_state = msg_move.copy()

    # Start
    print(f"Welcome to the Snake Game...")
    my_state = register(my_state)

    # create udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    
    # bind
    address = (ip_dest, port_recv)
    sock.bind(address)

    # allow for continous inputs with pressing Enter all the time
    fd = sys.stdin.fileno()
    settings = tty.setcbreak(fd)

    # asyncronous loop to receive messages and send messages
    try:
        await asyncio.gather(
            on_key(my_state), 
            update_and_send_state(my_state, sock),
            game_tick(sock, my_state),
        )
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)


# start
asyncio.run(main())
