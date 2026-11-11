# 📊 Transaktions-Isolation & Verteilte Konsistenz

Ein praxisorientiertes Lehr-Repository zur Evolution von Datenbanksystemen. Dieses Projekt entwirrt das klassische Begriffs-Chaos zwischen **Transaktions-Isolation (ACID)** auf der Zeitachse und **Replikations-Konsistenz (BASE)** auf der Raumachse. 

Enthalten sind theoretische Leitfäden, visuelle Abgrenzungen und ein schlüsselfertiges, **3-stündiges Labor-Praktikum** mit vier verschiedenen Datenbank-Paradigmen (**PostgreSQL, MongoDB, CockroachDB, Delta Lake**).

---

## 🧭 Die Goldene Regel der Architektur

In der Praxis und Wissenschaft werden die Begriffe "Isolation" und "Konsistenz" oft fälschlicherweise zusammengeworfen. Dieses Repository baut auf einer fundamentalen Trennung auf:

*   **🔒 Isolation Levels (Die DB-Instanz):** Beziehen sich auf die **Logik innerhalb einer Datenbankinstanz** (die Zeitachse). Sie regeln, wie parallel laufende Transaktionen voneinander abgeschirmt werden (Schutz vor *Dirty Reads*, *Non-Repeatable Reads*, *Phantomen*).
*   **🌍 Consistency Models (Das Netzwerk):** Beziehen sich auf den **Datenabgleich zwischen mehreren Replikaten** im Netzwerk (die Raumachse). Sie regeln, wann und in welcher Reihenfolge physisch getrennte Server Updates austauschen (*Linearizability*, *Eventual Consistency*).

---

## 🗺️ Das Begriffs-Sammelsurium: Richtig eingeordnet

| Dimension | 🏢 Centralized Database (Zentral) | 🌍 Distributed Database (Verteilt) |
| :--- | :--- | :--- |
| **Isolation Level** *(Die Zeitachse)* | • Read Committed<br>• Repeatable Read<br>• Snapshot Isolation<br>• **Serializable** | • Distributed Snapshot Isolation<br>• **Global Serializability** |
| **Consistency Model** *(Die Raumachse)* | **Nur ACID-Integrität (Inhalt):**<br>• Unique / Foreign Keys<br>• Geschäftsregeln (z.B. Saldo >= 0) | **ACID-Integrität** *(falls ACID-DB)*<br>**+ Replikations-Garantien (Synchronität):**<br>• Linearizability, Causal Consistency, LWW, Eventual Consistency |
| **Consens & Protocols** *(Die Werkzeuge)* | *Nicht anwendbar* (Der einzelne Server entscheidet alles selbst) | • **2PC (Two-Phase-Commit)** (Atomarität)<br>• **Raft / Paxos** (Konsens-Mehrheiten)<br>• Gossip-Protokolle |

> ⚠️ **Achtung Verwechslungsgefahr:** **2PL** (Two-Phase Locking) ist ein *Isolations-Verfahren* (regelt Sperren für ACID-I). **2PC** (Two-Phase Commit) ist ein *Atomaritäts-Protokoll* (regelt das synchrone Speichern für ACID-A). Sie ersetzen sich im Netzwerk nicht, sondern arbeiten Hand in Hand.

---

## ⚡ Das Bruchstelle: "Partial Failures"

> *„Standard database techniques like two-phase locking (2PL) and multi-version concurrency control (MVCC) do not typically perform well in the event of partial failure.“*

In zentralen Systemen stürzt entweder der ganze Server ab oder gar keiner. In verteilten Systemen bricht das Netzwerk asymmetrisch weg (Teilausfall / *Partial Failure*). Wer hier blind an klassischen, starren Sperren (2PL/2PC) festhält, bringt das globale System bei kleinsten Netzwerkrucklern komplett zum Stillstand. Moderne Architekturen weichen Garantien daher entweder bewusst auf (**BASE/NoSQL**) oder nutzen quorum-basierte Konsens-Algorithmen (**NewSQL**) sowie optimistische Verfahren (**Lakehouse**).

---

## 🧪 Das 3-Stunden-Labor (Praktikum)

Das Repository enthält ein vollständiges Aufgabenblatt für Studierende, um die theoretischen Garantien in der Praxis gezielt zu testen und zu verletzen.

### 🏢 Station 1: PostgreSQL (Klassisches RDBMS)
*   **Fokus:** Transaktions-Isolation auf einer Instanz.
*   **Experiment:** Provozieren eines *Non-Repeatable Reads* unter `READ COMMITTED` über zwei parallele Terminal-Sessions. Aktivieren von `REPEATABLE READ` und Beobachten der von Postgres erzwungenen Abbruch-Fehlermeldung bei konkurrierenden Updates.

### 🌍 Station 2: MongoDB (NoSQL / BASE)
*   **Fokus:** Eventual Consistency & Schreibgarantien im Netzwerk.
*   **Experiment:** Schreiben von Dokumenten mit einer bewusst schwachen Write-Concern-Garantie (`w=0`). Sichtbarmachen von *Stale Data* (veralteten Daten) durch unmittelbar nachfolgende Lesezugriffe.

### 🚀 Station 3: CockroachDB (NewSQL)
*   **Fokus:** Resilienz bei Teilausfällen (*Partial Failures*) via Raft-Konsens.
*   **Experiment:** Starten einer globalen, strikt transaktionalen Abfrage (`SERIALIZABLE`) und hartes "Killen" eines Docker-Knotens mitten im Flug. Beobachten, wie das System dank Quorum-Mehrheit konsistent weiterarbeitet.

### 💾 Station 4: Delta Lake (Data Lakehouse / Big Data)
*   **Fokus:** ACID-Garantien auf Datebene komplett ohne Datenbank-Server.
*   **Experiment:** Paralleles Schreiben zweier Python-Pipelines auf denselben Speicherordner. Errechnen des Konflikts im JSON-Transaktionsprotokoll (`_delta_log/`) mittels *Optimistic Concurrency Control (OCC)* und Triggern einer `ConcurrentAppendException`.

---

## 🕵️‍♂️ Realwelt-Validierung: Jepsen-Tests

Die Theorie hält nicht immer, was das Marketing verspricht. Das Framework **Jepsen** (entwickelt von Kyle Kingsbury) wirft Datenbanken in eine virtuelle Hölle aus Netzwerk-Partitionen (*Split-Brain*), Server-Crashes und künstlichen Uhren-Drifts (*Clock Drifts*). 

Legendäre Funde zeigen die Relevanz dieses Themas:
*   **Redis:** Verlor bei einer Netzwerk-Partition unter LWW (Last-Write-Wins) **56 % aller erfolgreich bestätigten Schreibvorgänge**, da die asynchronen Serverstände nach der Reparatur unkoordiniert überschrieben wurden.
*   **MongoDB:** Erzeugte unter extremem Stress "retrokausale Transaktionen", bei denen Lese-Befehle Effekte aus der Zukunft sahen und damit die versprochene kausale Konsistenz verletzten.

---

## 🚀 Setup & Start

1. Repository klonen:
   ```bash
   git clone https://github.com
   cd transaktions-isolation-labor
   ```
2. Die Docker-Infrastruktur im Hintergrund starten:
   ```bash
   docker-compose up -d
   ```
3. Die Anleitungen im Ordner `/labor` öffnen und mit Station 1 beginnen.

---
*Dieses Repository wurde für Lehrzwecke im Rahmen des Moduls „Verteilte Systeme und Datenbankarchitekturen“ erstellt.*
