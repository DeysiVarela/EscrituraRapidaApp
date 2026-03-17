package com.example.typingspeed;

import javafx.fxml.FXML;
import javafx.scene.control.ListView;
import javafx.stage.Stage;

import java.util.List;

/**
 * Controller for the results/history dialog.
 */
public class ResultsController {
    @FXML private ListView<String> resultsList;

    @FXML
    public void initialize() {
        List<String> lines = PersistenceService.getInstance().readAll();
        resultsList.getItems().addAll(lines);
    }

    @FXML
    protected void onCloseClicked() {
        Stage s = (Stage) resultsList.getScene().getWindow();
        s.close();
    }
}
