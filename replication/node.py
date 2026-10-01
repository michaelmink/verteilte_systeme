"""Knoten für eine Single-Leader-Replikation (Leader oder Follower).

- Der Leader nimmt alle Schreibzugriffe an und hängt sie an ein Replikationslog
  an. Jeder Eintrag bekommt eine fortlaufende LSN (Log Sequence Number).
- Follower holen sich das Log asynchron vom Leader (Pull, wie Postgres
  Streaming Replication) und wenden jeden Eintrag erst ``lag`` Sekunden nach
  dem Schreiben an. So lässt sich Replikationsverzögerung gezielt simulieren.
- Lesen geht auf jedem Knoten. Mit ``min_lsn`` kann ein Client verlangen, dass
  der Knoten mindestens diesen Stand hat (sonst wartet er bis ``timeout`` und
  antwortet dann mit 503). Darauf bauen Read-your-writes und Monotonic Reads auf.

Nur Standardbibliothek, damit das Image klein und ohne Abhängigkeiten bleibt.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROLE = os.environ.get("ROLE", "leader")
NODE_NAME = os.environ.get("NODE_NAME", ROLE)
LEADER_URL = os.environ.get("LEADER_URL", "http://leader:8000")
PORT = int(os.environ.get("PORT", "8000"))
POLL_INTERVAL = 0.05


class Store:
    def __init__(self, lag: float) -> None:
        self.cond = threading.Condition()
        self.data: dict[str, dict] = {}
        self.log: list[dict] = []
        self.applied_lsn = 0
        self.lag = lag

    def append(self, key: str, value: object) -> dict:
        with self.cond:
            entry = {"lsn": len(self.log) + 1, "key": key, "value": value, "ts": time.time()}
            self.log.append(entry)
            self.apply(entry)
            return entry

    def apply(self, entry: dict) -> None:
        with self.cond:
            self.data[entry["key"]] = {"value": entry["value"], "lsn": entry["lsn"]}
            self.applied_lsn = entry["lsn"]
            self.cond.notify_all()

    def entries_since(self, lsn: int) -> list[dict]:
        with self.cond:
            return self.log[lsn:]

    def read(self, key: str, min_lsn: int, timeout: float) -> dict | None:
        with self.cond:
            if not self.cond.wait_for(lambda: self.applied_lsn >= min_lsn, timeout=timeout):
                return None
            item = self.data.get(key)
            return {
                "node": NODE_NAME,
                "key": key,
                "value": item["value"] if item else None,
                "version": item["lsn"] if item else 0,
                "applied_lsn": self.applied_lsn,
            }


STORE = Store(lag=float(os.environ.get("REPLICATION_LAG", "0")))


def replicate_forever() -> None:
    """Follower: Log vom Leader holen und verzögert anwenden."""
    pending: list[dict] = []
    fetched = 0
    while True:
        try:
            with urllib.request.urlopen(f"{LEADER_URL}/log?since={fetched}", timeout=2) as resp:
                new_entries = json.load(resp)["entries"]
            pending.extend(new_entries)
            if new_entries:
                fetched = new_entries[-1]["lsn"]
        except (urllib.error.URLError, OSError):
            pass  # Leader (noch) nicht erreichbar

        now = time.time()
        # Die Container teilen sich die Uhr des Hosts, daher ist der Leader-Zeitstempel hier brauchbar.
        while pending and pending[0]["ts"] + STORE.lag <= now:
            entry = pending.pop(0)
            STORE.apply(entry)
            print(f"[{NODE_NAME}] apply lsn={entry['lsn']} {entry['key']}={entry['value']!r} "
                  f"(lag={STORE.lag}s)", flush=True)
        time.sleep(POLL_INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def _send(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        query = parse_qs(url.query)
        try:
            if url.path == "/read":
                key = query["key"][0]
                min_lsn = int(query.get("min_lsn", ["0"])[0])
                timeout = min(float(query.get("timeout", ["0"])[0]), 10.0)
                result = STORE.read(key, min_lsn, timeout)
                if result is None:
                    self._send(503, {"error": "replica behind", "node": NODE_NAME,
                                     "applied_lsn": STORE.applied_lsn, "min_lsn": min_lsn})
                else:
                    self._send(200, result)
            elif url.path == "/log" and ROLE == "leader":
                since = int(query.get("since", ["0"])[0])
                self._send(200, {"entries": STORE.entries_since(since)})
            elif url.path == "/status":
                self._send(200, {"node": NODE_NAME, "role": ROLE,
                                 "applied_lsn": STORE.applied_lsn, "lag": STORE.lag})
            else:
                self._send(404, {"error": "not found"})
        except (KeyError, ValueError) as exc:
            self._send(400, {"error": f"bad request: {exc}"})

    def do_POST(self) -> None:
        url = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if url.path == "/write":
                if ROLE != "leader":
                    self._send(403, {"error": "read-only replica, write to the leader"})
                    return
                entry = STORE.append(str(body["key"]), body["value"])
                print(f"[{NODE_NAME}] write lsn={entry['lsn']} {entry['key']}={entry['value']!r}",
                      flush=True)
                self._send(200, {"node": NODE_NAME, "lsn": entry["lsn"]})
            elif url.path == "/admin/lag" and ROLE == "follower":
                STORE.lag = max(0.0, float(body["lag"]))
                print(f"[{NODE_NAME}] lag -> {STORE.lag}s", flush=True)
                self._send(200, {"node": NODE_NAME, "lag": STORE.lag})
            else:
                self._send(404, {"error": "not found"})
        except (KeyError, ValueError) as exc:
            self._send(400, {"error": f"bad request: {exc}"})


def main() -> None:
    if ROLE == "follower":
        threading.Thread(target=replicate_forever, daemon=True).start()
    print(f"[{NODE_NAME}] role={ROLE} port={PORT} lag={STORE.lag}s", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
