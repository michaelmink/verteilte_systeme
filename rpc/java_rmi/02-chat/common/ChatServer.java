package common;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface ChatServer extends Remote {
    boolean register(String name, ChatClient client) throws RemoteException;

    void unregister(String name) throws RemoteException;

    void send(String from, String text) throws RemoteException;
}
