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
import io.grpc.Grpc;
import io.grpc.InsecureServerCredentials;
import io.grpc.Server;
import io.grpc.stub.StreamObserver;
import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;


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

    /** Class to Manage Clients */
    class ManageAllClients
    {
        Integer MAX_CLIENTS = 10;
        Integer CLIENT_ID = 1;
        record ClientInfo(StreamObserver<ChatMsg> observer, String status){};
        Map<String, ClientInfo> clients = new ConcurrentHashMap<>(MAX_CLIENTS);

        // add new client
        public Map<Integer, String> register_client(String nickname)
        {
            // check if client already exists
            if (clients.containsKey(nickname)){
                String msg = "User " + nickname + " already exists.";
                logger.warning(msg);
                return Map.of(-1, msg);
            }
            // check if MAX_CLIENTS is reached
            if (clients.size() >= MAX_CLIENTS){
                String msg = "User " + nickname + ": Limit reached.";
                logger.warning(msg);
                return Map.of(-1, msg);
            }
            clients.put(nickname, new ClientInfo(null, "asking"));
            return Map.of(0, "");
        }

        // remove client
        public void remove_client(String nickname){
            clients.remove(nickname);
        }

        // add observer
        public void add_observer(String nickname, StreamObserver<ChatMsg> observer)
        {
            if (clients.containsKey(nickname)){
                clients.put(nickname, new ClientInfo(observer, "online"));
            }
        }

        // remove observer
        public void remove_observer(String nickname)
        {
            if (clients.containsKey(nickname)){
                clients.put(nickname, new ClientInfo(null, "offline"));
            }
        }

        // get list of available Clients
        public List<String> get_available_clients()
        {
            return new ArrayList<>(clients.keySet());
        }
    }

    // create object for AllClients
    ManageAllClients allclients = new ManageAllClients();


    /**
     * Main launches the server from the command line.
     */
    public static void main(String[] args) throws IOException, InterruptedException {
        final ChatAppServer server = new ChatAppServer();
        server.start();
        server.blockUntilShutdown();
    }

    /** send Message to all Clients */
    public void send_to_all_clients(ChatMsg msg){
        for (String nickname : allclients.clients.keySet()){
            ManageAllClients.ClientInfo c = allclients.clients.get(nickname);
            c.observer().onNext(msg);
        }
    }

    class ChatAppImpl extends ChatAppGrpc.ChatAppImplBase {
        @Override
        public void registerClient(Client req, StreamObserver<RegisterAnswer> responseObserver) {
            String nickname = req.getNickname();
            logger.info("Will try to register nickname " + nickname);
            RegisterAnswer answer;
            Map<Integer, String> result = allclients.register_client(nickname);

            if (result.containsKey(0)){
                answer = RegisterAnswer.newBuilder()
                        .setClientId(666)
                        .build();
                logger.info(nickname+ " successfully registered.");
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
                    // observer für diesen Client speichern
                    allclients.add_observer(nickname, responseObserver);

                    switch (received.getContentCase()){
                        case TEXT:
                            String rec_msg = received.getText();
                            logger.info(nickname + ": " + rec_msg);
                            // send to all Clients
                            ChatMsg msg = ChatMsg.newBuilder().setText(nickname + ": " + rec_msg).build();
                            send_to_all_clients(msg);
                            break;
                        case EVENT:
                            EventType event_type = received.getEvent();
                            if (event_type.equals(EventType.LEAVE)){
                                logger.info("Received LEAVE from " + nickname);
                                String text = nickname + " has left the Chat.";
                                ChatMsg leave_msg = ChatMsg.newBuilder().setText(text).build();
                                send_to_all_clients(leave_msg);
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
    }
}