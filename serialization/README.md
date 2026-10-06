# Serialisierung: Proprietäres Binärformat vs. Protobuf vs. FlatBuffers

Drei Implementierungen derselben Nachricht über rohes TCP (Port 8080):

| Feld | Wert |
|---|---|
| `cmd` | `2` |
| `text` | `"Hallo aus dem rohen Socket!"` (27 Bytes) |

Alle Varianten nutzen TCP direkt (kein HTTP). Protobuf und FlatBuffers verwenden zusätzlich ein 2-Byte-Längenpräfix für das Framing.

## Verzeichnisstruktur

```
serialization/
├── proprietary_binary/   eigenes Format: [cmd:1][len:2][text]
├── protobuf/             protobuf-c:     [len:2][Protobuf-Bytes]
└── flatbuffers/          flatcc:         [len:2][FlatBuffer-Bytes]
```

## Bauen und Ausführen

Server und Client jeweils in zwei Terminals starten (zuerst den Server).

### Proprietäres Binärformat

```bash
cd proprietary_binary
gcc server.c -o server
gcc client.c -o client

./server
./client
```

### Protobuf (protobuf-c)

Abhängigkeiten:

```bash
sudo apt install protobuf-c-compiler libprotobuf-c-dev
```

Bauen:

```bash
cd protobuf
protoc-c --c_out=. format.proto
gcc server.c format.pb-c.c -lprotobuf-c -o server
gcc client.c format.pb-c.c -lprotobuf-c -o client

./server
./client
```

### FlatBuffers (flatcc)

flatcc einmalig aus dem Quellcode bauen:

```bash
cd flatbuffers
git clone https://github.com/dvidelabs/flatcc.git
cd flatcc && scripts/initbuild.sh make && scripts/build.sh && cd ..
```

Bauen:

```bash
flatcc/bin/flatcc -a format.fbs
gcc server.c -I flatcc/include -I . -L flatcc/lib -lflatccrt -o server
gcc client.c -I flatcc/include -I . -L flatcc/lib -lflatccrt -o client

./server
./client
```

### Wire-Bytes mitschneiden (optional)

```bash
sudo tcpdump -i lo -X port 8080
```

## Wire-Format

### Proprietär (30 Bytes)

```
02 | 00 1b | 48 61 6c 6c 6f ...
cmd  len=27  "Hallo aus dem rohen Socket!"
```

### Protobuf (2 + 31 = 33 Bytes)

```
00 1f | 08 02 | 12 1b | 48 61 6c 6c 6f ...
len   | Feld 1 | Feld 2, len=27 | Text
      | cmd=2  |
```

- `08` = Tag (Feld 1, Varint), `12` = Tag (Feld 2, längenpräfixiert)
- Varints: kleine Zahlen belegen 1 Byte

### FlatBuffers (2 + ~50–60 Bytes)

```
len | Root-Offset | vtable | Tabelle (cmd, Offset→text) | [len:4][text][\0][Padding]
```

- 4-Byte-Offsets und -Längen, Alignment-Padding
- Genaue Größe: siehe Ausgabe von `./client`

## Vergleich

| Kriterium | Proprietär | Protobuf | FlatBuffers |
|---|---|---|---|
| Bytes (Payload + Framing) | **30** | 33 | ~52–62 |
| Header-/Format-Overhead | 3 B | ~6 B | ~25–35 B |
| Lesen | direkter Zugriff über feste Offsets | Dekodieren (`unpack`) | direkter Zugriff über vtable |
| Zero-Copy beim Lesen | ja | nein (Allokation + Kopie) | ja |
| Schreiben | `memcpy` | `pack` | Builder (von hinten aufgebaut) |
| Schema-Evolution | nein, jede Änderung bricht die Kompatibilität | ja (neue Felder, optionale Felder) | ja (neue Felder am Ende) |
| Validierung | manuell | implizit beim `unpack` | explizit (`Message_verify_as_root`) |
| Mehrsprachigkeit | selbst implementieren | Code-Generator für viele Sprachen | Code-Generator für viele Sprachen |
| Abhängigkeiten | keine | `libprotobuf-c` | `libflatccrt` |
| Tooling / Debugging | keines | `protoc --decode`, Wireshark | `flatc --json` |

### Proprietäres Format

- **Vorteile:** minimaler Overhead, keine Abhängigkeiten, zero-copy lesbar, deterministische Größe
- **Nachteile:** keine Versionierung, keine Erweiterbarkeit, Parser und Sicherheit liegen in eigener Verantwortung, keine Interoperabilität
- **Geeignet für:** Embedded, harte Echtzeit, geschlossene Systeme mit fester Gegenstelle

### Protobuf

- **Vorteile:** kompakt (Varints), Schema-Evolution, großes Ökosystem, Standard bei gRPC
- **Nachteile:** Dekodieren nötig (CPU, Allokationen), kein wahlfreier Zugriff
- **Geeignet für:** RPC, Microservices, Messaging, allgemeiner Datenaustausch

### FlatBuffers

- **Vorteile:** zero-copy, wahlfreier Zugriff auf einzelne Felder, Schema-Evolution
- **Nachteile:** größere Nachrichten (Offsets, Padding), umständlicher Builder, Verifier bei nicht vertrauenswürdigen Daten nötig
- **Geeignet für:** große Daten mit selektivem Zugriff, Spiele, `mmap`-Dateien, latenzkritische Systeme

## Fazit

- **Format vs. Transport trennen:** Alle drei Formate sind transportunabhängig. Der große Overhead von gRPC/HTTP stammt aus der Transportschicht, nicht aus dem Format.
- **Größe:** Proprietär ≈ Protobuf << FlatBuffers. Gegenüber Protobuf spart das eigene Format nur wenige Bytes.
- **Lesegeschwindigkeit:** Proprietär ≈ FlatBuffers > Protobuf, weil beide ohne Dekodieren auskommen.
- **Das proprietäre Format vereint Kompaktheit und Zero-Copy, verzichtet dafür aber auf Erweiterbarkeit, Interoperabilität und geprüfte Parser.** Es lohnt sich nur bei besonderen Randbedingungen (Embedded, Echtzeit, Hardware-Parsing).