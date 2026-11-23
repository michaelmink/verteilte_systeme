import asyncio
import json
import random
import time

from . import state
from .config import PEERS, GRID_SIZE, MAX_TIME
from .viz import viz


def game_over():
    alive = [p for p in state.players.values() if not p["out"]]
    return len(state.players) >= 2 and len(alive) <= 1


async def inactivity_check():
    while True:
        await asyncio.sleep(0.2)
        if len(state.players) >= 2 and not game_over():
            now = time.time()
            for p in state.players.values():
                if not p["out"] and now - p["last_move"] > MAX_TIME:
                    p["out"] = True
                    p["out_at"] = now
        viz(state.players, GRID_SIZE)


def get_start_position():
    m = GRID_SIZE // 2
    starts = [(m, GRID_SIZE - 1), (m, 0), (0, m), (GRID_SIZE - 1, m)]   # oben, unten, links, rechts
    taken = {tuple(c) for p in state.players.values() for c in p["trail"]}
    state.players["me"]["trail"] =  [random.choice([s for s in starts if s not in taken])]


def check_collision(pos):
    """Gibt 'WALL', 'TRAIL' oder None zurück."""
    x, y = pos
    if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
        return "WALL"
    for p in state.players.values():
        if tuple(pos) in {tuple(c) for c in p["trail"]}:
            return "TRAIL"
    return None


def send_to_all(sock, msg):
    data = json.dumps(msg).encode("utf-8")
    me = state.players["me"]
    for peer in PEERS:
        if peer != (me["ip"], me["port"]):
            sock.sendto(data, peer)