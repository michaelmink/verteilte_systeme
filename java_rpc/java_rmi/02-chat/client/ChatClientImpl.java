package client;

import common.ChatClient;
import common.Message;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

public class ChatClientImpl extends UnicastRemoteObject implements ChatClient {

    protected ChatClientImpl() throws RemoteException {
        super();
    }

    // Laeuft im RMI-Thread des Clients, ausgeloest vom Server.
    @Override
    public void receive(Message msg) {
        System.out.println(msg);
    }
}