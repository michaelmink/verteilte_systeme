
import json
import asyncio

from .msg_templates import join_msg
from .msg_handles import handle_join_ack
from . import state


async def send_join(sock, friend):
    """
    join game contains sending a join message to the friend
    receiving a join_ack with snakes and peers from friend
    or receiving a join reject with a reason

    if join ack is received, then a announce msg is sent
    join_game(sock, CLOCK, players, friend)
    """
    print(f"Send JOIN to {friend}")
    loop = asyncio.get_running_loop()

    join = join_msg(state.tick(), state.players["me"]["nickname"], state.players["me"]["color"])
    join = json.dumps(join).encode("utf-8")
    sock.sendto(join, friend)

    try:
        while True:
            raw, addr = await asyncio.wait_for(loop.sock_recvfrom(sock, 65535), timeout=2)
            answer = json.loads(raw.decode("utf-8"))
            if addr == friend and answer["type"] in ("JOIN_ACK", "JOIN_REJECT"):
                break
    except asyncio.TimeoutError:
        print("Friend antwortet nicht.")
        return False

    if answer["type"] == "JOIN_REJECT":
        print(f"Join abgelehnt: {answer['reason']}")
        return False
    
    handle_join_ack(addr, answer)

    return True
