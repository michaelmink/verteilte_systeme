
import json
from .msg_templates import join_reject_msg, join_ack_msg, player_entry


def handle_eliminated(addr, peer_msg, players, CLOCK):
    """
    if received then set for this player out to True in players list
    """
    print(f"ELIMINATED received from {addr} with reason {peer_msg["reason"]}")
    addr_key = f"{addr[0]}_{addr[1]}"
    players[addr_key]["out"] = True


def handle_move(addr, peer_msg, players, CLOCK):
    """
    update player entry in players with updated move
    """
    print(f"MOVE received from {addr}")

    my_addr_key = f"{players["me"]["ip"]}_{players["me"]["port"]}"
    addr_key = f"{addr[0]}_{addr[1]}"
    for player in players:
        if addr_key in players:
            players[addr_key]["trail"] = peer_msg["trail"]
            players[addr_key]["direction"] = peer_msg["direction"]
            players[addr_key]["move_no"] = peer_msg["move_no"]
        elif addr_key == my_addr_key:
            players["me"]["trail"] = peer_msg["trail"]
            players["me"]["direction"] = peer_msg["direction"]
            players["me"]["move_no"] = peer_msg["move_no"]
        else:
            print(f"Warning: {addr_key} not registered.")


def handle_announce(addr, peer_msg, players, CLOCK):
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
        out=False
    )

    print(f"New peer {addr} added successfully.")


def handle_join_ack(addr, peer_msg, players, CLOCK):
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


def handle_join_reject(addr, peer_msg):
    """
    """
    print(f"JOIN_REJECT received from {addr} with reason: {peer_msg["reason"]}.")
    print("Try again.")


def handle_join(sock, addr, peer_msg, players, CLOCK):
    """
    receives join message with nickname, color
    checks if nickname and color are allowed
    and number of player is not exceeding the limit
    if true, then send join_ack back
    if false, send join_reject back
    """

    print(f"JOIN received from {addr}")
    
    reject_reason = ""
    if players["me"]["nickname"] == peer_msg["nickname"]:
        reject_reason = "nickname already exists."
    if players["me"]["color"] == peer_msg["color"]:
        reject_reason = "color already exists."
    if len(players) == 4:
        reject_reason = "Max players reached."

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




