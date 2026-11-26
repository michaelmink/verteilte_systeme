# PreLab

## 1.
Skizzieren Sie, beginnend mit einem gRPC-proto-File, welche Teile der gRPC-ClientServer-Architektur aus dem proto generiert werden (gestrichelt) und welche selbst entwickelt werden müssen (nicht gestrichelt). Hinweis: Folie aus Vorlesung. 

![Alternativtext](skizze_1.png.png)



## 2.
Definieren Sie über ProtoBuf v3 eine Schnittstelle für ein Serverobjekt, welches eine
Mitgliederliste verwaltet (Listenelemente: Mitgl.-Nr., Name, Telefonnnummer.
Operationen: Mitglied dazunehmen, Mitglied entfernen, Gesamte Liste abfragen) .
(Hinweis: Wenn Sie keinen Parameter oder Returnwerte haben, müssen Sie dafür eine
Empty-Message anlegen; es gibt hierfür google.protobuf.Empty)

```protobuf

syntax = "proto3";

package mitglieder;

import "google/protobuf/empty.proto";

message Mitglied {
    int32 mitglied_nr = 1;
    string name = 2;
    string telefon = 3;
}

message MitgliedNr {
    int32 mitglied_nr = 1;
}

message Mitgliederliste {
    repeated Mitglied mitglieder = 1;
}

service MitgliederService {
    rpc AddMitglied (Mitglied) returns (google.protobuf.Empty);
    rpc RemoveMitglied (MitgliedNr) returns (google.protobuf.Empty);
    rpc GetMitglieder (google.protobuf.Empty) returns (Mitgliederliste);
}
```


## 3.
Schauen Sie sich im Internet das gRPC-Proto-File
https://github.com/grpc/grpc/blob/v1.35.0/examples/protos/route_guide.proto an.
Machen Sie sich schlau, was die Anwendung macht. Weitere Erläuterungen zur
Anwendung finden Sie unter https://grpc.io/docs/languages/java/basics/.
Vervollständigen Sie unten auf dieser Seite den rpc-Typ, beschreiben Sie knapp,
wofür jede der 4 Methoden dient und wofür das Streaming jeweils gebraucht wird. 

Route Guide ist ein Kartendienst: Ein Client kann Orte (Features, also benannte Punkte wie Sehenswürdigkeiten) an einer Position oder in einem Gebiet abfragen, eine gefahrene Route aufzeichnen und auswerten lassen, und unterwegs Notizen mit anderen austauschen.

```
1. rpc GetFeature (Point) returns (Feature) {}

 Was macht es?
 Methode ist Unary. Zurück kommt ein Feature mit Name und Position. Gibt es an dem Punkt nichts, ist der Name leer.
```

```
2. rpc ListFeatures (Rectangle) returns (stream Feature) {}

 Was macht es?
 Innerhalb der gegebenen Bounding Box können mehrere Feature messages zurückgebeben werden. 
 Wofür genau wird Streaming gebraucht?
 Es wird gestreamt, weil das Rechteck ein großes Gebiet mit sehr vielen Features abdecken kann. Statt einer riesigen Antwort mit einem repeated-Feld schickt der Server die Features einzeln, sobald er sie findet. Der Client kann die ersten sofort verarbeiten bzw. anzeigen, und keine Seite muss die ganze Liste im Speicher halten.
```

```
3. rpc RecordRoute(stream Point) returns (RouteSummary) {}
 Was macht es?
 Basierend auf einem Stream von mehreren Punkten wird am Ende eine RouteSummary zurückgegeben.
 Wofür genau wird Streaming gebraucht?
 Der Client schickt die Punkte der Route nach und nach, während er sie abfährt. Wie viele es werden, steht vorher nicht fest. Am Ende antwortet der Server mit einer RouteSummary: Anzahl der Punkte, Anzahl der passierten Features, zurückgelegte Strecke in Metern und Dauer in Sekunden. Streaming ist nötig, weil die Daten über die Zeit entstehen und es vorher keine fertige Liste gibt.
```

```
4. rpc RouteChat (stream RouteNote) returns (stream RouteNote) {}
 Was macht es?
Das ist ein bidirektionales Streaming RPC und es werden asynchron Nachrichten ausgetauscht bei bestimmten Punkten.
 Wofür genau wird Streaming gebraucht?
 Eine RouteNote besteht aus Position und Textnachricht. Der Client schickt unterwegs Notizen, und gleichzeitig bekommt er Notizen von anderen Nutzern zu denselben Orten. Im Beispielserver sind das alle Notizen, die früher an dieser Position geschrieben wurden. Beide Richtungen laufen unabhängig voneinander, und die Anzahl der Nachrichten ist vorher in keiner Richtung bekannt.
 ```
