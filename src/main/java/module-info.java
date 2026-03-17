module com.example.typingspeed {
    requires javafx.controls;
    requires javafx.fxml;

    exports com.example.typingspeed;
    opens com.example.typingspeed to javafx.fxml, javafx.graphics;
}
