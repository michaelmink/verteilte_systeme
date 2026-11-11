package java_rmi;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface InterfaceDef extends Remote {
    public void say_hello() throws RemoteException;
    public double add(double a, double b) throws RemoteException;
}
