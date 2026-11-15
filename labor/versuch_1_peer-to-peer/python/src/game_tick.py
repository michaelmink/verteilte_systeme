



async def game_tick(sock):
    """
    game tick
    """
    loop = asyncio.get_running_loop()
    while(True):
        # recvfrom
        msg, addr = await loop.sock_recvfrom(sock, 1000)
        peer_msg = json.loads(msg.decode("utf-8"))

        if peer_msg.get("collision"):
            snakes.pop(addr, None)
            peers.pop(addr, None)
            status = f"{peer_msg['nickname']} ist ausgeschieden"
            continue

        snakes[addr] = peer_msg

        # check if received addr is known
        if addr not in peers:
            #print(f"received msg from {addr} --> unkonwn peer")
            # add new peer
            peers[addr] = {
                "nickname": peer_msg["nickname"],
                "farbe": peer_msg["farbe"],
                "last_seen": time.time()
            }
            # check nickname and color
            # TODO

        # update last_seen
        peers[addr]["last_seen"] = time.time()

        #print(f"received msg from {addr} - known peers: {[p for p in peers.keys()]}")

        # kick out peer if last_seen is older than 3s 
        now = time.time()
        for peer in list(peers):
            if (now - peers[peer]["last_seen"]) > 3:
                snakes.pop(peer, None)
                peers.pop(peer, None)
                #print(f"no activity since 3s from {peer} --> removed.")
