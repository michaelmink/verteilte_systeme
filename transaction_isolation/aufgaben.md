# 📝 Aufgabenblatt: Laborübung Transaktions-Isolation & Verteilte Konsistenz

* **Dauer:** 3 Stunden (180 Minuten)
* **Format:** Zweiergruppen (Pair Programming)
* **Abgabeziel:** Erstellung eines gemeinsamen Protokolls (`LABOR_PROTOKOLL.md`)

---

## 🏢 Station 1: Die Zeitachse – Isolation in PostgreSQL (45 Min)

**Szenario:** Ein Ticketshop verkauft die letzten Plätze für ein Konzert. Es ist nur noch genau 1 Ticket da. Zwei Fans klicken zeitgleich auf „Kaufen“.

### Arbeitsauftrag:
1. Öffnet zwei separate Terminal-Fenster (Terminal A und Terminal B) und verbindet euch jeweils mit PostgreSQL:  
   ```bash
   docker exec -it db-labor-postgres-1 psql -U postgres
   ```
2. Bereitet die Tabelle vor (führt dies nur in **Terminal A** aus):
   ```sql
   CREATE TABLE tickets (id INT, anzahl INT);
   INSERT INTO tickets VALUES (1, 1);
   ```
3. Startet in **beiden** Fenstern eine Transaktion mit der Stufe `READ COMMITTED`:
   ```sql
   BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED;
   ```
4. Führt die SQL-Befehle nun exakt in dieser **zeitlichen Reihenfolge** abwechselnd aus:
   * **Terminal A:** `SELECT anzahl FROM tickets WHERE id = 1;` *(Ergebnis: 1)*
   * **Terminal B:** `UPDATE tickets SET anzahl = 0 WHERE id = 1;`
   * **Terminal B:** `COMMIT;`
   * **Terminal A:** `SELECT anzahl FROM tickets WHERE id = 1;` *(Zweites Lesen!)*
5. Notiert eure Beobachtung des Kontostands in Terminal A beim zweiten Lesen. Beendet die Transaktion in Terminal A mit `COMMIT;`.
6. **Wiederholung mit Garantie:** Setzt den Wert zurück auf 1 (`UPDATE tickets SET anzahl = 1 WHERE id = 1;`). Wiederholt das Experiment von vorne (Schritte 3–4), nutzt für beide Transaktionen jedoch:
   ```sql
   BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;
   ```
7. Versucht nun im letzten Schritt in Terminal A ebenfalls ein Update abzusetzen (`UPDATE tickets SET anzahl = 0 WHERE id = 1;`), nachdem Terminal B bereits committet hat.

❓ **Laborfrage 1.1:** Welches transaktionale Phänomen (Anomalie) konntet ihr im `READ COMMITTED` Modus beobachten?  
❓ **Laborfrage 1.2:** Welche Fehlermeldung wirft PostgreSQL im `REPEATABLE READ` Modus aus, wenn ihr versucht, die Zeile parallel zu beschreiben? Was bedeutet das für das Design einer Anwendungssoftware (Stichwort: Retry-Logik)?

---

## 🌍 Station 2: Die Raumachse – Verteilte Welten & MongoDB (45 Min)

**Szenario:** Ein soziales Netzwerk spiegelt Daten asynchron auf Replikate weltweit. Wir erzwingen das *BASE-Prinzip* (Eventual Consistency), um maximale Performance zu demonstrieren.

### Arbeitsauftrag:
1. Installiert auf eurem Rechner das Python-Paket für MongoDB:  
   ```bash
   pip install pymongo
   ```
2. Erstellt eine Python-Datei namens `nosql_test.py` mit folgendem Inhalt. Wir nutzen hierbei bewusst das schwächste Schreibverhalten (`w=0`), bei dem MongoDB den Erfolg meldet, noch bevor die Daten physisch verarbeitet oder repliziert wurden:
   ```python
   import time
   from pymongo import MongoClient

   client = MongoClient("mongodb://localhost:27017/")
   db = client["labor_demo"]
   # Aktivierung der schwächsten Stufe (w=0, unacknowledged)
   collection = db.get_collection("posts", write_concern={"w": 0})

   # Bereinigung
   collection.delete_many({})

   print("Starte asynchronen Schreib-/Lese-Zyklus...")
   for i in range(1, 6):
       doc_id = i
       # 1. Schneller Schreibvorgang
       collection.insert_one({"_id": doc_id, "status": "aktiv", "payload": "X" * 1000})
       
       # 2. Sofortiger, ungedrosselter Leseversuch
       result = collection.find_one({"_id": doc_id})
       
       if result is None:
           print(f"💥 Anomalie bei Durchlauf {i}: Dokument {doc_id} wurde geschrieben, ist aber beim direkten Lesen noch unsichtbar (Stale Data)!")
       else:
           print(f"✅ Durchlauf {i}: Dokument {doc_id} gefunden.")
   ```
3. Führt das Skript aus: `python nosql_test.py`. (Falls euer Rechner zu schnell ist und alle Versuche klappen, erhöht den String `"X" * 1000` auf `"X" * 100000`, um eine künstliche Netzwerklast zu erzeugen).

❓ **Laborfrage 2.1:** Warum kann es bei `w=0` in asynchronen Systemen überhaupt passieren, dass Daten direkt nach dem Schreiben unauffindbar sind?  
❓ **Laborfrage 2.2:** Welches Kernversprechen des BASE-Modells und welcher Trade-off des CAP-Theorems werden hier in der Praxis sichtbar?

---

## 🚀 Station 3: Die NewSQL-Krone – CockroachDB & Teilausfälle (45 Min)

**Szenario:** Ein hochverfügbares Bankensystem muss absolut ausfallsicher sein. Wir simulieren eine Transaktion während eines harten Knotenausfalls (*Partial Failure*).

### Arbeitsauftrag:
1. Verbindet euch mit der SQL-Konsole der laufenden CockroachDB:  
   ```bash
   docker exec -it db-labor-cockroachdb-1 ./cockroach sql --insecure
   ```
2. Erstellt eine Tabelle und startet eine Transaktion. CockroachDB akzeptiert hierbei keine schwachen Stufen und erzwingt im Hintergrund automatisch immer das stärkste Level (`SERIALIZABLE`):
   ```sql
   CREATE TABLE konten (id INT PRIMARY KEY, saldo INT);
   INSERT INTO konten VALUES (1, 500);
   
   BEGIN;
   SELECT * FROM konten WHERE id = 1;
   ```
3. **Der Teilausfall (*Partial Failure*):** Lasst die SQL-Konsole offen! Öffnet ein zweites, normales Terminal auf eurem Host-System und simuliert den plötzlichen Crash dieses Datenbank-Knotens:  
   ```bash
   docker stop db-labor-cockroachdb-1
   ```
4. Wechselt sofort zurück in euer offenes SQL-Terminal aus Schritt 2 und versucht, die Transaktion mit folgendem Befehl abzuschließen:
   ```sql
   COMMIT;
   ```

❓ **Laborfrage 3.1:** Wie reagiert das SQL-Terminal beim Versuch zu committen?  
❓ **Laborfrage 3.2:** Angenommen, wir hätten ein echtes 3-Knoten-Cluster betrieben (anstatt eines Single-Nodes) und nur einer wäre gecrasht: Wie unterscheidet sich das Fehlertoleranz-Verhalten einer NewSQL-Datenbank (mittels Raft/Paxos-Konsens) fundamental von klassischen 2PC-Protokollen (Two-Phase-Commit) bei einem Teilausfall? Warum blockiert 2PC das gesamte System?

---

## 💾 Station 4: Das moderne Lakehouse – Delta Lake (45 Min)

**Szenario:** Ein Data-Engineering-Cluster verarbeitet große Datenmengen direkt auf einem Cloud-Objektspeicher (z. B. S3). Es gibt keinen aktiven Datenbank-Server; die Sicherheit muss rein auf Dateiebene erzwungen werden.

### Arbeitsauftrag:
1. Installiert die Python-Bibliothek für Delta Lake (basiert auf einer performanten Rust-Engine, benötigt kein Java/Spark):  
   ```bash
   pip install deltalake pandas
   ```
2. Erstellt ein Python-Skript namens `pipeline_write.py`. Dieses simuliert eine Pipeline, die Daten einliest, verarbeitet und versucht, diese optimistisch an einen Speicherort anzuhängen. Um den Konflikt zu erzwingen, lassen wir das Skript nach dem Start absichtlich 5 Sekunden schlafen, bevor es den Schreibvorgang abschließt:
   ```python
   import time
   import pandas as pd
   from deltalake import write_deltalake

   print("Pipeline gestartet. Bereite Daten vor...")
   df = pd.DataFrame({"id":, "status": ["aktiv"]})

   print("Simuliere komplexe Berechnung (5 Sekunden Wartezeit)...")
   time.sleep(5)

   print("Versuche, Daten atomar in das Lakehouse zu schreiben...")
   # Schreibt Daten optimistisch in einen lokalen Ordner
   write_deltalake("./lakehouse_db", df, mode="append")
   print("🎉 Schreibvorgang erfolgreich abgeschlossen!")
   ```
3. Erstellt ein zweites Skript namens `pipeline_fast.py`, das *sofort* ohne Wartezeit schreibt:
   ```python
   import pandas as pd
   from deltalake import write_deltalake

   df = pd.DataFrame({"id":, "status": ["blitzschnell"]})
   write_deltalake("./lakehouse_db", df, mode="append")
   print("⚡ Schnelle Pipeline hat erfolgreich vorab geschrieben!")
   ```
4. **Das Experiment:** 
   * Startet zuerst die langsame Pipeline: `python pipeline_write.py`
   * Öffnet *sofort* ein anderes Terminal und startet die schnelle Pipeline: `python pipeline_fast.py`
   * Wartet, bis die langsame Pipeline ihre 5 Sekunden abgesessen hat und versucht zu speichern.

❓ **Laborfrage 4.1:** Welche genaue Python-/Delta-Exception wird von der langsamen Pipeline geworfen?  
❓ **Laborfrage 4.2:** Werft einen Blick in das Verzeichnis `./lakehouse_db/_delta_log/`. Welche Dateien wurden dort angelegt? Erklärt kurz, wie Delta Lake hier echte ACID-Transaktionen ohne jeglichen Datenbank-Server oder Zeilensperren (Locks) erzwingt (Stichwort: *Optimistic Concurrency Control*).
