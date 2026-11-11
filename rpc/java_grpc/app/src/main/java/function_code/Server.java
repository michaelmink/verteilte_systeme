package function_code;

import io.grpc.ServerBuilder;

public class Server {

    public static void main(String[] args) throws Exception {
        io.grpc.Server server = ServerBuilder.forPort(50051)
                .addService(new InterfaceImpl())
                .build()
                .start();
        System.out.println("Server läuft auf Port 50051");
        server.awaitTermination();
    }
}