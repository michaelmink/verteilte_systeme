import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Server {
    public static void main(String[] args) throws Exception {
        int port = args.length > 0 ? Integer.parseInt(args[0]) : 1099;

        // Registry im selben Prozess starten (Alternative: separates Tool `rmiregistry`).
        Registry registry = LocateRegistry.createRegistry(port);

        Calculator calc = new CalculatorImpl();
        // Stub unter einem Namen in der Registry ablegen -> Clients finden ihn darueber.
        registry.rebind("Calculator", calc);

        System.out.println("Calculator-Server laeuft, Registry auf Port " + port);
        // Kein Busy-Wait noetig: die RMI-Threads halten die JVM am Leben.
    }
}
