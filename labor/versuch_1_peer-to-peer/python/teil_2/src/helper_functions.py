import asyncio
import json
import random
import time

from . import state
from .config import GRID_SIZE, MAX_TIME, HEARTBEAT_INTERVAL, ONLINE_TIMEOUT
from .msg_templates import heartbeat_msg
from .viz import viz


def game_over():
    alive = [p for p in state.players.values() if not p["out"]]
    return len(state.players) >= 2 and len(alive) <= 1


async def inactivity_check():
    while True:
        await asyncio.sleep(0.2)
        now = time.time()
        for key, p in state.players.items():
            if key == "me":
                continue
            # Online-Status (4d)
            if p["online"] and now - p["last_seen"] > ONLINE_TIMEOUT:
                p["online"] = False
        # Inaktivität (6), erst ab 2 Spielern und bis zum Spielende
        if len(state.players) >= 2 and not game_over():
            for p in state.players.values():
                if not p["out"] and now - p["last_move"] > MAX_TIME:
                    p["out"] = True
                    p["out_at"] = now
        viz(state.players, GRID_SIZE)


def get_start_position():
    m = GRID_SIZE // 2
    mids = [(m, GRID_SIZE - 1), (m, 0), (0, m), (GRID_SIZE - 1, m)]
    edge = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)
            if x in (0, GRID_SIZE - 1) or y in (0, GRID_SIZE - 1)]
    taken = {tuple(c) for p in state.players.values() for c in p["trail"]}
    free_mids = [s for s in mids if s not in taken]
    free_edge = [s for s in edge if s not in taken]
    candidates = free_mids or free_edge          # Randmitten mit Vorrang (16)
    state.players["me"]["trail"] = [random.choice(candidates)]


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
    """Nur an Online-Mitglieder (4b)."""
    data = json.dumps(msg).encode("utf-8")
    for key, p in state.players.items():
        if key != "me" and p["online"]:
            sock.sendto(data, (p["ip"], p["port"]))


async def heartbeat_loop(sock):
    while True:
        send_to_all(sock, heartbeat_msg(state.tick()))
        await asyncio.sleep(HEARTBEAT_INTERVAL)
