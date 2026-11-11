package function_code;

import io.grpc.stub.StreamObserver;
import java_grpc.proto.MyServicesGrpc;
import java_grpc.proto.AddInput;
import java_grpc.proto.AddOutput;
import com.google.protobuf.Empty;


public class InterfaceImpl extends MyServicesGrpc.MyServicesImplBase {
    
    @Override
    public void sayHello(Empty request, StreamObserver<Empty> responseObserver) {
        System.out.println("Hallo");
        responseObserver.onNext(request);
        responseObserver.onCompleted();
    }

    @Override 
    public void add(AddInput request, StreamObserver<AddOutput> responseObserver) {
        
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        System.out.println("add auf Thread: " + Thread.currentThread().getName());

        double summe = request.getA() + request.getB();
        AddOutput reply = AddOutput.newBuilder().setC(summe).build();
        responseObserver.onNext(reply);
        responseObserver.onCompleted();
    }


}
