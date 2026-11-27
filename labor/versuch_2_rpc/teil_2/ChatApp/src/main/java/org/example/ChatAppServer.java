/*
 * Copyright 2015 The gRPC Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.example;

import chat.app.*;
import com.google.protobuf.Empty;
import io.grpc.*;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.List;
import java.util.Map;


/**
 * Server that manages startup/shutdown of a {@code Greeter} server.
 */
public class ChatAppServer {
    private static final Logger logger = Logger.getLogger(ChatAppServer.class.getName());
    private Server server;

    private void start() throws IOException {
        /* The port on which the server should run */
        int port = 50051;
        /*
         * By default gRPC uses a global, shared Executor.newCachedThreadPool() for gRPC callbacks into
         * your application. This is convenient, but can cause an excessive number of threads to be
         * created if there are many RPCs. It is often better to limit the number of threads your
         * application uses for processing and let RPCs queue when the CPU is saturated.
         * The appropriate number of threads varies heavily between applications.
         * Async application code generally does not need more threads than CPU cores.
         */
        ExecutorService executor = Executors.newFixedThreadPool(10);
        server = Grpc.newServerBuilderForPort(port, InsecureServerCredentials.create())
                .executor(executor)
                .addService(new ChatAppImpl())
                .build()
                .start();
        logger.info("Server started, listening on " + port);
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                // Use stderr here since the logger may have been reset by its JVM shutdown hook.
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                try {
                    ChatAppServer.this.stop();
                } catch (InterruptedException e) {
                    if (server != null) {
                        server.shutdownNow();
                    }
                    e.printStackTrace(System.err);
                } finally {
                    executor.shutdown();
                }
                System.err.println("*** server shut down");
            }
        });
    }

    private void stop() throws InterruptedException {
        if (server != null) {
            server.shutdown().awaitTermination(30, TimeUnit.SECONDS);
        }
    }

    /**
     * Await termination on the main thread since the grpc library uses daemon threads.
     */
    private void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }

    /** create object for AllClients */
    ManageAllClients allclients = new ManageAllClients(logger);

    /**
     * Connect to History Server
     */
    public HistoryServiceGrpc.HistoryServiceStub connect_history_server() {
        System.out.println("Connecting to History Server.");

        //final HistoryServiceGrpc.HistoryServiceStub myAsyncStub;
        // Access a service running on the local machine on port 50051
        String target = "localhost:50052";
        ManagedChannel channel = Grpc.newChannelBuilder(target, InsecureChannelCredentials.create())
                .build();
        // Passing Channels to code makes code easier to test and makes it easier to reuse Channels.
        return HistoryServiceGrpc.newStub(channel);
    }
    HistoryServiceGrpc.HistoryServiceStub myAsyncStub = connect_history_server();

    /** Implements StreamObserver for sending backup messages to History Server*/
    public StreamObserver<ChatMsg> client_backup_msg () {
        class Arschklasse implements StreamObserver<Empty> {
            @Override
            public void onNext(Empty value) {
                System.out.println("Received nothing from Server.");
            }

            @Override
            public void onError(Throwable t) {
                System.out.println("Error: " + t.getMessage());
            }

            @Override
            public void onCompleted() {
                System.out.println("Backup-Stream vom HistoryServer beendet.");
            }
        }
        StreamObserver<Empty> listener = new Arschklasse();
        return myAsyncStub.backupMessage(listener);
    }
    StreamObserver<ChatMsg> backup_sender = client_backup_msg();

    /** Implements StreamObserver for requesting backup messages from History Server*/
    public void client_get_history_from_history_server(Integer n, StreamObserver<ChatMsgHistory> to_client){
        class MyRespObserver implements StreamObserver<ChatMsgHistory>{
            @Override
            public void onNext(ChatMsgHistory resp){
                System.out.println("Empfange History von History Server");
                to_client.onNext(resp);
            }
            @Override
            public void onError(Throwable t){
                System.out.println("Error: " + t.getMessage());
                to_client.onError(t);
            }
            @Override
            public void onCompleted(){
                System.out.println("Fertig.");
                to_client.onCompleted();
            }
        }
        StreamObserver<ChatMsgHistory> listener = new MyRespObserver();
        RequestHistory req = RequestHistory.newBuilder().setCount(n).build();

        myAsyncStub.requestHistory(req, listener);
    }

    /**
     * Main launches the server from the command line.
     */
    public static void main(String[] args) throws IOException, InterruptedException {
        final ChatAppServer server = new ChatAppServer();
        server.start();
        server.blockUntilShutdown();
    }

    /** send Message to all Clients */
    public void send_to_all_clients(String my_nickname, ChatMsg msg){
        for (String nickname : allclients.clients.keySet()){
            if (nickname.equals(my_nickname)){
                continue;
            }
            ManageAllClients.ClientInfo c = allclients.clients.get(nickname);
            c.observer().onNext(msg);
        }
        // send message to history server
        backup_sender.onNext(msg);
    }

    class ChatAppImpl extends ChatAppGrpc.ChatAppImplBase {
        @Override
        public void registerClient(Client req, StreamObserver<RegisterAnswer> responseObserver) {
            String nickname = req.getNickname();
            logger.info("Check, if " + nickname + " is allowed to join ...");
            RegisterAnswer answer;
            Map<Integer, String> result = allclients.check_new_client(nickname);

            if (result.containsKey(0)){
                answer = RegisterAnswer.newBuilder()
                        .setClientId(666)
                        .build();
                logger.info(nickname+ " ready to join.");
            }
            else {
                answer = RegisterAnswer.newBuilder()
                        .setErrorMsg(result.values().iterator().next())
                        .build();
                logger.info(result.values().iterator().next());
            }
            responseObserver.onNext(answer);
            responseObserver.onCompleted();
        }

        /** send list of all clients */
        @Override
        public void getAllClients(Empty req, StreamObserver<AllClients> responseObserver){
            List<String> client_list = allclients.get_available_clients();
            AllClients.Builder allclients_builder = AllClients.newBuilder();

            for (String client_nickname : client_list){
                Client c = Client.newBuilder().setNickname(client_nickname).build();
                allclients_builder.addClients(c);
            }
            responseObserver.onNext(allclients_builder.build());
            responseObserver.onCompleted();
        }

        @Override
        public StreamObserver<ChatMsg> sendMessage(StreamObserver<ChatMsg> responseObserver)
        {
            class myReqObserverClass implements StreamObserver<ChatMsg>
            {
                @Override
                public void onNext(ChatMsg received) {
                    String nickname = received.getNickname();

                    switch (received.getContentCase()){
                        case TEXT:
                            String rec_msg = received.getText();
                            logger.info(nickname + ": " + rec_msg);
                            // send to all Clients
                            ChatMsg msg = ChatMsg.newBuilder().setText(nickname + ": " + rec_msg).build();
                            send_to_all_clients(nickname, msg);
                            break;
                        case EVENT:
                            EventType event_type = received.getEvent();
                            if (event_type.equals(EventType.JOIN)){
                                logger.info("Received JOIN from " + nickname);
                                // diesen Client speichern
                                allclients.add_client(nickname, responseObserver);
                                // anderen Clients Bescheid geben
                                ChatMsg notify_msg = ChatMsg.newBuilder().setNickname(nickname)
                                        .setText(nickname + " ist beigetreten.")
                                        .build();
                                send_to_all_clients(nickname, notify_msg);
                            }
                            if (event_type.equals(EventType.LEAVE)){
                                logger.info("Received LEAVE from " + nickname);
                                String text = nickname + " has left the Chat.";
                                ChatMsg leave_msg = ChatMsg.newBuilder().setText(text).build();
                                send_to_all_clients(nickname, leave_msg);
                                // remove observer and set to offline in clientlist
                                allclients.remove_client(nickname);
                            }
                    }
                }

                @Override
                public void onError(Throwable t) {
                    logger.warning("Got Error: " + t.getMessage());
                }

                @Override
                public void onCompleted() {
                    responseObserver.onCompleted();
                }
            }
            return new myReqObserverClass();
        }

        @Override
        public void requestHistory(RequestHistory req, StreamObserver<ChatMsgHistory> responseObserver){
            // get history from history server
            client_get_history_from_history_server(100, responseObserver);
        }
    }
}