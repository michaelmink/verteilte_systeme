package java_rmi;

import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;

public class Client {
    public static void main(String[] args) throws Exception {
        Registry registry = LocateRegistry.getRegistry("localhost", 1099);

        // list available remote objects
        String[] names = registry.list();
        for (String name : names) {
            System.out.println(name);
        }
        
        InterfaceDef service = (InterfaceDef) registry.lookup("HalloService");

        InterfaceDef service2 = (InterfaceDef) registry.lookup("Hallo2");

        service.say_hello();
        service2.say_hello();

        System.out.println("--> " + service.add(3.3, 4.0));
        System.out.println("--> " + service2.add(3.1, 4.0));
    }
}
