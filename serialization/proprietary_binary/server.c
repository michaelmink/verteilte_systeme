#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

int main() {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in address = { .sin_family = AF_INET, .sin_port = htons(8080), .sin_addr.s_addr = INADDR_ANY };

    bind(server_fd, (struct sockaddr *)&address, sizeof(address));
    listen(server_fd, 1);
    printf("Server wartet auf Verbindung auf Port 8080...\n");

    int client_fd = accept(server_fd, NULL, NULL);
    printf("Client verbunden!\n");

    // --- UNSER BINÄRPROTOKOLL LESEN ---
    
    // Schritt 1: Befehls-ID lesen (1 Byte)
    uint8_t command_id = 0;
    read(client_fd, &command_id, 1);

    // Schritt 2: Länge lesen (2 Bytes) und von Network- in Host-Byte-Order umwandeln
    uint16_t payload_len_net = 0;
    read(client_fd, &payload_len_net, 2);
    uint16_t payload_len = ntohs(payload_len_net);

    // Schritt 3: Den eigentlichen Text lesen (exakt payload_len Bytes)
    char *buffer = malloc(payload_len + 1); // +1 für die Nullterminierung in C
    read(client_fd, buffer, payload_len);
    buffer[payload_len] = '\0'; // String sauber beenden

    // Auswertung
    printf("\n--- Paket empfangen ---\n");
    printf("Befehls-ID:  %d\n", command_id);
    printf("Textlänge:   %d Bytes\n", payload_len);
    printf("Inhalt:      %s\n", buffer);

    // Aufräumen
    free(buffer);
    close(client_fd);
    close(server_fd);
    return 0;
}
