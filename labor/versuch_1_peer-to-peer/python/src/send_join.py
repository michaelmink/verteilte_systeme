
import json
import asyncio

from .msg_templates import join_msg
from .msg_handles import handle_join_ack


async def send_join(sock, players, friend, CLOCK):
    """
    join game contains sending a join message to the friend
    receiving a join_ack with snakes and peers from friend
    or receiving a join reject with a reason

    if join ack is received, then a announce msg is sent
    join_game(sock, CLOCK, players, friend)
    """
    print(f"Send JOIN to {friend}")
    loop = asyncio.get_running_loop()

    CLOCK += 1
    join = join_msg(CLOCK, players["me"]["nickname"], players["me"]["color"])
    join = json.dumps(join).encode("utf-8")
    sock.sendto(join, friend)

    try:
        raw, addr = await asyncio.wait_for(loop.sock_recvfrom(sock, 65535), timeout=2)
    except asyncio.TimeoutError:
        print("Friend antwortet nicht.")
        return

    answer = json.loads(raw.decode("utf-8"))
    if answer["type"] == "JOIN_REJECT":
        print(f"Join abgelehnt: {answer['reason']}")
        return
    
    handle_join_ack(addr, answer, players, CLOCK)
