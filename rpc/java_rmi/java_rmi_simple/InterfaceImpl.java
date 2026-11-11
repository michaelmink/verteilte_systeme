package java_rmi;

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

public class InterfaceImpl extends UnicastRemoteObject implements InterfaceDef {

    public InterfaceImpl() throws RemoteException {}

    @Override
    public void say_hello() throws RemoteException {
        // print somehting
        System.out.println("Hallo.");
    }

    @Override
    public double add(double a, double b) throws RemoteException {
        return a+b;
    }
}

class Test2 extends UnicastRemoteObject implements InterfaceDef {
    public Test2() throws RemoteException {}

    @Override
    public void say_hello() throws RemoteException {
        System.out.println("Nochmal Hallo.");
    }

    @Override
    public double add(double a, double b) throws RemoteException {
        return a+b;
    }
}
