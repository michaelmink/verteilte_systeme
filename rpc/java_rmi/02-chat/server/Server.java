package server;

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Server {
    public static void main(String[] args) throws Exception {
        int port = args.length > 0 ? Integer.parseInt(args[0]) : 1099;

        Registry registry = LocateRegistry.createRegistry(port);
        registry.rebind("Chat", new ChatServerImpl());

        System.out.println("Chat-Server laeuft, Registry auf Port " + port);
    }
}