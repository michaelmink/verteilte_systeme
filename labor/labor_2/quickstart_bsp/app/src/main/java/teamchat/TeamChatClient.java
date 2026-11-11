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

package teamchat;

import io.grpc.Channel;
import io.grpc.Grpc;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.StatusRuntimeException;

import java.util.Iterator;
import java.util.concurrent.TimeUnit;


public class TeamChatClient {

  private final TeamChatGrpc.TeamChatBlockingStub blockingStub;

  public TeamChatClient(Channel channel) {
    blockingStub = TeamChatGrpc.newBlockingStub(channel);
  }

  // register
  public void register(String name) {
    RegMsg reg_msg = RegMsg.newBuilder().setName(name).build();
    Iterator<ServerEvent> reg_ack;

    try {
      reg_ack = blockingStub.registerClient(reg_msg);
      ServerEvent ack = reg_ack.next();
      System.out.println("User " + name + " got registered: " + ack.getRegack().getAck() + ".");
    } catch (StatusRuntimeException e) {
      System.out.println("RPC failed: {0}" + e.getStatus());
      return;
    }
  }

  // send msg
  public void send_msg(String name, String msg, Integer id) {
    ChatMsg client_message = ChatMsg.newBuilder().setName(name).setMsg(msg).setId(id).build();
    ChatMsg response;
    try {
      response = blockingStub.sendChatMsg(client_message);
    } catch (StatusRuntimeException e) {
      System.out.println("RPC failed: {0}" + e.getStatus());
      return;
    }
    System.out.println(response.getName() + ": " + response.getMsg() + " - ID: " + response.getId());
  }

  /**
   * Greet server. If provided, the first element of {@code args} is the name to use in the
   * greeting. The second argument is the target server.
   */
  public static void main(String[] args) throws Exception {
    String name = "Hans";
    String msg = "Message from myself.";
    Integer id = 1;

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
      TeamChatClient client = new TeamChatClient(channel);
      client.register(name);
      client.send_msg(name, msg, id);
      client.send_msg(name, msg, 2);
    } finally {
      // ManagedChannels use resources like threads and TCP connections. To prevent leaking these
      // resources the channel should be shut down when it will no longer be used. If it may be used
      // again leave it running.
      channel.shutdownNow().awaitTermination(5, TimeUnit.SECONDS);
    }
  }
}