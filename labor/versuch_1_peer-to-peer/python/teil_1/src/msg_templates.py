
"""
message definitions
"""

# neuer Peer -> Friend Peer
def join_msg(clock, nickname, color):
    return {
        "type": "JOIN",
        "clock": clock,
        "nickname": nickname,
        "color": color
    }

# Friend Peer -> neuer Peer
def join_ack_msg(clock, players):
    return {
        "type": "JOIN_ACK",
        "clock": clock,
        "players": players
    }

# Eintrag in JOIN_ACK.players
def player_entry(ip, port, nickname, color, trail, move_no, out, last_move):
    return {
        "ip": ip,
        "port": port,
        "nickname": nickname,
        "color": color,
        "trail": trail,      # [[x0, y0], [x1, y1], ...], trail[0] = Startposition
        "move_no": move_no,
        "out": out,
        "last_move": last_move,
    }

# Friend Peer -> neuer Peer
def join_reject_msg(clock, reason):
    return {
        "type": "JOIN_REJECT",
        "clock": clock,
        "reason": reason
    }

# neuer Peer -> alle
def announce_msg(clock, nickname, color, trail):
    return {
        "type": "ANNOUNCE",
        "clock": clock,
        "nickname": nickname,
        "color": color,
        "trail": trail
    }

# Peer -> alle
def move_msg(clock, trail, direction, move_no):
    return {
        "type": "MOVE",
        "clock": clock,
        "trail": trail,
        "direction": direction,
        "move_no": move_no
    }

# Peer -> alle
def eliminated_msg(clock, reason, move_no):
    return {
        "type": "ELIMINATED",
        "clock": clock,
        "reason": reason,
        "move_no": move_no
    }
