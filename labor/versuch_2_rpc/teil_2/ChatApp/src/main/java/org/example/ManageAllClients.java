package org.example;

import chat.app.ChatMsg;
import io.grpc.stub.StreamObserver;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;


/** Class to Manage Clients */
class ManageAllClients
{
    Logger logger;
    Integer MAX_CLIENTS = 10;
    Integer CLIENT_ID = 1;
    record ClientInfo(StreamObserver<ChatMsg> observer, String status){};
    Map<String, ClientInfo> clients = new ConcurrentHashMap<>(MAX_CLIENTS);

    // constructor
    public ManageAllClients(Logger logger) {
        this.logger = logger;
    }

    // check new client
    public Map<Integer, String> check_new_client(String nickname)
    {
        // check if client already exists
        if (clients.containsKey(nickname)){
            String msg = "User " + nickname + " already exists.";
            logger.warning(msg);
            return Map.of(-1, msg);
        }
        // check if MAX_CLIENTS is reached
        if (clients.size() >= MAX_CLIENTS){
            String msg = "User " + nickname + ": Limit reached.";
            logger.warning(msg);
            return Map.of(-1, msg);
        }
        //clients.put(nickname, new ClientInfo(null, "asking"));
        return Map.of(0, "");
    }

    // add new client
    public void add_client(String nickname, StreamObserver<ChatMsg> observer)
    {
        if (clients.containsKey(nickname)){
            logger.warning("Client " + nickname + " already exists.");
        }
        else {
            clients.put(nickname, new ClientInfo(observer, "online"));
        }
    }

    // remove client
    public void remove_client(String nickname){
        clients.remove(nickname);
    }

    // get list of available Clients
    public List<String> get_available_clients()
    {
        return new ArrayList<>(clients.keySet());
    }
}
