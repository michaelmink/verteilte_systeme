# PRE-LAB

## 1.
Was ist der prinzipielle Unterschied zwischen verteilten Anwendungen, die nach dem
Peer-to-Peer-Prinzip arbeiten und solchen, die das Client-Server-Prinzip anwenden.

* Client-Server: Die Rollen sind asymmetrisch. Ein zentraler Server stellt Dienste bereit, Clients stellen Anfragen und kommunizieren nur mit dem Server, nicht untereinander. Der Server ist ein Single Point of Failure und ein möglicher Engpass, erleichtert aber Konsistenz und Verwaltung.

* Peer-to-Peer: Die Rollen sind symmetrisch. Jeder Peer ist gleichzeitig Client und Server, bietet also Dienste an und nutzt sie. Es gibt keine zentrale Instanz, die Peers kommunizieren direkt miteinander und können dynamisch beitreten und das Netz verlassen. Das System skaliert und ist ausfallsicherer, dafür sind Konsistenz, Peer-Discovery und Koordination schwieriger.


## 2.
Angenommen ein Prozess muss gleichzeitig auf eine Benutzereingabe von der
Konsole und auf das Eintreffen einer Nachricht warten. Wie realisieren Sie dies?

* Python: Mit asyncio. Eine Event-Loop überwacht mehrere Ein-/Ausgabequellen gleichzeitig. Intern nutzt sie select/epoll. Die Konsole wird mit loop.add_reader(sys.stdin.fileno(), callback) registriert, der Socket wird mit await loop.sock_recvfrom(sock, ...) abgefragt. Sobald eine der Quellen Daten hat, wird die zugehörige Coroutine bzw. der Callback ausgeführt. Kein Aufruf blockiert den ganzen Prozess.

  Alternativen: Ein Thread pro Quelle (einer blockiert auf der Konsole, einer auf dem Socket) oder direkt select.select([sys.stdin, sock], [], []).

* Java: Typischerweise zwei Threads. Einer liest mit Scanner/BufferedReader von System.in, der andere blockiert in DatagramSocket.receive(). Den Datenaustausch übernimmt eine threadsichere Queue, z. B. BlockingQueue. Alternativ gibt es NIO mit DatagramChannel und einem Selector, System.in lässt sich dort aber nicht registrieren.


## 3.
Wie realisieren Sie das Empfangen einer einzelnen UDP-Nachricht über eine SocketSchnittstelle mit der Programmiersprache Ihrer Wahl (Java, Python, C, C++, C#).
Bitte auch alle vorbereitenden Schritte.

Python und Java bieten dafür Wrapper-Funktionen, die die entsprechenden Systemaufrufe der POSIX-Socket-Schnittstelle (socket, bind, recvfrom, close) aufrufen; unter Windows übernimmt dies die weitgehend kompatible Winsock-API.

Python
```python
import socket

# 1. Socket erzeugen: AF_INET = IPv4, SOCK_DGRAM = UDP (SOCK_STREAM wäre TCP)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 2. An lokale Adresse und Port binden (Tupel!)
sock.bind(("127.0.0.1", 5000))

# 3. Auf eine Nachricht warten (blockiert); Puffergröße; groß genug für jedes UDP-Datagramm.
data, addr = sock.recvfrom(65535)     # addr = (IP, Port) des Absenders

# 4. Bytes dekodieren
print(f"{addr}: {data.decode('utf-8')}")

# 5. Socket schließen
sock.close()
```

Java
```java
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.nio.charset.StandardCharsets;

try (DatagramSocket socket = new DatagramSocket(5000)) {        // erzeugen + binden
    byte[] buffer = new byte[65535];
    DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
    socket.receive(packet);                                       // blockiert
    String msg = new String(packet.getData(), 0, packet.getLength(), StandardCharsets.UTF_8);
    System.out.println(packet.getAddress() + ":" + packet.getPort() + " -> " + msg);
}                                                                 // schließt automatisch
```


## 4.
Wie erzeugen Sie eine Nachricht mit einem Integer und einem String als Inhalt mit
einer Programmiersprache Ihrer Wahl (Java, Python, C/C#/C++). Verwenden Sie, wo
möglich, JSON-basierte Nachrichten

Python:
```python
import json
msg = {
    "key_1": 0,
    "key_2": "string",
    }
# convert dict to json and encode as binary
msg = json.dumps(msg).encode("utf-8") 
```

Java:
```java
import org.json.JSONObject;
import org.json.JSONArray;
import java.nio.charset.StandardCharsets;
import java.util.List;

JSONObject msg = new JSONObject();
msg.put("key_1", 0);
msg.put("key_2", "string");
byte[] data = msg.toString().getBytes(StandardCharsets.UTF_8);
```

## 5.
Wie erzeugen Sie eine Nachricht mit einem Integer und einer Liste mit Strings als
Inhalt mit einer Programmiersprache Ihrer Wahl (Java, Python, C/C#/C++).
Verwenden Sie, wo möglich, JSON-basierte Nachrichten.

Python:
```python
import json
msg = {
    "key_1": 0,
    "key_2": ["string_1", "string_2"],
    }
# convert dict to json and encode as binary
msg = json.dumps(msg).encode("utf-8") 
```

Java:
```java
import org.json.JSONObject;
import org.json.JSONArray;
import java.nio.charset.StandardCharsets;
import java.util.List;

JSONObject msg2 = new JSONObject();
msg2.put("key_1", 0);
msg2.put("key_2", new JSONArray(List.of("string_1", "string_2")));
byte[] data = msg.toString().getBytes(StandardCharsets.UTF_8);
```

## 6.
Was könnte eine Datenstruktur aussehen, welche bei einem "4-Gewinnt" MultiPlayer-Spiel den auf allen Peers replizierten SPIELZUSTAND zu einem gegebenen
Zeitpunkt wiedergibt?

Python:
```python
SPIELZUSTAND = {
    "rows": 6,
    "cols": 7,
    "board": [[None] * 7 for _ in range(6)],   # board[row][col] = None | "rot" | "gelb"
    "players": {
        "rot":  {"nickname": "alice", "addr": ("192.168.1.10", 5000)},
        "gelb": {"nickname": "bob",   "addr": ("192.168.1.11", 5000)},
    },
    "turn": "rot",          # wer ist am Zug
    "move_no": 0,           # Anzahl bisheriger Züge (Reihenfolge, Duplikaterkennung)
    "status": "running",    # "running" | "won" | "draw"
    "winner": None,
}
```

Java:
```java
import java.util.Map;
import java.util.HashMap;

public class Spielzustand {
    public static final int ROWS = 6, COLS = 7;
    public String[][] board = new String[ROWS][COLS];   // null | "rot" | "gelb"
    public Map<String, Player> players = new HashMap<>(); // Farbe -> Spieler
    public String turn = "rot";
    public int moveNo = 0;
    public String status = "running";                  // running | won | draw
    public String winner = null;
}

record Player(String nickname, String ip, int port) {}
```



## Anhang

### A. HashMap (Java) vs. dict (Python)

`HashMap` ist das Java-Gegenstück zum Python-`dict`. Beide speichern Schlüssel-Wert-Paare in einer Hashtabelle. Zugriff, Einfügen und Löschen dauern im Mittel O(1).

| | Python `dict` | Java `HashMap` |
|---|---|---|
| Anlegen | `d = {}` | `Map<String, Integer> d = new HashMap<>();` |
| Schreiben | `d["a"] = 1` | `d.put("a", 1);` |
| Lesen | `d["a"]` bzw. `d.get("a")` | `d.get("a")` (`null`, falls nicht vorhanden) |
| Enthalten? | `"a" in d` | `d.containsKey("a")` |
| Typen | beliebig, auch gemischt | fest über Generics `<K, V>` |
| Reihenfolge | Einfügereihenfolge (ab Python 3.7) | keine garantierte Reihenfolge |

- Einfügereihenfolge wie beim `dict`: `LinkedHashMap`. Sortierte Schlüssel: `TreeMap`.
- Eigene Klassen als Schlüssel müssen `equals()` und `hashCode()` implementieren (in Python `__eq__` und `__hash__`). Ein Java-`record` bringt beides automatisch mit.

### B. UTF-8

UTF-8 ist eine **Zeichenkodierung**. Sie legt fest, wie Text in Bytes umgewandelt wird. Sockets und Dateien übertragen nur Bytes, daher muss ein String vor dem Senden **kodiert** und nach dem Empfangen **dekodiert** werden.

- **Unicode** ordnet jedem Zeichen eine eindeutige Nummer zu (Codepoint), z. B. `A` = U+0041, `ü` = U+00FC.
- **UTF-8** speichert diese Nummer mit **variabler Länge** von 1 bis 4 Bytes:

| Zeichen | Codepoint | UTF-8-Bytes | Länge |
|---|---|---|---|
| `A` | U+0041 | `41` | 1 Byte |
| `ü` | U+00FC | `C3 BC` | 2 Byte |
| `€` | U+20AC | `E2 82 AC` | 3 Byte |
| `🐍` | U+1F40D | `F0 9F 90 8D` | 4 Byte |

Vorteile:
- **ASCII-kompatibel:** Die Zeichen 0–127 sind identisch mit ASCII und belegen je 1 Byte.
- **Vollständig:** Alle Unicode-Zeichen sind darstellbar, auch Umlaute und Emojis.
- **Standard:** Im Web verbreitet und für JSON vorgeschrieben (RFC 8259).

Verwendung:

```python
data = json.dumps(msg).encode("utf-8")   # str  -> bytes (senden)
msg  = json.loads(data.decode("utf-8"))  # bytes -> str  (empfangen)
```

```java
byte[] data = msg.toString().getBytes(StandardCharsets.UTF_8);   // senden
String text = new String(data, StandardCharsets.UTF_8);          // empfangen
```

**Wichtig:**
- Sender und Empfänger müssen **dieselbe Kodierung** verwenden. Sonst wird z. B. aus „grün“ ein „grÃ¼n“. Die Kodierung sollte daher immer ausdrücklich angegeben werden und nicht von der Systemvoreinstellung abhängen.
- Zeichenanzahl ≠ Byteanzahl: `"grün"` hat 4 Zeichen, aber 5 Bytes. Für die Größe eines UDP-Datagramms zählen die Bytes.