# Mini-Spark

Stark vereinfachter Nachbau der Spark-Architektur, um die Grundkonzepte zu verstehen:

- **Python-Client ↔ JVM über Py4J** (wie PySpark)
- **Lazy Evaluation**: Transformationen bauen nur einen Plan, Actions führen aus
- **Logischer und physischer Plan**
- **Partitionen, Tasks, Stages**
- **Map → Shuffle → Reduce**

## Aufbau

```
mini-spark/
├── jvm-gateway/          # "Spark-Engine" in Java
│   ├── MiniSpark.java      # Entry Point (≈ SparkSession), startet den GatewayServer
│   ├── MiniDataFrame.java  # immutable DataFrame, hält nur einen Plan (≈ Dataset)
│   ├── Plan.java           # logische Plan-Knoten: Range, Filter, Multiply
│   ├── Engine.java         # physischer Plan, Tasks, Map/Shuffle/Reduce
│   └── py4j-0.10.9.9.jar
└── pyspark/              # Python-Client
    └── src/pyspark/main.py # dünne Wrapper-Klassen DataFrame / SparkSession
```

## Konzepte

### Python ↔ JVM (Py4J)

`MiniSpark` startet einen `GatewayServer` auf `127.0.0.1:25333`. Python verbindet sich mit
`JavaGateway()` und bekommt über `gateway.entry_point` einen **Proxy** auf das `MiniSpark`-Objekt.
Jeder Methodenaufruf auf einem Proxy wird als Textnachricht per TCP an die JVM geschickt (RPC).

Gibt Java ein Objekt zurück, legt Py4J es in einer **Objekttabelle** ab (`o0`, `o1`, …) und
Python erhält nur die ID. Primitive Werte (`int`, `String`, …) werden direkt als Wert übertragen.

Den Verkehr mitschneiden:
```bash
sudo tcpdump -i lo -A -s0 'tcp port 25333'
```

### Lazy Evaluation

```python
df = spark.range(0, 20).filter(">", 5).multiply(10)   # baut nur einen Plan
df.collect()                                           # erst hier wird gerechnet
```

Jede Transformation erzeugt in der JVM ein **neues** `MiniDataFrame`, dessen Plan den alten
als Kind enthält:

```
Project(x * 10)
  Filter(x > 5)
    Range(0, 20)
```

Ungültige Operatoren werden sofort geprüft (≈ Analyzer in Spark), ausgeführt wird erst bei
einer Action (`collect`, `count`, `count_by_mod`).

### Physischer Plan

`Engine.physicalPlan` macht aus dem Baum eine **Stage**: eine Datenquelle (`Range`) plus eine
Pipeline von Operationen, die pro Zeile direkt hintereinander laufen (≈ Pipelining in Spark).

```
Scan Range(0, 20) in 4 partitions
  -> Filter(x > 5)
  -> Project(x * 10)
```

### Partitionen und Tasks

Die Quelle wird in `NUM_PARTITIONS = 4` Partitionen aufgeteilt. Pro Partition läuft ein
**Task** auf einem Thread-Pool (≈ Executors in `local[*]`).

### Map → Shuffle → Reduce

`count_by_mod(3)` zählt, wie oft jeder Rest `x % 3` vorkommt:

| Phase | Was passiert |
|---|---|
| **Map** | jeder Task verarbeitet seine Partition, bildet `key = x % 3`, zählt lokal vor (Combiner) und sortiert nach `key % NUM_REDUCERS` in Buckets |
| **Shuffle** | Reducer `r` holt Bucket `r` von **allen** Map-Tasks |
| **Reduce** | jeder Reducer summiert die Teilergebnisse für seine Keys |

`collect()` / `count()` brauchen nur die Map-Phase. Ein Shuffle ist nur nötig, wenn nach einem
Key gruppiert wird. In Spark ist genau das die Grenze zwischen zwei **Stages**.

### Zuordnung zu echtem Spark

| Mini-Spark | Spark |
|---|---|
| `MiniSpark` | `SparkSession` |
| `MiniDataFrame` / Python `DataFrame._jdf` | `Dataset` / `DataFrame._jdf` |
| `Plan.*` | `LogicalPlan` |
| `Engine.Stage` | Stage mit Whole-Stage Codegen |
| Thread-Pool-Tasks | Tasks auf Executors |
| Buckets / Reducer | Shuffle-Write / Shuffle-Read |

Bewusst weggelassen: Optimizer (Catalyst), Fehlertoleranz, echte Verteilung auf mehrere Rechner.

## Voraussetzungen

- JDK ≥ 17 (`javac -version`)
- [uv](https://docs.astral.sh/uv/) und Python ≥ 3.14

## Starten

**1. JVM-Gateway kompilieren und starten** (Terminal 1)

```bash
cd mini-spark/jvm-gateway
rm -f *.class
javac -cp py4j-0.10.9.9.jar *.java
java -cp py4j-0.10.9.9.jar:. MiniSpark
```

Der Server läuft, bis er mit `Ctrl+C` beendet wird. Hier erscheinen die Logs der Map- und
Reduce-Tasks. Nach Änderungen am Java-Code neu kompilieren und neu starten.

**2. Python-Client ausführen** (Terminal 2)

```bash
cd mini-spark/pyspark
uv sync
uv run python src/pyspark/main.py
```

## Erwartete Ausgabe

Python:
```
== Logical Plan ==
Filter(x < 150)
  Project(x * 10)
    Filter(x > 5)
      Range(0, 20)

== Physical Plan ==
Scan Range(0, 20) in 4 partitions
  -> Filter(x > 5)
  -> Project(x * 10)
  -> Filter(x < 150)
9
[60, 70, 80, 90, 100, 110, 120, 130, 140]
{0: 5, 1: 5, 2: 4}
```

JVM (Reihenfolge variiert, da parallel):
```
[pool-1-thread-1] map task 0: rows 0..4
[pool-1-thread-2] map task 1: rows 5..9
[pool-1-thread-3] map task 2: rows 10..14
[pool-1-thread-4] map task 3: rows 15..19
[pool-1-thread-1] reduce task 0: {0=5, 2=4}
[pool-1-thread-2] reduce task 1: {1=5}
```