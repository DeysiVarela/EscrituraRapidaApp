package com.example.escriturarapida;

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

    @FXML
    public void initialize() {
        inputField.setOnAction(e -> onSubmitClicked());
        // accessibility hints
        inputField.setAccessibleText("Campo de entrada para escribir la palabra");
        statusLabel.setAccessibleText("Estado del juego");
    }

    @FXML
    protected void onStartClicked() {
        resetGame();
        startTimer();
        nextWord();
        statusLabel.setText("Juego iniciado");
        inputField.requestFocus();
    }

    @FXML
    protected void onSubmitClicked() {
        String text = inputField.getText().trim();
        if (text.isEmpty() || currentWord.isEmpty()) return;
        if (text.equalsIgnoreCase(currentWord)) {
            score++;
            scoreLabel.setText(String.valueOf(score));
            statusLabel.setText("Correcto!");
        } else {
            statusLabel.setText("Incorrecto. Era: " + currentWord);
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
        statusLabel.setText("Tiempo! Puntaje: " + score);
        saveResult();
    }

    @FXML
    protected void onShowHistoryClicked() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/com/example/escriturarapida/results-view.fxml"));
            Parent root = loader.load();
            Stage stage = new Stage();
            stage.initModality(Modality.APPLICATION_MODAL);
            stage.setTitle("Historial de partidas");
            stage.setScene(new Scene(root));
            stage.showAndWait();
        } catch (IOException e) {
            statusLabel.setText("No se pudo abrir historial");
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

    private void saveResult() {
        try {
            Path out = Path.of("results.json");
            String line = String.format("{\"time\":\"%s\",\"score\":%d}%n", Instant.now().toString(), score);
            Files.writeString(out, line, java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
            statusLabel.setText(statusLabel.getText() + " (guardado)");
        } catch (IOException e) {
            statusLabel.setText(statusLabel.getText() + " (error al guardar)");
        }
    }
}
