package server;

import common.Message;
import common.ChatClient;
import common.ChatServer;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ChatServerImpl extends UnicastRemoteObject implements ChatServer {

    // Aufrufe kommen parallel aus mehreren RMI-Threads.
    private final Map<String, ChatClient> clients = new ConcurrentHashMap<>();

    protected ChatServerImpl() throws RemoteException {
        super();
    }

    @Override
    public boolean register(String name, ChatClient client) {
        if (clients.putIfAbsent(name, client) != null) {
            System.out.println("Name bereits vergeben: " + name);
            return false;
        }
        System.out.println(name + " ist beigetreten (" + clients.size() + " online)");
        broadcast(new Message("Server", name + " ist beigetreten"));
        return true;
    }

    @Override
    public void unregister(String name) {
        if (clients.remove(name) != null) {
            System.out.println(name + " hat den Chat verlassen");
            broadcast(new Message("Server", name + " hat den Chat verlassen"));
        }
    }

    @Override
    public void send(String from, String text) {
        Message msg = new Message(from, text);
        System.out.println(msg);
        broadcast(msg);
    }

    private void broadcast(Message msg) {
        clients.forEach((name, client) -> {
            try {
                client.receive(msg);
            } catch (RemoteException e) {
                System.out.println(name + " nicht erreichbar, wird entfernt");
                clients.remove(name);
            }
        });
    }
}