# Java RMI – Beispiel: Remote Calculator

## Konzepte

```
Client                         Registry (Port 1099)              Server
  |  lookup("Calculator") -------->|                               |
  |<------- Stub (Proxy) ----------|<--- rebind("Calculator") -----|
  |                                                                |
  |  stub.add(3,4)  ==== TCP (Serialisierung der Argumente) ====>  CalculatorImpl.add
  |  <================== Rueckgabewert (serialisiert) ============ |
```

| Baustein | Datei | Rolle |
|---|---|---|
| Remote-Interface | `Calculator.java` | erweitert `Remote`, jede Methode wirft `RemoteException` |
| Implementierung | `CalculatorImpl.java` | erweitert `UnicastRemoteObject` → wird automatisch exportiert |
| Wertobjekt | `Result.java` | `Serializable` → wird als **Kopie** übertragen |
| Server | `Server.java` | startet Registry, registriert Objekt per Name |
| Client | `Client.java` | holt Stub aus Registry, ruft Methoden auf |

**Parameterübergabe:**
- `Remote`-Objekte → per **Referenz** (Stub wird übertragen)
- `Serializable`-Objekte / Primitive → per **Wert** (Kopie)
- Alles andere → `NotSerializableException`

## Ausführen

```bash
javac -d out *.java

# Terminal 1
java -cp out Server

# Terminal 2
java -cp out Client
```

Über Rechnergrenzen: Server mit `-Djava.rmi.server.hostname=<IP des Servers>` starten,
Client mit `java -cp out Client <IP des Servers>`.

## Übungsideen
1. Methode `void store(double)` / `double recall()` hinzufügen (Server-Zustand, Thread-Safety!).
2. Ein nicht-serialisierbares Objekt zurückgeben → Fehler beobachten.
3. Callback: Client implementiert selbst ein `Remote`-Interface und registriert sich beim Server.
