import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

final class Engine {
  static final int NUM_PARTITIONS = 4;
  static final int NUM_REDUCERS = 2;
  private static final ExecutorService EXECUTORS = Executors.newFixedThreadPool(4);

  // physischer Plan: eine Quelle + Pipeline von Operationen, die pro Zeile hintereinander laufen
  record Stage(Plan.Range source, List<Plan> ops) {
    @Override
    public String toString() {
      StringBuilder sb = new StringBuilder("Scan " + source.tree("").strip()
          + " in " + NUM_PARTITIONS + " partitions");
      for (Plan op : ops) sb.append("\n  -> ").append(op.tree("").lines().findFirst().orElse(""));
      return sb.toString();
    }
  }

  static Stage physicalPlan(Plan p) {
    List<Plan> ops = new ArrayList<>();
    while (!(p instanceof Plan.Range)) {
      ops.add(0, p);
      if (p instanceof Plan.Filter f) p = f.child();
      else if (p instanceof Plan.Multiply m) p = m.child();
      else throw new IllegalStateException("unknown node " + p);
    }
    return new Stage((Plan.Range) p, ops);
  }

  static int[] partition(Plan.Range r, int p) {
    int size = Math.max(0, r.end() - r.start());
    return new int[] {
        r.start() + size * p / NUM_PARTITIONS,
        r.start() + size * (p + 1) / NUM_PARTITIONS };
  }

  static List<Integer> runTask(Stage stage, int partition, int from, int to) {
    System.out.printf("[%s] map task %d: rows %d..%d%n",
        Thread.currentThread().getName(), partition, from, to - 1);
    List<Integer> out = new ArrayList<>();
    for (int x = from; x < to; x++) {
      int v = x;
      boolean kept = true;
      for (Plan op : stage.ops()) {
        if (op instanceof Plan.Filter f) {
          if (!keep(f, v)) { kept = false; break; }
        } else if (op instanceof Plan.Multiply m) {
          v *= m.factor();
        }
      }
      if (kept) out.add(v);
    }
    return out;
  }

  private static boolean keep(Plan.Filter f, int x) {
    return switch (f.op()) {
      case ">" -> x > f.value();
      case "<" -> x < f.value();
      default -> x == f.value();
    };
  }

  // nur Map-Phase, kein Shuffle nötig
  static List<Integer> collect(Plan logical) throws Exception {
    Stage stage = physicalPlan(logical);
    List<Future<List<Integer>>> tasks = new ArrayList<>();
    for (int p = 0; p < NUM_PARTITIONS; p++) {
      int[] range = partition(stage.source(), p);
      int id = p;
      tasks.add(EXECUTORS.submit(() -> runTask(stage, id, range[0], range[1])));
    }
    List<Integer> result = new ArrayList<>();
    for (Future<List<Integer>> t : tasks) result.addAll(t.get());
    return result;
  }

  static Map<Integer, Integer> countByKey(Plan logical, int mod) throws Exception {
    Stage stage = physicalPlan(logical);

    // Map-Phase: pro Partition vorzählen (Combiner) und nach Reducer in Buckets aufteilen
    List<Future<List<Map<Integer, Integer>>>> mapTasks = new ArrayList<>();
    for (int p = 0; p < NUM_PARTITIONS; p++) {
      int[] range = partition(stage.source(), p);
      int id = p;
      mapTasks.add(EXECUTORS.submit(() -> {
        List<Map<Integer, Integer>> buckets = new ArrayList<>();
        for (int r = 0; r < NUM_REDUCERS; r++) buckets.add(new HashMap<>());
        for (int x : runTask(stage, id, range[0], range[1])) {
          int key = x % mod;
          buckets.get(key % NUM_REDUCERS).merge(key, 1, Integer::sum);
        }
        return buckets;
      }));
    }
    List<List<Map<Integer, Integer>>> mapOutputs = new ArrayList<>();
    for (var t : mapTasks) mapOutputs.add(t.get());

    // Shuffle + Reduce: Reducer r holt Bucket r von jedem Map-Task
    List<Future<Map<Integer, Integer>>> reduceTasks = new ArrayList<>();
    for (int r = 0; r < NUM_REDUCERS; r++) {
      int id = r;
      reduceTasks.add(EXECUTORS.submit(() -> {
        Map<Integer, Integer> sums = new HashMap<>();
        for (var out : mapOutputs) out.get(id).forEach((k, v) -> sums.merge(k, v, Integer::sum));
        System.out.printf("[%s] reduce task %d: %s%n", Thread.currentThread().getName(), id, sums);
        return sums;
      }));
    }
    Map<Integer, Integer> result = new TreeMap<>();
    for (var t : reduceTasks) result.putAll(t.get());
    return result;
  }
}