#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in serv_addr = { .sin_family = AF_INET, .sin_port = htons(8080) };

    inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr);

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("Verbindung fehlgeschlagen!\n");
        return 1;
    }

    // --- UNSER BINÄRPROTOKOLL ERSTELLEN ---
    char *message = "Hallo aus dem rohen Socket!";
    uint8_t cmd = 2; // Unser Befehl für "Textnachricht"
    uint16_t len = strlen(message);
    uint16_t len_net = htons(len); // Konvertierung in Network Byte Order

    // Buffer vorbereiten (1 Byte Cmd + 2 Bytes Länge + Nachricht)
    char packet[1 + 2 + len];
    
    // Bytes manuell zusammensetzen
    packet[0] = cmd;                             // Byte 0
    memcpy(&packet[1], &len_net, 2);             // Byte 1-2
    memcpy(&packet[3], message, len);            // Ab Byte 3

    // Das gesamte Paket auf einmal senden
    send(sock, packet, sizeof(packet), 0);
    printf("Paket gesendet!\n");

    close(sock);
    return 0;
}
