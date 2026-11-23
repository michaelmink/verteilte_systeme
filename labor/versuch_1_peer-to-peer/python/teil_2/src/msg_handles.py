
import json
import time

from .msg_templates import join_reject_msg, join_ack_msg, player_entry
from . import state
from .config import MAX_PLAYERS
from .helper_functions import game_over

def key_of(addr):
    return f"{addr[0]}_{addr[1]}"


def touch(addr):
    """Bei jeder Nachricht: Absender ist online."""
    p = state.players.get(key_of(addr))
    if p:
        p["online"] = True
        p["last_seen"] = time.time()

def handle_heartbeat(addr, peer_msg):
    pass


def handle_eliminated(addr, peer_msg):
    """
    if received then set for this player out to True in state.players list
    """
    print(f"ELIMINATED received from {addr} with reason {peer_msg["reason"]}")
    if key_of(addr) in state.players:
        state.players[key_of(addr)]["out"] = True
        state.players[key_of(addr)]["out_at"] = time.time()
    else:
        print(f"ELIMINATED received from unknown: {addr}")


def handle_move(addr, peer_msg):
    p = state.players.get(key_of(addr))
    if p is None or p["out"] or peer_msg["move_no"] <= p["move_no"]:
        return
    p["trail"] = peer_msg["trail"]
    p["move_no"] = peer_msg["move_no"]
    p["last_move"] = time.time()


def handle_announce(addr, peer_msg):
    """
    if new player send announce message then he is ack'ed and can be added to each state.players list
    """
    print(f"ANNOUNCE received from {addr}")

    for player in state.players.keys():
        if (state.players[player]["ip"] == addr[0]) and (state.players[player]["port"] == addr[1]):
            print(f"player {addr} already in my state.players list.")
            return
    
    now = time.time()
    # reset last_move to avoid inactive check to be positive when new player enters
    for k, v in state.players.items():
        v["last_move"] = now
    # add announced player
    state.players[key_of(addr)] = player_entry(
        ip=addr[0],
        port=addr[1],
        nickname=peer_msg["nickname"],
        color=peer_msg["color"],
        trail=peer_msg["trail"],
        move_no=0,
        out=False,
        last_move=now,
        online=True,
        last_seen=now
    )

    print(f"New peer {addr} added successfully.")


def handle_join_ack(addr, peer_msg):
    """
    der Fragende empfängt ack Nachricht mit den Parameters snakes und peers
    beim Empfang des ACK wird der Spieler in die 
    """
    now = time.time()
    me = state.players["me"]
    for key, value in peer_msg["players"].items():
        key_rec = key_of((value["ip"], value["port"]))
        if key_rec not in state.players:
            value["last_move"] = now
            value["last_seen"] = now
            state.players[key_rec] = value
            

def handle_join_reject(addr, peer_msg):
    """
    """
    print(f"JOIN_REJECT received from {addr} with reason: {peer_msg["reason"]}.")
    print("Try again.")


def handle_join(sock, addr, peer_msg):
    """
    receives join message with nickname, color
    checks if nickname and color are allowed
    and number of player is not exceeding the limit
    if true, then send join_ack back
    if false, send join_reject back
    """

    print(f"JOIN received from {addr}")

    online = [p for p in state.players.values() if p["online"]]
    
    reject_reason = ""
    if key_of(addr) in state.players:
        reject_reason = "ADDRESS_USED"
    elif any(p["nickname"] == peer_msg["nickname"] for p in state.players.values()):
        reject_reason = "NICKNAME_TAKEN"
    elif any(p["color"] == peer_msg["color"] for p in state.players.values()):
        reject_reason = "COLOR_TAKEN"
    elif game_over():
        reject_reason = "GAME_OVER"
    elif len(online) >= MAX_PLAYERS:
        reject_reason = "GAME_FULL"

    if reject_reason:
        # send reject_join
        print(f"Send REJECT_JOIN to {addr}")
        join_reject = join_reject_msg(state.tick(), reject_reason)
        join_reject = json.dumps(join_reject).encode("utf-8")
        sock.sendto(join_reject, addr)

    else:
        # send join_ack
        print(f"Send JOIN_ACK to {addr}")
        join_ack = join_ack_msg(state.tick(), state.players)
        join_ack = json.dumps(join_ack).encode("utf-8")
        sock.sendto(join_ack, addr)


def handle_leave(addr, peer_msg):
    p = state.players.get(key_of(addr))
    if p is None:
        return
    p["online"] = False
    if not p["out"]:
        p["out"] = True
        p["out_at"] = time.time()
