import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Client {
    public static void main(String[] args) throws Exception {
        String host = args.length > 0 ? args[0] : "localhost";
        int port = args.length > 1 ? Integer.parseInt(args[1]) : 1099;

        System.out.println("Passed Arguments:");
        System.out.println("host:" + host);
        System.out.println("port:" + port);

        Registry registry = LocateRegistry.getRegistry(host, port);
        // Liefert einen Stub (Proxy). Aufrufe darauf gehen uebers Netz zum Server.
        Calculator calc = (Calculator) registry.lookup("Calculator");
        System.out.println("Stub-Klasse: " + calc.getClass().getName());

        System.out.println("3 + 4 = " + calc.add(3, 4));
        System.out.println("10 - 7 = " + calc.subtract(10, 7));
        System.out.println("7 / 2 = " + calc.divide(7, 2));

        Result r = calc.compute("*", 6, 7);
        System.out.println(r);

        try {
            calc.divide(1, 0);
        } catch (ArithmeticException e) {
            System.out.println("Server-Exception beim Client angekommen: " + e.getMessage());
        }
    }
}
