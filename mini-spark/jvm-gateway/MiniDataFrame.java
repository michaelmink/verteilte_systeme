import java.util.List;
import java.util.Map;

public class MiniDataFrame {
  private final Plan plan;

  MiniDataFrame(Plan plan) { this.plan = plan; }

  public MiniDataFrame filter(String op, int value) {
    // Analyse passiert sofort (wie in Spark), Ausführung erst bei einer Action
    if (!List.of(">", "<", "==").contains(op)) {
      throw new IllegalArgumentException("unknown operator: " + op);
    }
    return new MiniDataFrame(new Plan.Filter(plan, op, value));
  }

  public MiniDataFrame multiply(int factor) {
    return new MiniDataFrame(new Plan.Multiply(plan, factor));
  }

  public String explain() {
    return "== Logical Plan ==\n" + plan.tree("")
        + "\n== Physical Plan ==\n" + Engine.physicalPlan(plan);
  }

  public List<Integer> collect() throws Exception {
    return Engine.collect(plan);
  }

  public int count() throws Exception {
    return collect().size();
  }

  public Map<Integer, Integer> countByMod(int mod) throws Exception {
    return Engine.countByKey(plan, mod);
  }
}