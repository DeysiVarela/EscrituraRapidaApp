package com.example.typingspeed;

import javafx.animation.FadeTransition;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.control.ListView;
import javafx.scene.control.TextField;
import javafx.stage.Modality;
import javafx.stage.Stage;
import javafx.util.Duration;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.Timer;
import java.util.TimerTask;

public class HelloController {
    @FXML private Label timeLabel;
    @FXML private Label scoreLabel;
    @FXML private Label wordLabel;
    @FXML private TextField inputField;
    @FXML private Label statusLabel;

    private Timer timer;
    private int timeLeft = 60;
    private int score = 0;
    private List<String> words = Arrays.asList("java","maven","fx","hola","rapido","teclado","programa","codigo","ejemplo","prueba");
    private Random rnd = new Random();
    private String currentWord = "";
    private FadeTransition ft;

    /** Initialize controller: wire events and accessibility. */
    @FXML
    public void initialize() {
        inputField.setOnAction(e -> onSubmitClicked());
        // keyboard shortcut: Ctrl+R to restart
        inputField.getScene();
        // accessibility hints (in English)
        inputField.setAccessibleText("Input field to type the shown word");
        statusLabel.setAccessibleText("Game status");
        // mouse hover for wordLabel
        wordLabel.setOnMouseEntered(e -> wordLabel.setStyle("-fx-opacity:0.9; -fx-cursor:hand;"));
        wordLabel.setOnMouseExited(e -> wordLabel.setStyle("-fx-opacity:1.0;"));
    }

    /** Start or restart the game. */
    @FXML
    protected void onStartClicked() {
        resetGame();
        startTimer();
        nextWord();
        statusLabel.setText("Game started");
        inputField.requestFocus();
    }

    /** Submit the current input and update score. */
    @FXML
    protected void onSubmitClicked() {
        String text = inputField.getText().trim();
        if (text.isEmpty() || currentWord.isEmpty()) return;
        if (text.equalsIgnoreCase(currentWord)) {
            score++;
            scoreLabel.setText(String.valueOf(score));
            statusLabel.setText("Correct!");
        } else {
            statusLabel.setText("Wrong. Was: " + currentWord);
        }
        inputField.clear();
        nextWord();
    }

    private void nextWord() {
        currentWord = words.get(rnd.nextInt(words.size()));
        wordLabel.setText(currentWord);
        // simple fade animation for the word card
        if (ft != null) ft.stop();
        ft = new FadeTransition(Duration.millis(350), wordLabel);
        ft.setFromValue(0.4);
        ft.setToValue(1.0);
        ft.playFromStart();
    }

    private void startTimer() {
        timer = new Timer(true);
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                timeLeft--;
                Platform.runLater(() -> timeLabel.setText(String.valueOf(timeLeft)));
                if (timeLeft <= 0) {
                    timer.cancel();
                    Platform.runLater(() -> endGame());
                }
            }
        }, 1000, 1000);
    }

    private void endGame() {
        inputField.setDisable(true);
        statusLabel.setText("Time! Score: " + score);
        // use persistence service
        PersistenceService.getInstance().save(new GameResult(Instant.now(), score));
    }

    @FXML
    protected void onShowHistoryClicked() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/com/example/escriturarapida/results-view.fxml"));
            Parent root = loader.load();
            Stage stage = new Stage();
            stage.initModality(Modality.APPLICATION_MODAL);
            stage.setTitle("Game history");
            stage.setScene(new Scene(root));
            stage.showAndWait();
        } catch (IOException e) {
            statusLabel.setText("Could not open history");
        }
    }

    private void resetGame() {
        if (timer != null) timer.cancel();
        timeLeft = 60;
        score = 0;
        scoreLabel.setText("0");
        timeLabel.setText(String.valueOf(timeLeft));
        inputField.setDisable(false);
        statusLabel.setText("");
    }

    @Deprecated
    private void saveResult() {
        // kept for compatibility but now uses PersistenceService
        PersistenceService.getInstance().save(new GameResult(Instant.now(), score));
    }
}
