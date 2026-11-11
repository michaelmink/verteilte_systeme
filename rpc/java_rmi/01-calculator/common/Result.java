import java.io.Serializable;

// Kein Remote-Objekt: wird serialisiert und als Kopie zum Client geschickt.
public class Result implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String expression;
    private final double value;
    private final String computedBy;

    public Result(String expression, double value, String computedBy) {
        this.expression = expression;
        this.value = value;
        this.computedBy = computedBy;
    }

    @Override
    public String toString() {
        return expression + " = " + value + " (berechnet von " + computedBy + ")";
    }
}
