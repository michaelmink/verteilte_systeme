import py4j.GatewayServer;

public class MiniSpark {
  public MiniDataFrame range(int start, int end) {
    return new MiniDataFrame(new Plan.Range(start, end));
  }

  public static void main(String[] args) {
    new GatewayServer(new MiniSpark()).start();
    System.out.println("MiniSpark gateway listening on 25333");
  }
}