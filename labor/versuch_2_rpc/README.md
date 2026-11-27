# grpc in Java

## Unary: Client kein Stream, Server kein Stream

### proto
```protobuf
rpc Register_Client (ReqMsg) returns (RespMsg);
```

### Client
```java
class MyRespObserver implements StreamObserver<RespMsg> {
    @Override
    public void onNext(RespMsg resp) {
        // Empfange die RespMsg und mache was ...
        System.out.println("Empfangen: " + resp.getText());
    }
    @Override
    public void onError(Throwable t) {
        System.out.println("Error: " + t.getMessage());
    }
    @Override
    public void onCompleted() {
        // Server hat den Aufruf beendet
        System.out.println("Fertig.");
    }
}
// eigene StreamObserver Implementierung instanziieren und dem asynchronen Stub zusammen mit einer reqMsg übergeben.
StreamObserver<RespMsg> respObserver = new MyRespObserver();
myAsyncStub.registerClient(reqMsg, respObserver);
```
oder
```java
// Blocking Aufruf
RespMsg resp = blockingStub.registerClient(reqMsg);
```

### Server
```java
class ServiceImpl extends ServiceGrpc.ServiceImplBase {
    @Override
    public void registerClient(ReqMsg req, StreamObserver<RespMsg> responseObserver){
        System.out.println("Empfangene Message: " + req.getText());
        // Antwort Message bauen
        RespMsg resp = RespMsg.newBuilder().setText("Hallo").build();
        responseObserver.onNext(resp);
        // RPC Aufruf beenden
        responseObserver.onCompleted();
    }
}
```

## Client streamt, Server kein Stream (Client-Streaming)

### proto
```protobuf
rpc Register_Client (stream ReqMsg) returns (RespMsg);
```

### Client
```java
// 1. Observer für die spätere Antwort bauen.
class MyRespObserver implements StreamObserver<RespMsg> {
    @Override
    public void onNext(RespMsg resp) {
        // Empfangene Nachricht vom Server
        System.out.println("Empfangen: " + resp.getText());
    }
    @Override
    public void onError(Throwable t) {
        System.out.println("Error: " + t.getMessage());
    }
    @Override
    public void onCompleted() {
        // Server hat den Aufruf beendet
        System.out.println("Fertig.");
    }
}
// 2. Methode aufrufen -> wir erhalten den ReqObserver zum Senden.
StreamObserver<RespMsg> observer = new MyRespObserver();
StreamObserver<ReqMsg> reqObserver = myAsyncStub.registerClient(observer);

// 3. Mehrere Nachrichten schicken und am Ende abschließen
reqObserver.onNext(req1);
reqObserver.onNext(req2);
reqObserver.onNext(req3);
reqObserver.onCompleted();
```

### Server
```java
class ServiceImpl extends ServiceGrpc.ServiceImplBase {
    @Override
    public StreamObserver<ReqMsg> registerClient(StreamObserver<RespMsg> responseObserver) {
        // 1. Eigenen Observer bauen, der auf die eingehenden Nachrichten reagiert.
        class MyReqObserver implements StreamObserver<ReqMsg> {
            @Override
            public void onNext(ReqMsg req) {
                // wird für jede Nachricht des Clients einmal aufgerufen
                System.out.println("Empfangen: " + req.getText());
            }

            @Override
            public void onError(Throwable t) {
                System.out.println("Error: " + t.getMessage());
            }

            @Override
            public void onCompleted() {
                // 2. Erst wenn der Client fertig ist, die EINE Antwort zurückschicken
                RespMsg resp = RespMsg.newBuilder().setText("Fertig.").build();
                responseObserver.onNext(resp);
                responseObserver.onCompleted();
            }
        }
        // 3. Observer an gRPC zurückgeben -> gRPC ruft ihn bei jeder Client-Nachricht auf
        return new MyReqObserver();
    }
}
```

## Client kein Stream, Server streamt (Server-Streaming)

### proto
```protobuf
rpc Register_Client (ReqMsg) returns (stream RespMsg);
```

### Client
```java
// 1. Observer empfängt jetzt mehrere Antworten nacheinander
class MyRespObserver implements StreamObserver<RespMsg> {
    @Override
    public void onNext(RespMsg resp) {
        // Empfange jede einzelne RespMsg und mache was ...
        System.out.println("Empfangen: " + resp.getText());
    }
    @Override
    public void onError(Throwable t) {
        System.out.println("Error: " + t.getMessage());
    }
    @Override
    public void onCompleted() {
        // Server hat den Stream beendet (keine weiteren onNext mehr)
        System.out.println("Fertig.");
    }
}
// 2. Methode aufrufen -> gRPC ruft onNext für jede Antwort des Servers auf
StreamObserver<RespMsg> respObserver = new MyRespObserver();
myAsyncStub.registerClient(reqMsg, respObserver);   // kehrt sofort zurück
```
oder
```java
// Blocking Aufruf: Iterator über alle Antworten
Iterator<RespMsg> antworten = blockingStub.registerClient(reqMsg);
while (antworten.hasNext()) {
    RespMsg resp = antworten.next();   // wartet jeweils auf die nächste Nachricht
    System.out.println("Empfangen: " + resp.getText());
}
// Schleife endet, wenn der Server onCompleted() aufruft
```

### Server
```java
class ServiceImpl extends ServiceGrpc.ServiceImplBase {
    @Override
    public void registerClient(ReqMsg req, StreamObserver<RespMsg> responseObserver) {
        // 1. Mehrere Antworten nacheinander schicken
        responseObserver.onNext(resp1);
        responseObserver.onNext(resp2);
        responseObserver.onNext(resp3);
        // 2. Am Ende Stream schließen
        responseObserver.onCompleted();
    }
}
```


## Client streamt, Server streamt (bidirektionales Streaming)

### proto
```protobuf
rpc Register_Client (stream ReqMsg) returns (stream RespMsg);
```

### Client
```java
// 1. Observer für die Antworten des Servers
class MyRespObserver implements StreamObserver<RespMsg> {
    @Override
    public void onNext(RespMsg resp) {
        // Empfangene Nachricht vom Server
        System.out.println("Empfangen: " + resp.getText());
    }
    @Override
    public void onError(Throwable t) {
        System.out.println("Error: " + t.getMessage());
    }
    @Override
    public void onCompleted() {
        // Server hat seinen Stream beendet
        System.out.println("Fertig.");
    }
}
// 2. Methode aufrufen -> wir erhalten den ReqObserver zum Senden.
StreamObserver<RespMsg> observer = new MyRespObserver();
StreamObserver<ReqMsg> reqObserver = myAsyncStub.registerClient(observer);

// 3. Mehrere Nachrichten schicken und am Ende abschließen
reqObserver.onNext(req1);
reqObserver.onNext(req2);
reqObserver.onNext(req3);
reqObserver.onCompleted();
```

### Server
```java
class ServiceImpl extends ServiceGrpc.ServiceImplBase {
    @Override
    public StreamObserver<ReqMsg> registerClient(StreamObserver<RespMsg> responseObserver) {
        // 1. Eigenen Observer bauen, der auf die eingehenden Nachrichten reagiert.
        class MyReqObserver implements StreamObserver<ReqMsg> {
            @Override
            public void onNext(ReqMsg req) {
                // direkt während der Stream läuft Antworten zurückschicken
                RespMsg resp = RespMsg.newBuilder().setText("Echo").build();
                responseObserver.onNext(resp);
            }

            @Override
            public void onError(Throwable t) {
                System.out.println("Error: " + t.getMessage());
            }

            @Override
            public void onCompleted() {
                // 2. Wenn Client schliesst, schliesst Server auch
                responseObserver.onCompleted();
            }
        }
        // 3. Observer an gRPC zurückgeben -> gRPC ruft ihn bei jeder Client-Nachricht auf
        return new MyReqObserver();
    }
}
```


## Anhang

### A. Channel und Stubs erzeugen
```java
// Channel = Verbindung zum Server, wird für alle Aufrufe wiederverwendet
ManagedChannel channel = Grpc.newChannelBuilder("localhost:50051", InsecureChannelCredentials.create())
        .build();

ServiceGrpc.ServiceStub myAsyncStub = ServiceGrpc.newStub(channel);                  // asynchron
ServiceGrpc.ServiceBlockingStub blockingStub = ServiceGrpc.newBlockingStub(channel); // blockierend

// ... Aufrufe ...

// am Programmende Channel schließen
channel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
```

### B. Server starten
```java
Server server = Grpc.newServerBuilderForPort(50051, InsecureServerCredentials.create())
        .addService(new ServiceImpl())
        .build()
        .start();
server.awaitTermination();   // main-Thread blockieren, gRPC nutzt Daemon-Threads
```

### C. Wann gibt es welchen Stub?

| Variante | Async-Stub | Blocking-Stub |
|---|---|---|
| Unary | ✅ | ✅ gibt `RespMsg` zurück |
| Client-Streaming | ✅ | ❌ |
| Server-Streaming | ✅ | ✅ gibt `Iterator<RespMsg>` zurück |
| Bidirektional | ✅ | ❌ |

Fehler kommen beim Blocking-Stub nicht über `onError`, sondern als Exception:
```java
try {
    RespMsg resp = blockingStub.registerClient(reqMsg);
} catch (StatusRuntimeException e) {
    System.out.println("Error: " + e.getStatus());
}
```

### D. Asynchron heißt: kehrt sofort zurück
Ein Aufruf über den Async-Stub wartet nicht auf die Antwort. Die Antwort kommt später, in einem anderen Thread, über `onNext`.
Endet das Programm vorher oder wird der Channel geschlossen, kommt die Antwort nie an.
Wenn man im Hauptprogramm auf die Antwort warten muss, geht das z. B. mit einem `CountDownLatch`:

```java
class MyRespObserver implements StreamObserver<RespMsg> {
    RespMsg antwort;
    CountDownLatch fertig = new CountDownLatch(1);

    @Override
    public void onNext(RespMsg resp) { antwort = resp; }

    @Override
    public void onError(Throwable t) { fertig.countDown(); }   // auch im Fehlerfall freigeben

    @Override
    public void onCompleted() { fertig.countDown(); }
}

MyRespObserver respObserver = new MyRespObserver();
myAsyncStub.registerClient(reqMsg, respObserver);   // kehrt sofort zurück
respObserver.fertig.await();                        // warten auf onCompleted/onError
// nach onError ist respObserver.antwort null -> vorher prüfen
```

### E. Regeln für StreamObserver
- Jeder Aufruf wird **genau einmal** beendet: entweder `onCompleted()` oder `onError(...)`, nie beides.
- Nach `onCompleted()` / `onError(...)` darf kein `onNext(...)` mehr kommen (sonst `IllegalStateException`).
- `onCompleted()` beendet nur **diesen RPC-Aufruf**, nicht den Channel bzw. die TCP-Verbindung.
- Fehler auf dem Server mit `Status` melden:
  ```java
  responseObserver.onError(Status.INVALID_ARGUMENT.withDescription("Text fehlt").asRuntimeException());
  ```
- Ein `StreamObserver` ist **nicht thread-sicher**: Rufen mehrere Threads `onNext` auf demselben Observer auf (z. B. Chat-Server, der an alle Clients verteilt), muss man synchronisieren:
  ```java
  synchronized (observer) {
      observer.onNext(msg);
  }
  ```

### F. Namen aus der proto-Datei
- Aus dem RPC `Register_Client` wird in Java die Methode `registerClient` (camelCase).
- Aus `service Service` werden `ServiceGrpc`, `ServiceGrpc.ServiceImplBase`, `ServiceGrpc.ServiceStub` und `ServiceGrpc.ServiceBlockingStub`.
- In einem Service darf jeder RPC-Name nur einmal vorkommen. Die vier Varianten oben sind getrennte Beispiele.

### G. Imports
```java
import io.grpc.*;                       // Grpc, ManagedChannel, Server, Status, StatusRuntimeException, ...
import io.grpc.stub.StreamObserver;
import java.util.Iterator;              // Server-Streaming mit Blocking-Stub
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
```
