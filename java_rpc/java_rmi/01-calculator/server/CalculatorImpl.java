import java.rmi.RemoteException;
import java.rmi.server.RemoteServer;
import java.rmi.server.ServerNotActiveException;
import java.rmi.server.UnicastRemoteObject;

// Implementierung des Remote-Interfaces. Laeuft nur auf dem Server.
// UnicastRemoteObject exportiert das Objekt automatisch (oeffnet einen Port, erzeugt Stub).
public class CalculatorImpl extends UnicastRemoteObject implements Calculator {

    protected CalculatorImpl() throws RemoteException {
        super();
    }

    @Override
    public int add(int a, int b) {
        log("add(" + a + ", " + b + ")");
        return a + b;
    }

    @Override
    public int subtract(int a, int b) {
        log("subtract(" + a + ", " + b + ")");
        return a - b;
    }

    @Override
    public double divide(double a, double b) {
        log("divide(" + a + ", " + b + ")");
        if (b == 0) {
            // Exceptions werden serialisiert und beim Client erneut geworfen.
            throw new ArithmeticException("Division durch 0");
        }
        return a / b;
    }

    @Override
    public Result compute(String op, double a, double b) {
        log("compute(" + op + ", " + a + ", " + b + ")");
        double value = switch (op) {
            case "+" -> a + b;
            case "-" -> a - b;
            case "*" -> a * b;
            case "/" -> a / b;
            default -> throw new IllegalArgumentException("Unbekannter Operator: " + op);
        };
        return new Result(a + " " + op + " " + b, value, Thread.currentThread().getName());
    }

    private void log(String call) {
        String client;
        try {
            client = RemoteServer.getClientHost();
        } catch (ServerNotActiveException e) {
            client = "lokal";
        }
        // Jeder Remote-Aufruf laeuft in einem eigenen RMI-Thread -> Implementierung muss thread-safe sein.
        System.out.printf("[%s] %s von %s%n", Thread.currentThread().getName(), call, client);
    }
}
