"""Szenarien zu Konsistenzgarantien bei Single-Leader-Replikation.

Aufruf (im Compose-Netz):
    docker compose run --rm client ryw --mode naive
    docker compose run --rm client ryw --mode guaranteed
    docker compose run --rm client monotonic --mode naive
    docker compose run --rm client monotonic --mode sticky
    docker compose run --rm client monotonic --mode min-lsn
    docker compose run --rm client status
    docker compose run --rm client lag follower2 5
"""

from __future__ import annotations

import argparse
import json
import os
import random
import threading
import time
import urllib.error
import urllib.request
import uuid
import zlib
from urllib.parse import urlencode

NODES = {
    "leader": os.environ.get("LEADER_URL", "http://leader:8000"),
    "follower1": os.environ.get("FOLLOWER1_URL", "http://follower1:8000"),
    "follower2": os.environ.get("FOLLOWER2_URL", "http://follower2:8000"),
}
FOLLOWERS = ["follower1", "follower2"]


def call(method: str, url: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)


def write(key: str, value: object) -> int:
    _, body = call("POST", f"{NODES['leader']}/write", {"key": key, "value": value})
    return body["lsn"]


def read(node: str, key: str, min_lsn: int = 0, timeout: float = 0.0) -> dict | None:
    params = urlencode({"key": key, "min_lsn": min_lsn, "timeout": timeout})
    status, body = call("GET", f"{NODES[node]}/read?{params}")
    return body if status == 200 else None


def set_lag(node: str, lag: float) -> None:
    call("POST", f"{NODES[node]}/admin/lag", {"lag": lag})


def print_status() -> None:
    for name, url in NODES.items():
        _, body = call("GET", f"{url}/status")
        print(f"  {name:10} role={body['role']:8} applied_lsn={body['applied_lsn']:<5} "
              f"lag={body['lag']}s")


# --------------------------------------------------------------------------- #
# Read-your-writes
# --------------------------------------------------------------------------- #
def scenario_ryw(mode: str, rounds: int) -> None:
    """Nutzer ändert seinen Anzeigenamen und lädt direkt danach die Seite neu.

    naive:      Lesen von einem beliebigen Follower -> eigene Änderung fehlt oft.
    guaranteed: Client merkt sich die LSN seines Writes und liest nur von einem
                Knoten, der mindestens diese LSN hat (sonst Fallback auf Leader).
    """
    set_lag("follower1", 1.0)
    set_lag("follower2", 2.0)
    key = f"profil:{uuid.uuid4().hex[:6]}"
    print(f"Read-your-writes, mode={mode}, key={key}")
    print_status()
    print()

    violations = 0
    for i in range(1, rounds + 1):
        value = f"Anzeigename v{i}"
        lsn = write(key, value)
        node = random.choice(FOLLOWERS)

        if mode == "naive":
            result = read(node, key)
        else:
            result = read(node, key, min_lsn=lsn, timeout=0.3)
            if result is None:
                print(f"    {node} hat lsn={lsn} noch nicht -> Fallback auf leader")
                result = read("leader", key)

        ok = result["version"] >= lsn
        violations += not ok
        verdict = "OK      " if ok else "VERLETZT"
        print(f"[{verdict}] geschrieben {value!r} (lsn={lsn}) | gelesen von "
              f"{result['node']:9}: {result['value']!r} (version={result['version']})")
        time.sleep(0.5)

    print(f"\n{violations}/{rounds} Reads haben den eigenen Write nicht gesehen.")


# --------------------------------------------------------------------------- #
# Monotonic reads
# --------------------------------------------------------------------------- #
def scenario_monotonic(mode: str, duration: float) -> None:
    """Ein Zähler wird laufend erhöht, ein Leser fragt ihn wiederholt ab.

    naive:   jeder Read geht an einen zufälligen Follower -> Werte springen zurück.
    sticky:  Nutzer wird per Hash fest einem Follower zugeordnet.
    min-lsn: Client merkt sich die höchste gesehene Version und verlangt sie
             als min_lsn (sonst Fallback auf Leader).
    """
    set_lag("follower1", 0.2)
    set_lag("follower2", 3.0)
    key = f"zaehler:{uuid.uuid4().hex[:6]}"
    user = "alice"
    sticky_node = FOLLOWERS[zlib.crc32(user.encode()) % len(FOLLOWERS)]
    print(f"Monotonic reads, mode={mode}, key={key}"
          + (f", {user} -> {sticky_node}" if mode == "sticky" else ""))
    print_status()
    print()

    stop = threading.Event()

    def writer() -> None:
        i = 1
        while not stop.is_set():
            write(key, i)
            i += 1
            time.sleep(0.3)

    writer_thread = threading.Thread(target=writer)
    writer_thread.start()
    time.sleep(1.0)

    max_seen = 0
    reads = violations = 0
    end = time.time() + duration
    while time.time() < end:
        node = sticky_node if mode == "sticky" else random.choice(FOLLOWERS)
        if mode == "min-lsn":
            result = read(node, key, min_lsn=max_seen, timeout=0.3)
            if result is None:
                print(f"    {node} ist hinter version={max_seen} -> Fallback auf leader")
                result = read("leader", key)
        else:
            result = read(node, key)

        reads += 1
        version = result["version"]
        if version < max_seen:
            violations += 1
            print(f"[VERLETZT] {result['node']:9} liefert {result['value']!r} (version={version}) "
                  f"- vorher schon version={max_seen} gesehen, Zeitreise zurueck!")
        else:
            print(f"[OK      ] {result['node']:9} liefert {result['value']!r} (version={version})")
        max_seen = max(max_seen, version)
        time.sleep(0.4)

    stop.set()
    writer_thread.join()
    print(f"\n{violations}/{reads} Reads waren aelter als ein vorher gesehener Stand.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ryw", help="Read-your-writes")
    p.add_argument("--mode", choices=["naive", "guaranteed"], default="naive")
    p.add_argument("--rounds", type=int, default=8)

    p = sub.add_parser("monotonic", help="Monotonic reads")
    p.add_argument("--mode", choices=["naive", "sticky", "min-lsn"], default="naive")
    p.add_argument("--duration", type=float, default=10.0)

    sub.add_parser("status", help="Stand aller Knoten anzeigen")

    p = sub.add_parser("lag", help="Replikationsverzoegerung eines Followers setzen")
    p.add_argument("node", choices=FOLLOWERS)
    p.add_argument("seconds", type=float)

    args = parser.parse_args()
    if args.cmd == "ryw":
        scenario_ryw(args.mode, args.rounds)
    elif args.cmd == "monotonic":
        scenario_monotonic(args.mode, args.duration)
    elif args.cmd == "status":
        print_status()
    elif args.cmd == "lag":
        set_lag(args.node, args.seconds)
        print_status()


if __name__ == "__main__":
    main()
