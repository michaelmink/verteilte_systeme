
from .msg_templates import player_entry

import socket

def detect_ip():
    """Ermittelt die LAN-IP (es wird nichts gesendet)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def register():
    """
    Fragt Nickname, Farbe, Port und optional einen Friend ab (Anforderungen 13, 18).
    Gibt (eigener Spielereintrag, Friend-Adresse oder None) zurück.
    """
    while not (nickname := input("Nickname: ").strip()):
        print("Nickname darf nicht leer sein.")

    while not (color := input("Farbe: ").strip().lower()):
        print("Farbe darf nicht leer sein.")

    default_ip = detect_ip()
    my_ip = input(f"Eigene IP [{default_ip}]: ").strip() or default_ip
    while not (port_str := input("Port: ").strip()).isdigit():
        print("Port muss eine Zahl sein.")

    MY_ADDR = (my_ip, int(port_str))

    while True:
        friend_str = input("Join (IP:Port eines Friends, leer = neues Spiel): ").strip()
        if not friend_str:
            friend = None                     # erster Spieler -> neues Spiel
            break
        try:
            ip, port = friend_str.rsplit(":", 1)
            friend = (ip, int(port))          # Tupel (str, int), passt zu recvfrom-Adressen
        except ValueError:
            print("Format: IP:Port, z. B. 127.0.0.1:5000")
            continue
        if friend == MY_ADDR:
            print("Du kannst nicht dein eigener Friend sein.")
            continue
        break

    me = player_entry(
        ip=MY_ADDR[0],
        port=MY_ADDR[1],
        nickname=nickname,
        color=color,
        trail=[],        # Startposition wird nach dem Join gewählt
        move_no=0,
        out=False,
        last_move=None
    )
    return me, friend

