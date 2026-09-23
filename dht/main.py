"""Übungsskript: Verteilte Hashtabelle (DHT) nach dem Chord-Prinzip.

Eine verteilte Hashtabelle verteilt Schlüssel-Wert-Paare auf viele Knoten,
ohne dass ein zentraler Server nötig ist. Dieses Skript zeigt die Kernideen:

1. Consistent Hashing: Knoten und Schlüssel werden auf denselben Ring
   (0 .. 2**m - 1) abgebildet.
2. Zuständigkeit: Für einen Schlüssel ist der erste Knoten im Uhrzeigersinn
   (der "Nachfolger") verantwortlich.
3. Lookup: Statt jeden Knoten zu kennen, nutzt jeder Knoten eine "Finger-Tabelle"
   als Abkürzung, um in O(log N) Schritten zum Ziel zu springen.

Das Skript ist eine In-Memory-Simulation (kein echtes Netzwerk), damit man die
Konzepte isoliert nachvollziehen kann.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


# Größe des Identifier-Rings: IDs liegen im Bereich [0, 2**M - 1].
# Klein gewählt, damit man den Ring leicht überblicken kann.
M = 6
RING_SIZE = 2**M


def hash_id(key: str) -> int:
    """Bildet einen beliebigen String stabil auf eine Ring-Position ab."""
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return int(digest, 16) % RING_SIZE


def in_interval(x: int, start: int, end: int, *, inclusive_end: bool) -> bool:
    """Prüft, ob x im Ring-Intervall (start, end] bzw. (start, end) liegt.

    Der Ring ist zyklisch, daher muss der Fall start > end (Überlauf über 0)
    gesondert behandelt werden.
    """
    if start == end:
        # Ganzer Ring ist gemeint (außer ggf. dem offenen Startpunkt).
        return x != start or inclusive_end
    if start < end:
        return start < x <= end if inclusive_end else start < x < end
    # Intervall läuft über die 0 hinweg (z. B. (60, 5]).
    return x > start or (x < end or (x == end and inclusive_end))


@dataclass
class Node:
    """Ein Knoten im Chord-Ring."""

    name: str
    node_id: int = field(init=False)
    store: dict[str, str] = field(default_factory=dict)
    finger: list["Node"] = field(default_factory=list)
    successor: "Node" = field(init=False)
    predecessor: "Node | None" = field(default=None)

    def __post_init__(self) -> None:
        self.node_id = hash_id(self.name)
        self.successor = self  # Anfangs ist der Knoten allein im Ring.

    def __repr__(self) -> str:
        return f"Node({self.name}, id={self.node_id})"


class Chord:
    """Vereinfachter Chord-Ring als lokale Simulation."""

    def __init__(self) -> None:
        self.nodes: list[Node] = []

    def _sorted_nodes(self) -> list[Node]:
        return sorted(self.nodes, key=lambda n: n.node_id)

    def add_node(self, name: str) -> Node:
        node = Node(name)
        self.nodes.append(node)
        self._rebuild()
        return node

    def _rebuild(self) -> None:
        """Aktualisiert Nachfolger, Vorgänger und Finger-Tabellen aller Knoten.

        In echtem Chord passiert das inkrementell und verteilt; hier bauen wir
        es zur Übersichtlichkeit global neu auf.
        """
        ordered = self._sorted_nodes()
        count = len(ordered)
        for i, node in enumerate(ordered):
            node.successor = ordered[(i + 1) % count]
            node.predecessor = ordered[(i - 1) % count]
            node.finger = [
                self._first_node_from((node.node_id + 2**k) % RING_SIZE, ordered)
                for k in range(M)
            ]
        self._reassign_keys(ordered)

    @staticmethod
    def _first_node_from(position: int, ordered: list[Node]) -> Node:
        """Erster Knoten im Uhrzeigersinn ab position (inklusive)."""
        for node in ordered:
            if node.node_id >= position:
                return node
        return ordered[0]  # Überlauf über die 0.

    def _reassign_keys(self, ordered: list[Node]) -> None:
        """Sammelt alle Schlüssel ein und verteilt sie neu (bei Join/Leave nötig)."""
        all_items: dict[str, str] = {}
        for node in ordered:
            all_items.update(node.store)
            node.store = {}
        for key, value in all_items.items():
            self.responsible_node(key).store[key] = value

    def responsible_node(self, key: str) -> Node:
        """Direkte Berechnung des zuständigen Knotens (für Referenz/Tests)."""
        return self._first_node_from(hash_id(key), self._sorted_nodes())

    def lookup(self, start: Node, key: str) -> tuple[Node, list[Node]]:
        """Findet den zuständigen Knoten per Finger-Tabelle (O(log N)).

        Gibt den Zielknoten und den gelaufenen Pfad zurück, damit man die
        Sprünge über den Ring nachvollziehen kann.
        """
        key_id = hash_id(key)
        current = start
        path = [current]
        # Solange der Schlüssel nicht in (current, successor] liegt, weiterspringen.
        while not in_interval(key_id, current.node_id, current.successor.node_id, inclusive_end=True):
            next_hop = current.closest_preceding_node(key_id)
            if next_hop is current:
                break  # Kein besserer Finger -> wir sind faktisch am Ziel.
            current = next_hop
            path.append(current)
        target = current.successor
        if path[-1] is not target:
            path.append(target)
        return target, path

    def put(self, start: Node, key: str, value: str) -> Node:
        target, _ = self.lookup(start, key)
        target.store[key] = value
        return target

    def get(self, start: Node, key: str) -> tuple[str | None, Node]:
        target, _ = self.lookup(start, key)
        return target.store.get(key), target


def _closest_preceding_node(self: Node, key_id: int) -> Node:
    """Wählt aus der Finger-Tabelle den Knoten, der key_id am nächsten vorausgeht."""
    for finger_node in reversed(self.finger):
        if in_interval(finger_node.node_id, self.node_id, key_id, inclusive_end=False):
            return finger_node
    return self


# Methode nachträglich an Node hängen, damit lookup() sie aufrufen kann.
Node.closest_preceding_node = _closest_preceding_node  # type: ignore[attr-defined]


def demo() -> None:
    ring = Chord()
    for name in ["node-a", "node-b", "node-c", "node-d", "node-e"]:
        ring.add_node(name)

    print("Ring-Belegung (nach ID sortiert):")
    for node in ring._sorted_nodes():
        print(f"  id={node.node_id:>2}  {node.name}")

    print("\nDaten ablegen (put) von node-a aus:")
    daten = {
        "temperatur": "21.5",
        "luftfeuchte": "48",
        "status": "ok",
        "version": "1.2.3",
        "user:42": "alice",
    }
    start = ring.nodes[0]
    for key, value in daten.items():
        target = ring.put(start, key, value)
        print(f"  '{key}' (hash={hash_id(key):>2}) -> {target.name}")

    print("\nLookup mit Finger-Tabelle (Pfad über den Ring):")
    for key in ["temperatur", "user:42", "version"]:
        target, path = ring.lookup(start, key)
        route = " -> ".join(n.name for n in path)
        value, _ = ring.get(start, key)
        print(f"  '{key}': {route}  => {target.name} (value={value})")

    print("\nEin neuer Knoten tritt bei (node-f) — Schlüssel werden umverteilt:")
    ring.add_node("node-f")
    for key in daten:
        print(f"  '{key}' liegt jetzt auf {ring.responsible_node(key).name}")


# ---------------------------------------------------------------------------
# ÜBUNGEN
#
# 1. Implementiere eine Methode Chord.remove_node(name), die einen Knoten
#    entfernt und dabei dessen Schlüssel an den Nachfolger übergibt.
#    (Tipp: _rebuild() erledigt die Umverteilung bereits, wenn nodes stimmt.)
#
# 2. Erweitere put/get um Replikation: Lege jeden Schlüssel zusätzlich auf den
#    r nächsten Nachfolgern ab, damit Daten einen Knotenausfall überleben.
#
# 3. Zähle bei lookup() die Anzahl der Hops und zeige empirisch, dass sie mit
#    wachsender Knotenzahl etwa wie log2(N) steigt.
#
# 4. Ersetze das globale _rebuild() durch eine inkrementelle join()-Logik,
#    bei der nur betroffene Finger-Tabellen aktualisiert werden.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    demo()
