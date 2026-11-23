players = {}
clock = 0


def tick():
    """Vor jedem Senden."""
    global clock
    clock += 1
    return clock


def on_receive(received_clock):
    """Bei jedem Empfang."""
    global clock
    clock = max(clock, received_clock) + 1