import java.rmi.Remote;
import java.rmi.RemoteException;

// Remote-Interface: der "Vertrag" zwischen Client und Server.
// Jede Methode muss RemoteException deklarieren, da Netzwerkfehler auftreten koennen.
public interface Calculator extends Remote {
    int add(int a, int b) throws RemoteException;

    int subtract(int a, int b) throws RemoteException;

    double divide(double a, double b) throws RemoteException;

    // Rueckgabe eines Serializable-Objekts: wird per Wert (Kopie) uebertragen.
    Result compute(String op, double a, double b) throws RemoteException;
}
