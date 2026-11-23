
from .msg_templates import player_entry


from .config import PEERS

IP_RANGE = [p[1] for p in PEERS]
my_ip = "127.0.0.1"


def register():
    """
    Fragt Nickname, Farbe, Port und optional einen Friend ab (Anforderungen 13, 18).
    Gibt (eigener Spielereintrag, Friend-Adresse oder None) zurück.
    """
    while not (nickname := input("Nickname: ").strip()):
        print("Nickname darf nicht leer sein.")

    while not (color := input("Farbe: ").strip().lower()):
        print("Farbe darf nicht leer sein.")

    while True:
        port_str = input(f"Port {IP_RANGE}: ").strip()
        if port_str.isdigit() and int(port_str) in IP_RANGE:
            break
        print(f"Port muss einer von {IP_RANGE} sein.")
    
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

