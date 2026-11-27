package org.example;

import chat.app.*;
import com.google.protobuf.Empty;
import io.grpc.Channel;
import io.grpc.Grpc;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.stub.StreamObserver;

import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.Scanner;



/**
 * A simple client that requests a greeting from the {@link ChatAppServer}.
 */
public class ChatAppClient {

    private final ChatAppGrpc.ChatAppBlockingStub blockingStub;
    private final ChatAppGrpc.ChatAppStub myAsyncStub;
    static Scanner scanner = new Scanner(System.in);

    /** Construct client for accessing HelloWorld server using the existing channel. */
    public ChatAppClient(Channel channel) {
        // 'channel' here is a Channel, not a ManagedChannel, so it is not this code's responsibility to
        // shut it down.

        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        blockingStub = ChatAppGrpc.newBlockingStub(channel);
        myAsyncStub = ChatAppGrpc.newStub(channel);
    }

    static class myRespObserverClass implements StreamObserver<ChatMsg>
    {
        @Override
        public void onNext(ChatMsg rec){
            System.out.println(rec.getText());
        }

        @Override
        public void onError(Throwable t){
            System.out.println("Got Error: " + t.getMessage());
        }

        @Override
        public void onCompleted(){
            System.out.println("Fertig.");
        }
    }

    /** Say hello to server. */
    static String ask_for_nickname() {
        System.out.println("Enter your nickname ...");
        return scanner.nextLine();
    }

    /** Register the new Client. */
    boolean register_client(String nickname) {
        System.out.println(nickname + ", will try to log you in ...");

        Client client_req = Client.newBuilder().setNickname(nickname).setZahl(300).build();
        RegisterAnswer answer = blockingStub.registerClient(client_req);
        switch (answer.getResultCase()) {
            case CLIENT_ID:
                int id = answer.getClientId();
                System.out.println(nickname + " successfully registered.");
                return true;
            case ERROR_MSG:
                String msg = answer.getErrorMsg();
                System.out.println(nickname + " could not be registered: " + msg);
                return false;
        }
        return false;
    }

    /** Send a Message to Server. */
    void send_message_in_chat(String nickname) throws InterruptedException {
        StreamObserver<ChatMsg> myRespObserver = new myRespObserverClass();
        StreamObserver<ChatMsg> myReqObserver = myAsyncStub.sendMessage(myRespObserver);

        // send a JOIN to allow server to handle observer object
        ChatMsg join_msg = ChatMsg.newBuilder().setNickname(nickname).setEvent(EventType.JOIN).build();
        myReqObserver.onNext(join_msg);
        // request chat history from server
        RequestHistory req = RequestHistory.newBuilder().build();
        ChatMsgHistory chat_history = blockingStub.requestHistory(req);
        System.out.println("Loading Chat History ...");
        for (ChatMsg msg : chat_history.getChatHistoryList()){
            System.out.println(msg.getText());
        }

        while (true){
            String input = scanner.nextLine();
            ChatMsg msg;

            if (input.equals("!Exit")){
                // send Msg to say GoodBye
                ChatMsg leave_msg = ChatMsg.newBuilder()
                        .setNickname(nickname)
                        .setEvent(EventType.LEAVE)
                        .build();
                // send to Server
                myReqObserver.onNext(leave_msg);
                break;
            }
            if (input.equals("list")){
                Empty empty = Empty.newBuilder().build();
                AllClients all_clients = blockingStub.getAllClients(empty);
                System.out.println("Available Nicknames in the Chat:");
                for (Client c : all_clients.getClientsList()){
                    System.out.println(" - " + c.getNickname());
                }
                continue;
            }

            msg = ChatMsg.newBuilder().setText(input).setNickname(nickname).build();
            // send to Server
            myReqObserver.onNext(msg);
        }
        myReqObserver.onCompleted();
    }

    /**
     * Chat App server.
     */
    public static void main(String[] args) throws Exception {

        // Access a service running on the local machine on port 50051
        String target = "localhost:50051";

        // Create a communication channel to the server, known as a Channel. Channels are thread-safe
        // and reusable. It is common to create channels at the beginning of your application and reuse
        // them until the application shuts down.
        //
        // For the example we use plaintext insecure credentials to avoid needing TLS certificates. To
        // use TLS, use TlsChannelCredentials instead.
        ManagedChannel channel = Grpc.newChannelBuilder(target, InsecureChannelCredentials.create())
                .build();
        try {
            ChatAppClient client = new ChatAppClient(channel);

            System.out.println(" ==================== ");
            System.out.println("Welcome to the Chat.");
            System.out.println(" ==================== ");

            String nickname;
            while (true) {
                // Ask User for his nickname
                nickname = ask_for_nickname();

                // register new client
                if (client.register_client(nickname)){
                    break;
                }
            }

            // send a message to server
            client.send_message_in_chat(nickname);

        } finally {
            // ManagedChannels use resources like threads and TCP connections. To prevent leaking these
            // resources the channel should be shut down when it will no longer be used. If it may be used
            // again leave it running.
            channel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
        }
    }
}