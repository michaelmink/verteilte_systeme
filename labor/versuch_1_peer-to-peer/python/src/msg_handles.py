
import json
from .msg_templates import join_reject_msg, join_ack_msg


def handle_join_ack(addr, peer_msg, players):
    """
    der Fragende empfängt ack Nachricht mit den Parameters snakes und peers
    beim Empfang des ACK wird der Spieler in die 
    """
    # update players
    print(f"JOIN ACK received from {addr}")

    players_rec = peer_msg["players"]

    for player_addr in players_rec.keys():
        if player_addr == "me":
            players[addr] = players_rec["me"]
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




