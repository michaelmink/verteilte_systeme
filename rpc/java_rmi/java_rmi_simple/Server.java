package java_rmi;

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Server {
    public static void main(String[] args) throws Exception {
        Registry registry = LocateRegistry.createRegistry(1099);
        registry.rebind("HalloService", new InterfaceImpl());
        registry.rebind("Hallo2", new Test2());

        System.out.println("Server läuft auf Port 1099.");
    }
}
