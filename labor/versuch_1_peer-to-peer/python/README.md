# P2P-Snake (Labor Verteilte Systeme – Versuch 1)

Verteiltes Mehrspieler-Spiel in einer reinen Peer-to-Peer-Architektur. Die Peers kommunizieren per **UDP** und tauschen Nachrichten im **JSON**-Format aus. Jeder Peer hält eine vollständige Kopie des Spielzustands und stellt ihn im Terminal dar.

## Starten

Benötigt **Python ≥ 3.11** (wegen `loop.sock_recvfrom`/`sock_sendto`). Es werden keine externen Pakete gebraucht.

```bash
cd python
python main.py
```

Beim Start fragt jeder Peer nacheinander ab:

1. **Nickname**
2. **Farbe** (z. B. `rot`, `gruen`, `blau`, `gelb`)
3. **Port** (muss einer der bekannten Ports aus `config.PEERS` sein)
4. **Join**: `IP:Port` eines bereits laufenden Peers (*Friend*). Bleibt das Feld leer, startet ein neues Spiel.

Gesteuert wird mit den Pfeiltasten. Jeder Tastendruck bewegt den Spieler um genau ein Feld.

## Spielregeln (Kurzfassung)

- Quadratisches Spielfeld `GRID_SIZE × GRID_SIZE`.
- 2 bis 4 Spieler mit eindeutigem Nickname und eindeutiger Farbe.
- Startposition: zufällig eine freie Randmitte (oben, unten, links, rechts).
- Jeder Spieler hinterlässt eine **dauerhafte Spur**. Spuren und der Spielfeldrand sind Wände.
- Wer gegen eine Wand oder eine Spur fährt (auch die eigene), scheidet aus.
- Wer `MAX_TIME` Sekunden lang keine Taste drückt, scheidet ebenfalls aus.
- Gewonnen hat, wer als Letzter übrig bleibt. Scheiden alle gleichzeitig aus, ist es ein Unentschieden.

## Projektstruktur

```text
python/
├── main.py                 # Ablauf: Register → Join → Announce → Spielschleifen
└── src/
    ├── config.py           # PEERS, GRID_SIZE, MAX_TIME
    ├── state.py            # gemeinsamer Zustand (players) + Lamport-Uhr
    ├── register.py         # Benutzereingaben
    ├── send_join.py        # JOIN senden, auf JOIN_ACK/JOIN_REJECT warten
    ├── msg_templates.py    # Nachrichtenformate
    ├── msg_handles.py      # Handler für empfangene Nachrichten
    ├── helper_functions.py # Kollision, Startposition, Inaktivität, Senden
    └── viz.py              # Darstellung im Terminal (ANSI)
```

## Architektur

Nach dem Join laufen in einer `asyncio`-Eventloop drei nebenläufige Aufgaben:

| Aufgabe | Funktion |
|---|---|
| `on_key` | Liest Pfeiltasten, prüft auf Kollision, sendet `MOVE` bzw. `ELIMINATED` |
| `receiver_loop` | Empfängt alle Nachrichten und verteilt sie nach `type` an die Handler |
| `inactivity_check` | Prüft alle 0,2 s die Inaktivität aller Spieler und zeichnet das Spielfeld neu |

**Zustand:** `state.players` enthält einen Eintrag pro Spieler mit `ip`, `port`, `nickname`, `color`, `trail`, `move_no`, `out`, `last_move` und `out_at`. Der eigene Spieler steht unter dem Schlüssel `"me"`, alle anderen unter `"ip_port"`.

**Verantwortung:**
- Jeder Peer prüft **nur seine eigene** Kollision und meldet sie per `ELIMINATED`.
- Inaktivität und Spielende erkennt jeder Peer **lokal**, ohne eigene Nachricht.

## Protokoll

### Nachrichtentypen

| Typ | Richtung | Inhalt | Zweck |
|---|---|---|---|
| `JOIN` | neu → Friend | `nickname`, `color` | Beitrittsanfrage |
| `JOIN_ACK` | Friend → neu | `players` (alle Spieler inkl. Spuren) | Beitritt angenommen, kompletter Spielzustand |
| `JOIN_REJECT` | Friend → neu | `reason` (`NICKNAME_TAKEN`, `COLOR_TAKEN`, `GAME_FULL`) | Beitritt abgelehnt |
| `ANNOUNCE` | neu → alle | `nickname`, `color`, `trail` (Startposition) | Neuen Spieler bekannt machen |
| `MOVE` | Spieler → alle | `trail` (komplett), `direction`, `move_no` | Zug |
| `ELIMINATED` | Spieler → alle | `reason` (`WALL`, `TRAIL`), `move_no` | Ausscheiden durch Kollision |

Jede Nachricht enthält zusätzlich `type` und `clock` (Lamport-Zeitstempel). Die Absenderadresse wird aus dem UDP-Header entnommen (`recvfrom`). Gesendet und empfangen wird über denselben gebundenen Socket.

Beispiel:
```json
{ "type": "MOVE", "clock": 17, "trail": [[12, 24], [12, 23], [13, 23]], "direction": "right", "move_no": 2 }
```

### Ablauf beim Beitritt

```text
Neuer Peer B                Friend A               Peer C
    | --- JOIN ------------->  |                      |
    |                          | prüft Nickname, Farbe, Spielerzahl
    | <-- JOIN_ACK(players) -- |                      |
    | wählt freie Startposition                       |
    | --- ANNOUNCE ----------> | -------------------> |
    | --- MOVE (Pfeiltaste) -> | -------------------> |
```

- **Erster Spieler:** Ohne Friend-Adresse wird ein neues Spiel angelegt. Dabei werden keine Nachrichten ausgetauscht.
- **Der Friend nimmt beim `JOIN` niemanden auf**, sondern prüft nur und antwortet. Aufgenommen wird der neue Spieler erst beim `ANNOUNCE`, und zwar bei allen Peers. Dadurch ist ein wiederholtes `JOIN` harmlos.

### Designentscheidungen

- **Senden an alle bekannten Peers:** `MOVE`, `ANNOUNCE` und `ELIMINATED` gehen an alle Adressen in `PEERS`, auch wenn dort niemand online ist (laut Aufgabenstellung erlaubt). Nachrichten von unbekannten Absendern werden ignoriert.
- **`MOVE` enthält die komplette Spur:** Geht ein `MOVE` verloren, gleicht das nächste den Verlust aus. Duplikate und veraltete Nachrichten werden über `move_no` verworfen (`move_no` ≤ bekannter Stand).
- **`JOIN_ACK` enthält alle Spuren:** Auch die von ausgeschiedenen Spielern, damit ein neuer Peer sofort das vollständige Spielfeld kennt und eine freie Startposition wählen kann.
- **Inaktivität:** Ein Spieler gilt als ausgeschieden, wenn sich sein `move_no` `MAX_TIME` Sekunden lang nicht erhöht hat. Das erkennt jeder Peer anhand seiner lokalen Uhr. Das deckt auch abgestürzte Peers ab.
- **Spielende:** Mindestens 2 Spieler waren beteiligt, und höchstens 1 ist noch im Spiel. Jeder Peer erkennt das selbst.

## Lamport-Uhr

Jeder Peer führt eine logische Uhr (`state.clock`), die nach den Lamport-Regeln aktualisiert wird:

```python
# vor jedem Senden (state.tick)
clock += 1

# bei jedem Empfang (state.on_receive)
clock = max(clock, msg["clock"]) + 1
```

Dadurch gilt: Hat ein Ereignis a ein Ereignis b beeinflusst (z. B. weil b nach dem Empfang von a passiert), dann ist `clock(a) < clock(b)`. Zusammen mit dem Port als Tiebreaker ergibt `(clock, port)` eine **totale Ordnung** aller Ereignisse, die auf jedem Peer gleich ist.

**Abgrenzung zu `move_no`:** `move_no` zählt nur die Züge **eines** Spielers und dient zur Erkennung von Duplikaten sowie zur Anzeige. Die Lamport-Uhr ordnet Ereignisse **verschiedener** Spieler.

**Aktueller Stand:** Die Uhr wird mitgeführt und synchronisiert, aber noch nicht ausgewertet. Die Aufgabenstellung erlaubt die Annahme, dass Eingaben nicht gleichzeitig erfolgen.

**Relevant wäre sie für:**
1. **Gleichzeitige Züge auf dasselbe Feld** (optionale Anforderung 21): Ohne Uhr hält jeder Peer seinen eigenen Zug für gültig, und die Replikate werden inkonsistent. Mit `(clock, port)` entscheiden alle Peers einheitlich, welcher Zug zuerst kam. Der spätere gilt als Kollision.
2. **Rangfolge bei fast gleichzeitigem Ausscheiden:** Die Rangfolge basiert derzeit auf der lokalen Empfangszeit (`out_at`) und kann sich daher zwischen Peers unterscheiden. Mit dem `clock`-Wert der `ELIMINATED`-Nachricht wäre sie überall gleich.
3. **Gleichzeitige Joins mit derselben Farbe** über verschiedene Friends.

## Bekannte Einschränkungen

- **UDP-Verlust:** Ein verlorenes `JOIN` oder `JOIN_ACK` wird nicht wiederholt. Nach 2 s Timeout bricht der Join ab. Ein verlorenes `ELIMINATED` wird durch die Inaktivitätserkennung aufgefangen, allerdings verzögert.
- **Gleichzeitige Ereignisse** (siehe Lamport-Uhr) werden nicht aufgelöst.
- **Split Brain:** Starten zwei Peers gleichzeitig ohne Friend, entstehen zwei getrennte Spiele.
- **Keine Persistenz:** Der Zustand liegt nur im Arbeitsspeicher.
- Darstellung im Terminal (ANSI-Escape-Codes, 256 Farben), kein grafisches Fenster.