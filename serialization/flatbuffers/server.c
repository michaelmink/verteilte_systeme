#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include "format_reader.h"
#include "format_verifier.h"

static int recv_all(int fd, void *buf, size_t len) {
    uint8_t *p = buf;
    while (len > 0) {
        ssize_t n = recv(fd, p, len, 0);
        if (n <= 0) return -1;
        p += n;
        len -= n;
    }
    return 0;
}

int main() {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    struct sockaddr_in address = { .sin_family = AF_INET, .sin_port = htons(8080), .sin_addr.s_addr = INADDR_ANY };

    bind(server_fd, (struct sockaddr *)&address, sizeof(address));
    listen(server_fd, 1);
    printf("Server wartet auf Verbindung auf Port 8080...\n");

    int client_fd = accept(server_fd, NULL, NULL);

    uint16_t len_net;
    if (recv_all(client_fd, &len_net, 2) < 0) return 1;
    uint16_t len = ntohs(len_net);

    // Eigener malloc-Puffer, da FlatBuffers ausgerichtete Daten erwartet
    uint8_t *buf = malloc(len);
    if (recv_all(client_fd, buf, len) < 0) return 1;

    int ret = Message_verify_as_root(buf, len);
    if (ret != flatcc_verify_ok) {
        fprintf(stderr, "Ungültiger FlatBuffer: %s\n", flatcc_verify_error_string(ret));
        return 1;
    }

    Message_table_t msg = Message_as_root(buf);
    uint8_t cmd = Message_cmd(msg);
    flatbuffers_string_t text = Message_text(msg);

    printf("\n--- Paket empfangen ---\n");
    printf("Befehls-ID:  %u\n", cmd);
    printf("Textlänge:   %zu Bytes\n", flatbuffers_string_len(text));
    printf("Inhalt:      %s\n", text);

    free(buf);
    close(client_fd);
    close(server_fd);
    return 0;
}