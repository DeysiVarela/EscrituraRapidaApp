package com.escriturarapida;

import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Scene;
import javafx.stage.Stage;

/**
 * Main application class for the Fast Writing game.
 * This class initializes the JavaFX application and loads the main game interface.
 * 
 * @author Student
 * @version 1.0
 */
public class EscrituraRapidaApp extends Application {
    
    /**
     * The main entry point for the JavaFX application.
     * 
     * @param args command line arguments
     */
    public static void main(String[] args) {
        launch(args);
    }
    
    /**
     * Initializes the application and sets up the primary stage.
     * 
     * @param primaryStage the primary stage for this application
     * @throws Exception if an error occurs during initialization
     */
    @Override
    public void start(Stage primaryStage) throws Exception {
        FXMLLoader loader = new FXMLLoader(getClass().getResource("/com/escriturarapida/game-view.fxml"));
        Scene scene = new Scene(loader.load(), 800, 600);
        
        primaryStage.setTitle("Escritura Rápida - Fast Writing Game");
        primaryStage.setScene(scene);
        primaryStage.setResizable(false);
        primaryStage.show();
    }
}
