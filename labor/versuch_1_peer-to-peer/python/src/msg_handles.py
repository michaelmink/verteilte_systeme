
import json
import time

from .msg_templates import join_reject_msg, join_ack_msg, player_entry
from . import state


def handle_eliminated(addr, peer_msg):
    """
    if received then set for this player out to True in players list
    """
    print(f"ELIMINATED received from {addr} with reason {peer_msg["reason"]}")
    addr_key = f"{addr[0]}_{addr[1]}"
    if addr_key in players:
        players[addr_key]["out"] = True
        players[addr_key]["out_at"] = time.time()
    else:
        print(f"ELIMINATED received from unknown: {addr}")


def handle_move(addr, peer_msg):
    key = f"{addr[0]}_{addr[1]}"
    p = players.get(key)
    if p is None or p["out"] or peer_msg["move_no"] <= p["move_no"]:
        return
    p["trail"] = peer_msg["trail"]
    p["move_no"] = peer_msg["move_no"]
    p["last_move"] = time.time()


def handle_announce(addr, peer_msg):
    """
    if new player send announce message then he is ack'ed and can be added to each players list
    """
    print(f"ANNOUNVE received from {addr}")

    for player in players.keys():
        if (players[player]["ip"] == addr[0]) and (players[player]["port"] == addr[1]):
            print(f"player {addr} already in my players list.")
            return

    # add announced player
    addr_key = f"{addr[0]}_{addr[1]}"
    players[addr_key] = player_entry(
        ip=addr[0],
        port=addr[1],
        nickname=peer_msg["nickname"],
        color=peer_msg["color"],
        trail=peer_msg["pos"],
        move_no=0,
        out=False,
        last_move=time.time()
    )

    print(f"New peer {addr} added successfully.")


def handle_join_ack(addr, peer_msg):
    """
    der Fragende empfängt ack Nachricht mit den Parameters snakes und peers
    beim Empfang des ACK wird der Spieler in die 
    """
    # update players
    print(f"JOIN ACK received from {addr}")

    players_rec = peer_msg["players"]
    addr_key = f"{addr[0]}_{addr[1]}"
    my_addr_key = f"{players["me"]["ip"]}_{players["me"]["port"]}"

    for player_addr in players_rec.keys():
        if player_addr == "me":
            players[addr_key] = players_rec["me"]
        elif player_addr == my_addr_key:
            continue
        else:
            players[player_addr] = players_rec[player_addr]
    
    # set timestamp according to my local clock
    for key, p in players.items():
        p["last_move"] = time.time()


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
    
    reject_reason = ""
    if any(p["nickname"] == peer_msg["nickname"] for p in players.values()):
        reject_reason = "NICKNAME_TAKEN"
    elif any(p["color"] == peer_msg["color"] for p in players.values()):
        reject_reason = "COLOR_TAKEN"
    elif len(players) >= 4:
        reject_reason = "GAME_FULL"

    CLOCK += 1

    if reject_reason:
        # send reject_join
        print(f"Send REJECT_JOIN to {addr}")
        join_reject = join_reject_msg(CLOCK, reject_reason)
        join_reject = json.dumps(join_reject).encode("utf-8")
        sock.sendto(join_reject, addr)

    else:
        # send join_ack
        print(f"Send JOIN_ACK to {addr}")
        join_ack = join_ack_msg(CLOCK, players)
        join_ack = json.dumps(join_ack).encode("utf-8")
        sock.sendto(join_ack, addr)




