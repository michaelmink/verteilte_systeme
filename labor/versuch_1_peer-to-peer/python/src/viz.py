
ANSI_COLORS = {
    "rot": 31, "red": 31,
    "grün": 32, "gruen": 32, "green": 32,
    "gelb": 33, "yellow": 33,
    "blau": 34, "blue": 34,
    "lila": 35, "magenta": 35, "purple": 35,
    "türkis": 36, "tuerkis": 36, "cyan": 36,
    "weiß": 37, "weiss": 37, "white": 37,
}



RESET = "\x1b[0m"


def color_code(farbe):
    """ANSI-Vordergrundcode (30-37) für eine Farbe, Fallback weiß."""
    return ANSI_COLORS.get(str(farbe).lower(), 37)

async def viz():
    """
    viz for snakes (statisches Bild im Alternate Screen)
    """
    # Hintergrund: dezentes Schachbrett (256-Farben-Grautöne)
    empty = ["\x1b[48;5;235m  " + RESET, "\x1b[48;5;236m  " + RESET]
    grid = [[empty[(x + y) % 2] for x in range(GRID_SIZE)] for y in range(GRID_SIZE)]

    # Schlangen eintragen
    for s in snakes.values():
        code = color_code(s["farbe"])
        occ = [tuple(p) for p in s["occupied"]]
        label = (s["nickname"] or "??")[:2].ljust(2)
        for i, (x, y) in enumerate(occ):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                if i == len(occ) - 1:
                    # Kopf: heller Hintergrund (100-107), schwarze fette Schrift
                    grid[y][x] = f"\x1b[1;30;{code + 70}m{label}{RESET}"
                else:
                    # Körper: normaler Hintergrund (40-47)
                    grid[y][x] = f"\x1b[{code + 10}m  {RESET}"

    # Spielfeld mit Rahmen
    width = 2 * GRID_SIZE
    lines = ["╔" + " SNAKE ".center(width, "═") + "╗"]
    for y in reversed(range(GRID_SIZE)):         # "up" erhöht y -> y=0 unten zeichnen
        lines.append("║" + "".join(grid[y]) + "║")
    lines.append("╚" + "═" * width + "╝")

    # Legende
    lines.append("")
    for addr, s in snakes.items():
        code = color_code(s["farbe"])
        me = " (du)" if addr == MY_ADDR else ""
        head = tuple(s["occupied"][-1]) if s["occupied"] else "-"
        lines.append(f" \x1b[{code + 10}m  {RESET} \x1b[1m{s['nickname']}{RESET}{me}"
                     f"  len={len(s['occupied'])}  kopf={head}")

    # Statuszeile
    lines.append("")
    if status:
        lines.append(f"\x1b[1;33m{status}{RESET}")

    # Cursor nach oben links, jede Zeile überschreiben (\x1b[K löscht Reste), Rest darunter löschen
    sys.stdout.write("\x1b[H" + "\x1b[K\n".join(lines) + "\x1b[K\n\x1b[J")
    sys.stdout.flush()
    