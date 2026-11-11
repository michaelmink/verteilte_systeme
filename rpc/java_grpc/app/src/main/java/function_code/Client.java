package function_code;

import com.google.protobuf.Empty;

import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import java_grpc.proto.AddInput;
import java_grpc.proto.MyServicesGrpc;

public class Client {

    public static void main(String[] args) {
        ManagedChannel channel = ManagedChannelBuilder.forAddress("localhost", 50051)
                .usePlaintext()
                .build();

        MyServicesGrpc.MyServicesBlockingStub stub = MyServicesGrpc.newBlockingStub(channel);
        
        stub.sayHello(Empty.getDefaultInstance());

        AddInput tmp = AddInput.newBuilder().setA(3.3).setB(2.0).build();
        System.out.println(stub.add(tmp));

        channel.shutdown();
    }
}