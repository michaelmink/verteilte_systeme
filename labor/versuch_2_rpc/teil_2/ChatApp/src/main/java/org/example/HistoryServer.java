package org.example;

import chat.app.*;
import com.google.protobuf.Empty;
import io.grpc.Grpc;
import io.grpc.InsecureServerCredentials;
import io.grpc.Server;
import io.grpc.stub.StreamObserver;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;


public class HistoryServer {
    private static final Logger logger = Logger.getLogger(HistoryServer.class.getName());
    private Server server;

    private void start() throws IOException {
        /* The port on which the server should run */
        int port = 50052;
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
                .addService(new HistoryServiceImpl())
                .build()
                .start();
        logger.info("Server started, listening on " + port);
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                // Use stderr here since the logger may have been reset by its JVM shutdown hook.
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                try {
                    HistoryServer.this.stop();
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

    /**
     * Main launches the server from the command line.
     */
    public static void main(String[] args) throws IOException, InterruptedException {
        final HistoryServer server = new HistoryServer();
        server.start();
        server.blockUntilShutdown();
    }


    /**
     * Helper Class to Store Chat History
     */
    static class HistoryStorage {
        List<ChatMsg> storage = new ArrayList<>(1000);

        // constructor
        void HistoryStorage() {
            System.out.println("Create History Storage.");
        }

        // add chat msg
        synchronized void add_msg(ChatMsg msg) {
            storage.add(msg);
        }

        // return last n messages
        synchronized List<ChatMsg> return_history(Integer n) {
            Integer len = storage.size();
            return storage.subList(Math.max(0, len - n), len);
        }
    }
    HistoryStorage history_storage = new HistoryStorage();

    class HistoryServiceImpl extends HistoryServiceGrpc.HistoryServiceImplBase {

        @Override
        public StreamObserver<ChatMsg> backupMessage(StreamObserver<Empty> responseObserver) {
            class myReqObserverClass implements StreamObserver<ChatMsg> {
                @Override
                public void onNext(ChatMsg req) {
                    System.out.println("[History Server]: " + req.getText());
                    history_storage.add_msg(req);
                }

                @Override
                public void onError(Throwable t) {
                    System.out.println("Error: " + t.getMessage());
                }

                @Override
                public void onCompleted() {
                    responseObserver.onCompleted();
                }
            }
            return new myReqObserverClass();
        }

        @Override
        public void requestHistory(RequestHistory req, StreamObserver<ChatMsgHistory> history_to_client) {
            Integer n = req.getCount();
            List<ChatMsg> history_msgs = history_storage.return_history(n);
            ChatMsgHistory.Builder msg_builder = ChatMsgHistory.newBuilder();

            for (ChatMsg history_msg : history_msgs) {
                msg_builder.addChatHistory(history_msg);
            }
            history_to_client.onNext(msg_builder.build());
            history_to_client.onCompleted();
        }
    }
}