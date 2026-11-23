import sys

RESET = "\x1b[0m"
ANSI_COLORS = {
    "rot": 31, "red": 31,
    "grün": 32, "gruen": 32, "green": 32,
    "gelb": 33, "yellow": 33,
    "blau": 34, "blue": 34,
    "lila": 35, "magenta": 35, "purple": 35,
    "türkis": 36, "tuerkis": 36, "cyan": 36,
    "weiß": 37, "weiss": 37, "white": 37,
}


def color_code(color):
    return ANSI_COLORS.get(str(color).lower(), 37)


def ranking(players):
    """Aktive Spieler teilen Platz 1, Ausgeschiedene nach Zeitpunkt (später = besser)."""
    alive = [k for k, p in players.items() if not p["out"]]
    out = sorted((k for k, p in players.items() if p["out"]),
                 key=lambda k: players[k].get("out_at", 0), reverse=True)
    ranks = {k: 1 for k in alive}
    for i, k in enumerate(out):
        ranks[k] = len(alive) + i + 1
    return sorted(players, key=lambda k: ranks[k]), ranks


def viz(players, grid_size=16, status=""):
    # Hintergrund: Schachbrett
    empty = ["\x1b[48;5;235m  " + RESET, "\x1b[48;5;236m  " + RESET]
    grid = [[empty[(x + y) % 2] for x in range(grid_size)] for y in range(grid_size)]

    # Spuren eintragen
    for p in players.values():
        code = color_code(p["color"])
        trail = [tuple(c) for c in p["trail"]]
        label = "xx" if p["out"] else (p["nickname"] or "??")[:2].ljust(2)
        for i, (x, y) in enumerate(trail):
            if 0 <= x < grid_size and 0 <= y < grid_size:
                if i == len(trail) - 1:
                    grid[y][x] = f"\x1b[1;30;{code + 70}m{label}{RESET}"   # Kopf
                else:
                    grid[y][x] = f"\x1b[{code + 10}m  {RESET}"             # Spur

    # Spielfeld
    width = 2 * grid_size
    lines = ["╔" + " SNAKE ".center(width, "═") + "╗"]
    for y in reversed(range(grid_size)):       # "up" = y+1 -> oben
        lines.append("║" + "".join(grid[y]) + "║")
    lines.append("╚" + "═" * width + "╝")

    # Spielstand
    lines.append("")
    lines.append(" Rang  Spieler              Züge  Status")
    order, ranks = ranking(players)
    for k in order:
        p = players[k]
        code = color_code(p["color"])
        me = " (du)" if k == "me" else ""
        state = "ausgeschieden" if p["out"] else "im Spiel"
        name = f"{p['nickname']}{me}"
        lines.append(f"  {ranks[k]}.  \x1b[{code + 10}m  {RESET} {name:<18} {p['move_no']:>4}  {state}")

    # Spielende
    alive = [p for p in players.values() if not p["out"]]
    lines.append("")
    if len(players) >= 2 and len(alive) <= 1:
        if alive:
            lines.append(f"\x1b[1;32m🏆 Sieger: {alive[0]['nickname']}{RESET}")
        else:
            lines.append(f"\x1b[1;33mUnentschieden!{RESET}")
    elif status:
        lines.append(f"\x1b[1;33m{status}{RESET}")

    sys.stdout.write("\x1b[H" + "\x1b[K\n".join(lines) + "\x1b[K\n\x1b[J")
    sys.stdout.flush()