package com.benchmark;

import javafx.application.Application;
import javafx.concurrent.Task;
import javafx.fxml.FXMLLoader;
import javafx.geometry.Pos;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.control.ProgressBar;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;

public class App extends Application {

    private Process pythonServerProcess;
    private Stage primaryStage;

    @Override
    public void start(Stage stage) {
        this.primaryStage = stage;

        // 1. Setup Loading Screen
        VBox loadingRoot = new VBox(20);
        loadingRoot.setAlignment(Pos.CENTER);
        Label statusLabel = new Label("Initializing...");
        ProgressBar progressBar = new ProgressBar(0);
        progressBar.setPrefWidth(300);
        loadingRoot.getChildren().addAll(statusLabel, progressBar);

        Scene loadingScene = new Scene(loadingRoot, 400, 200);
        stage.setTitle("LLM Benchmark Launcher");
        stage.setScene(loadingScene);
        stage.show();

        // 2. Run Setup Task
        Task<Void> setupTask = new Task<>() {
            @Override
            protected Void call() throws Exception {
                DependencyManager.ensureEnvironmentReady((msg, progress) -> {
                    updateMessage(msg);
                    updateProgress(progress, 1.0);
                });

                updateMessage("Starting Backend Server...");
                pythonServerProcess = DependencyManager.startBackendServer();

                Thread.sleep(2000);

                return null;
            }
        };

        statusLabel.textProperty().bind(setupTask.messageProperty());
        progressBar.progressProperty().bind(setupTask.progressProperty());

        // 3. On Success: Load Main UI
        setupTask.setOnSucceeded(e -> launchMainInterface());

        // 4. On Fail: Show Error
        setupTask.setOnFailed(e -> {
            statusLabel.textProperty().unbind();
            statusLabel.setText("Error: " + setupTask.getException().getMessage());
            setupTask.getException().printStackTrace();
        });

        new Thread(setupTask).start();
    }

    private void launchMainInterface() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("benchmark.fxml")); // Your existing FXML
            Parent root = loader.load();
            Scene scene = new Scene(root, 1000, 700);
            scene.getStylesheets().add(getClass().getResource("styles.css").toExternalForm());

            primaryStage.setTitle("LLM Benchmark Tool");
            primaryStage.setScene(scene);
            primaryStage.centerOnScreen();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void stop() {
        // Cleanup: Kill python server when Java app closes
        if (pythonServerProcess != null && pythonServerProcess.isAlive()) {
            System.out.println("Stopping Python backend...");
            pythonServerProcess.destroy(); // or destroyForcibly()

        }
    }

    public static void main(String[] args) {
        launch(args);
    }
}