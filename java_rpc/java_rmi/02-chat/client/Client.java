package client;

import common.ChatServer;

import java.rmi.registry.LocateRegistry;
import java.rmi.server.UnicastRemoteObject;
import java.util.Scanner;

public class Client {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.out.println("Usage: java Client <name> [host] [port]");
            return;
        }
        String name = args[0];
        String host = args.length > 1 ? args[1] : "localhost";
        int port = args.length > 2 ? Integer.parseInt(args[2]) : 1099;

        ChatServer server = (ChatServer) LocateRegistry.getRegistry(host, port).lookup("Chat");

        ChatClientImpl me = new ChatClientImpl();
        if (!server.register(name, me)) {
            System.out.println("Name '" + name + "' ist schon vergeben.");
            UnicastRemoteObject.unexportObject(me, true);
            return;
        }

        System.out.println("Verbunden als " + name + ". '/quit' zum Beenden.");
        try (Scanner in = new Scanner(System.in)) {
            while (in.hasNextLine()) {
                String line = in.nextLine().trim();
                if (line.equals("/quit")) {
                    break;
                }
                if (!line.isEmpty()) {
                    server.send(name, line);
                }
            }
        }

        server.unregister(name);
        // Sonst haelt der exportierte Callback die JVM am Leben.
        UnicastRemoteObject.unexportObject(me, true);
    }
}