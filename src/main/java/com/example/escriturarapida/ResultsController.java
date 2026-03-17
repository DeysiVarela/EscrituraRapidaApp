package com.example.escriturarapida;

import javafx.fxml.FXML;
import javafx.scene.control.ListView;
import javafx.stage.Stage;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;

public class ResultsController {
    @FXML private ListView<String> resultsList;

    @FXML
    public void initialize() {
        try {
            Path p = Path.of("results.json");
            if (Files.exists(p)) {
                List<String> lines = Files.readAllLines(p).stream().collect(Collectors.toList());
                resultsList.getItems().addAll(lines);
            }
        } catch (IOException e) {
            resultsList.getItems().add("No se pudo leer results.json");
        }
    }

    @FXML
    protected void onCloseClicked() {
        Stage s = (Stage) resultsList.getScene().getWindow();
        s.close();
    }
}
