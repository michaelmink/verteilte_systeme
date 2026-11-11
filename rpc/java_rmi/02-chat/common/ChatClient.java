package common;

import java.rmi.Remote;
import java.rmi.RemoteException;

// Wird vom Client implementiert; der Server ruft es als Callback auf.
public interface ChatClient extends Remote {
    void receive(Message msg) throws RemoteException;
}
