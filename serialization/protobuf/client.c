#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include "format.pb-c.h"

static int send_all(int fd, const void *buf, size_t len) {
    const uint8_t *p = buf;
    while (len > 0) {
        ssize_t n = send(fd, p, len, 0);
        if (n <= 0) return -1;
        p += n;
        len -= n;
    }
    return 0;
}

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in serv_addr = { .sin_family = AF_INET, .sin_port = htons(8080) };
    inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr);

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("Verbindung fehlgeschlagen!\n");
        return 1;
    }

    Message msg = MESSAGE__INIT;
    msg.cmd = 2;
    msg.text = "Hallo aus dem rohen Socket!";

    size_t len = message__get_packed_size(&msg);
    uint8_t packet[2 + len];
    uint16_t len_net = htons(len);
    memcpy(packet, &len_net, 2);
    message__pack(&msg, &packet[2]);

    printf("Protobuf-Payload: %zu Bytes, gesamt: %zu Bytes\n", len, sizeof(packet));
    for (size_t i = 0; i < sizeof(packet); i++) printf("%02x ", packet[i]);
    printf("\n");

    if (send_all(sock, packet, sizeof(packet)) < 0) {
        perror("send");
        return 1;
    }

    close(sock);
    return 0;
}