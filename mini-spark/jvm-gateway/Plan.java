import java.util.ArrayList;
import java.util.List;
import java.util.stream.IntStream;

interface Plan {
  String tree(String indent);

  record Range(int start, int end) implements Plan {
    public String tree(String indent) {
      return indent + "Range(" + start + ", " + end + ")\n";
    }
  }

  record Filter(Plan child, String op, int value) implements Plan {
    public String tree(String indent) {
      return indent + "Filter(x " + op + " " + value + ")\n" + child.tree(indent + "  ");
    }
  }

  record Multiply(Plan child, int factor) implements Plan {
    public String tree(String indent) {
      return indent + "Project(x * " + factor + ")\n" + child.tree(indent + "  ");
    }
  }
}