
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

# message definition
msg = {
    "msg_id": 1,
    "name": None,
    "m": 16,
    "occupied": [(3,3),(3,2)],
    "max_len": 3,
    "direction": "up",
    "t": 0,
    "collision": False,
    "color": "red",
}

def register(name: str) -> dict:
    msg_reg = msg.copy()
    msg_reg["name"] = name
    return msg_reg

# function to send next action
async def send_action(msg, sock):
    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(0.2)

        data = json.dumps(msg).encode("utf-8") # sendto erwartet bytes
        address = (ip_dest, port_dest)
        await loop.sock_sendto(sock, data, address)
 
# function to receive from other peers
async def on_key(msg):
    
    def update_msg():
        user_input = os.read(fd, 100)
        # input validation
        # TODO
        msg["direction"] = user_input.decode(errors="ignore")

    loop = asyncio.get_running_loop()
    fd = sys.stdin.fileno()
    loop.add_reader(fd, update_msg)

async def game_tick(sock, global_state):
    loop = asyncio.get_running_loop()
    while(True):    
        # recvfrom
        print("waiting for receive")
        msg, addr = await loop.sock_recvfrom(sock, 1000)
        peer_msg = json.loads(msg.decode("utf-8"))

        # merge single states into a global joint state
        # TODO
        name = peer_msg["name"]
        global_state[name] = peer_msg

        print(peer_msg)   


async def main():

    # Register
    print("Enter name to register and start: ")
    name = "michi"

    # Start
    print(f"Welcome {name} to the Snake Game...")
    init_msg = register(name)

    print(init_msg)

    # create udp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    
    # bind
    address = (ip_dest, port_recv)
    sock.bind(address)

    # allow for continous inputs with pressing Enter all the time
    fd = sys.stdin.fileno()
    settings = tty.setcbreak(fd)

    # init global state
    global_state = {}

    # asyncronous loop to receive messages and send messages
    try:
        await asyncio.gather(
            on_key(init_msg), 
            send_action(init_msg, sock),
            game_tick(sock, global_state),
        )
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)


# start
asyncio.run(main())
