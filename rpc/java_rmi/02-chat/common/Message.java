package common;

import java.io.Serializable;
import java.time.LocalTime;


public class Message implements Serializable {
    private static final long serialVersionUID = 1L;

    String from;
    String text;
    LocalTime time;

    public Message(String from, String text) {
        this.from = from;
        this.text = text;
        this.time = LocalTime.now();
    }
}