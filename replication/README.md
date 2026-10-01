# Single-Leader-Replikation: Read-your-writes & Monotonic Reads

Ein Leader, zwei Follower mit asynchroner, künstlich verzögerter Replikation (nur Python-Standardbibliothek).

```
client ──write──▶ leader ──log (pull)──▶ follower1 (lag 0.5s)
   └────read────▶ follower1 / follower2  └──▶ follower2 (lag 3s)
```

## Start

```bash
docker compose up -d --build
docker compose logs -f leader follower1 follower2   # Replikation live mitverfolgen
```

## Szenarien

| Befehl | Was passiert |
|---|---|
| `docker compose run --rm client ryw --mode naive` | Write auf den Leader, sofort Read von einem Follower: eigener Write fehlt |
| `docker compose run --rm client ryw --mode guaranteed` | Client schickt die LSN seines Writes als `min_lsn` mit und fällt auf den Leader zurück |
| `docker compose run --rm client monotonic --mode naive` | Zufälliger Follower pro Read: der Zähler springt zurück |
| `docker compose run --rm client monotonic --mode sticky` | Nutzer fest einem Follower zugeordnet: Reads sind monoton (aber evtl. alt) |
| `docker compose run --rm client monotonic --mode min-lsn` | Client verlangt mindestens die zuletzt gesehene Version |
| `docker compose run --rm client lag follower2 10` | Lag zur Laufzeit ändern |
| `docker compose run --rm client status` | `applied_lsn` und Lag aller Knoten |

## API der Knoten

- `POST /write {"key", "value"}`: nur auf dem Leader, liefert `lsn`
- `GET /read?key=..&min_lsn=..&timeout=..`: wartet bis `applied_lsn >= min_lsn`, sonst `503`
- `GET /log?since=N`: Replikationslog (Leader)
- `POST /admin/lag {"lag": s}`: Lag setzen (Follower)
- `GET /status`
