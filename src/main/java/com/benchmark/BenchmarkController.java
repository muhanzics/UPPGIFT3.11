package com.benchmark;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.concurrent.Task;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.scene.control.*;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.Region;
import javafx.stage.DirectoryChooser;
import javafx.stage.FileChooser;
import javafx.stage.Stage;

import java.io.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

public class BenchmarkController {

    // FXML Components
    @FXML private TextField testSuitePathField;
    @FXML private Button browseTestSuiteButton;
    @FXML private TextField exportPathField;
    @FXML private Button browseExportButton;
    @FXML private ListView<String> downloadedModelsList;
    @FXML private ListView<String> availableModelsList;
    @FXML private Button refreshModelsButton;
    @FXML private Button runBenchmarkButton;
    @FXML private ProgressBar progressBar;
    @FXML private Label statusLabel;
    @FXML private Slider temperatureSlider;
    @FXML private Label temperatureValueLabel;

    // Observable Lists
    private final ObservableList<String> downloadedModels = FXCollections.observableArrayList();
    private final ObservableList<String> availableModels = FXCollections.observableArrayList();

    // HTTP Client & Utilities
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final List<HttpResponse<InputStream>> activeRequests = new ArrayList<>();

    private static final String API_URL = "http://127.0.0.1:8000";

    @FXML
    public void initialize() {
        setupModelLists();
        setupEventHandlers();
        setupTemperatureSlider();
        refreshModels();
    }

    // ==================== Setup Methods ====================

    private void setupEventHandlers() {
        browseTestSuiteButton.setOnAction(e -> browseTestSuite());
        browseExportButton.setOnAction(e -> browseExportPath());
        refreshModelsButton.setOnAction(e -> refreshModels());
        runBenchmarkButton.setOnAction(e -> runBenchmark());
    }

    private void setupTemperatureSlider() {
        if (temperatureSlider != null) {
            temperatureSlider.valueProperty().addListener((obs, oldVal, newVal) ->
                    temperatureValueLabel.setText(String.format("%.1f", newVal))
            );
        }
    }

    private void setupModelLists() {
        downloadedModelsList.setItems(downloadedModels);
        availableModelsList.setItems(availableModels);

        downloadedModelsList.getSelectionModel().setSelectionMode(SelectionMode.SINGLE);
        availableModelsList.getSelectionModel().setSelectionMode(SelectionMode.SINGLE);

        availableModelsList.setCellFactory(param -> new ModelListCell());
    }

    // ==================== Action Handlers ====================

    @FXML
    public void handleTerminate(ActionEvent event) {
        activeRequests.forEach(response -> {
            try {
                response.body().close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
        activeRequests.clear();

        updateStatus("Process terminated by user.", 0);
        runBenchmarkButton.setDisable(false);
    }

    private void browseTestSuite() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Test Suite");
        fileChooser.getExtensionFilters().add(
                new FileChooser.ExtensionFilter("JSON Files", "*.json")
        );

        File file = fileChooser.showOpenDialog(getStage());
        if (file != null) {
            testSuitePathField.setText(file.getAbsolutePath());
            statusLabel.setText("Test suite loaded: " + file.getName());
        }
    }

    private void browseExportPath() {
        DirectoryChooser directoryChooser = new DirectoryChooser();
        directoryChooser.setTitle("Select Export Folder");
        directoryChooser.setInitialDirectory(new File(System.getProperty("user.home")));

        File selectedDirectory = directoryChooser.showDialog(getStage());
        if (selectedDirectory != null) {
            exportPathField.setText(selectedDirectory.getAbsolutePath());
        }
    }

    private void refreshModels() {
        statusLabel.setText("Connecting to backend...");

        Task<List<String>> fetchTask = createFetchModelsTask();

        fetchTask.setOnSucceeded(e -> {
            downloadedModels.clear();
            downloadedModels.addAll(fetchTask.getValue());
            statusLabel.setText("Models refreshed from Ollama.");
            populateAvailableModels();
        });

        fetchTask.setOnFailed(e -> {
            statusLabel.setText("Failed to connect to backend server.");
            fetchTask.getException().printStackTrace();
            showAlert("Connection Error",
                    "Could not connect to Python backend. Is server.py running?",
                    Alert.AlertType.ERROR);
        });

        new Thread(fetchTask).start();
    }

    private void downloadModel(String modelName) {
        updateStatus("Initializing download for " + modelName + "...", 0);
        runBenchmarkButton.setDisable(true);

        Task<Void> downloadTask = createDownloadTask(modelName);
        bindTaskToUI(downloadTask);

        downloadTask.setOnSucceeded(e -> onDownloadSuccess(modelName));
        downloadTask.setOnFailed(e -> onDownloadFailure(downloadTask));

        new Thread(downloadTask).start();
    }

    private void runBenchmark() {
        ValidationResult validation = validateBenchmarkInputs();
        if (!validation.isValid()) {
            showAlert("Validation Error", validation.getMessage(), Alert.AlertType.WARNING);
            return;
        }

        String selectedModel = downloadedModelsList.getSelectionModel().getSelectedItem();
        double temperature = temperatureSlider.getValue();

        runBenchmarkButton.setDisable(true);
        updateStatus("Starting benchmark...", 0);

        Task<Void> benchmarkTask = createBenchmarkTask(selectedModel, temperature);
        bindTaskToUI(benchmarkTask);

        benchmarkTask.setOnSucceeded(e -> onBenchmarkSuccess(selectedModel));
        benchmarkTask.setOnFailed(e -> onBenchmarkFailure(benchmarkTask));

        new Thread(benchmarkTask).start();
    }

    // ==================== Task Creation ====================

    private Task<List<String>> createFetchModelsTask() {
        return new Task<>() {
            @Override
            protected List<String> call() throws Exception {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(API_URL + "/models"))
                        .GET()
                        .build();

                HttpResponse<String> response = httpClient.send(request,
                        HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() == 200) {
                    return objectMapper.readValue(response.body(), new TypeReference<>() {});
                } else {
                    throw new IOException("Server returned " + response.statusCode());
                }
            }
        };
    }

    private Task<Void> createDownloadTask(String modelName) {
        return new Task<>() {
            @Override
            protected Void call() throws Exception {
                String jsonBody = objectMapper.writeValueAsString(
                        Map.of("model_name", modelName)
                );

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(API_URL + "/models/pull"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                        .build();

                HttpResponse<InputStream> response = httpClient.send(request,
                        HttpResponse.BodyHandlers.ofInputStream());
                activeRequests.add(response);

                if (response.statusCode() != 200) {
                    throw new IOException("Server returned " + response.statusCode());
                }

                processDownloadStream(response.body());
                return null;
            }

            private void processDownloadStream(InputStream inputStream) throws IOException {
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {

                    String line;
                    while ((line = reader.readLine()) != null && !isCancelled()) {
                        processDownloadLine(line);
                    }
                }
            }

            private void processDownloadLine(String line) {
                try {
                    JsonNode node = objectMapper.readTree(line);

                    if (node.has("status")) {
                        updateMessage(node.get("status").asText());
                    }

                    if (node.has("total") && node.has("completed")) {
                        long total = node.get("total").asLong();
                        long completed = node.get("completed").asLong();
                        if (total > 0) {
                            updateProgress(completed, total);
                        }
                    } else {
                        updateProgress(-1, 1);
                    }
                } catch (Exception ignored) {
                    // Skip malformed JSON lines
                }
            }
        };
    }

    private Task<Void> createBenchmarkTask(String selectedModel, double temperature) {
        return new Task<>() {
            @Override
            protected Void call() throws Exception {
                updateMessage("Testing model: " + selectedModel + "...");

                Map<String, Object> payload = Map.of(
                        "model_name", selectedModel,
                        "suite_path", testSuitePathField.getText(),
                        "temperature", temperature
                );

                String jsonBody = objectMapper.writeValueAsString(payload);

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(API_URL + "/run"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8))
                        .build();

                updateProgress(-1, 1);

                HttpResponse<InputStream> response = httpClient.send(request,
                        HttpResponse.BodyHandlers.ofInputStream());
                activeRequests.add(response);

                if (response.statusCode() != 200) {
                    throw new IOException("Server returned error code: " + response.statusCode());
                }

                List<Map<String, Object>> results = objectMapper.readValue(
                        response.body(), new TypeReference<>() {}
                );

                updateProgress(1, 1);
                updateMessage("Saving results...");

                File outputFile = generateOutputFile(selectedModel);
                saveAsCsv(results, outputFile);
                updateMessage("Saved to " + outputFile.getName());

                return null;
            }
        };
    }

    // ==================== Success/Failure Handlers ====================

    private void onDownloadSuccess(String modelName) {
        unbindTaskFromUI();
        updateStatus("Download complete: " + modelName, 1.0);
        runBenchmarkButton.setDisable(false);
        refreshModels();
        showAlert("Download Success",
                "Model " + modelName + " has been successfully downloaded.",
                Alert.AlertType.INFORMATION);
    }

    private void onDownloadFailure(Task<?> task) {
        unbindTaskFromUI();
        statusLabel.setText("Download failed.");
        runBenchmarkButton.setDisable(false);

        Throwable ex = task.getException();
        if (ex != null) {
            ex.printStackTrace();
            showAlert("Download Error",
                    "Failed to download model: " + ex.getMessage(),
                    Alert.AlertType.ERROR);
        }
    }

    private void onBenchmarkSuccess(String selectedModel) {
        unbindTaskFromUI();
        updateStatus("Benchmark complete. Saved: " + exportPathField.getText(), 1.0);
        runBenchmarkButton.setDisable(false);
        showAlert("Success",
                "Benchmark for " + selectedModel + " completed!",
                Alert.AlertType.INFORMATION);
    }

    private void onBenchmarkFailure(Task<?> task) {
        unbindTaskFromUI();
        statusLabel.setText("Benchmark failed.");
        runBenchmarkButton.setDisable(false);

        Throwable ex = task.getException();
        if (ex != null) {
            ex.printStackTrace();
            showAlert("Error",
                    "Benchmark failed: " + ex.getMessage(),
                    Alert.AlertType.ERROR);
        }
    }

    // ==================== Validation ====================

    private ValidationResult validateBenchmarkInputs() {
        String selectedModel = downloadedModelsList.getSelectionModel().getSelectedItem();
        if (selectedModel == null) {
            return ValidationResult.invalid("Please select a model to benchmark.");
        }

        String suitePath = testSuitePathField.getText();
        if (suitePath == null || suitePath.isEmpty()) {
            return ValidationResult.invalid("Please load a test suite first.");
        }

        String exportDirStr = exportPathField.getText();
        if (exportDirStr == null || exportDirStr.trim().isEmpty()) {
            return ValidationResult.invalid("Please specify an export folder.");
        }

        File exportDir = new File(exportDirStr);
        if (!exportDir.exists() || !exportDir.isDirectory()) {
            return ValidationResult.invalid("The selected export path is not a valid directory.");
        }

        return ValidationResult.valid();
    }

    // ==================== Utility Methods ====================

    private void bindTaskToUI(Task<?> task) {
        statusLabel.textProperty().bind(task.messageProperty());
        progressBar.progressProperty().bind(task.progressProperty());
    }

    private void unbindTaskFromUI() {
        statusLabel.textProperty().unbind();
        progressBar.progressProperty().unbind();
    }

    private void updateStatus(String message, double progress) {
        statusLabel.setText(message);
        progressBar.setProgress(progress);
    }

    private File generateOutputFile(String modelName) {
        String safeModelName = modelName.replaceAll("[^a-zA-Z0-9.-]", "_");
        String timestamp = LocalDateTime.now().format(
                DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")
        );
        String filename = "benchmark_" + safeModelName + "_" + timestamp + ".csv";
        return new File(exportPathField.getText(), filename);
    }

    private void saveAsCsv(List<Map<String, Object>> results, File file) throws IOException {
        if (results == null || results.isEmpty()) {
            return;
        }

        List<String> headers = new ArrayList<>(results.get(0).keySet());
        StringBuilder csvContent = new StringBuilder();

        csvContent.append(String.join(",", headers)).append("\n");

        for (Map<String, Object> row : results) {
            String rowString = headers.stream()
                    .map(header -> escapeCsvValue(row.get(header)))
                    .collect(Collectors.joining(","));
            csvContent.append(rowString).append("\n");
        }

        Files.writeString(file.toPath(), csvContent.toString(), StandardCharsets.UTF_8);
    }

    private String escapeCsvValue(Object value) {
        String strVal = (value == null) ? "" : value.toString();
        if (strVal.contains(",") || strVal.contains("\"") || strVal.contains("\n")) {
            return "\"" + strVal.replace("\"", "\"\"") + "\"";
        }
        return strVal;
    }

    private void populateAvailableModels() {
        availableModels.clear();
        availableModels.addAll(
                // Latest Qwen3 models
                "qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b",

                // Gemma 3
                "gemma3:1b", "gemma3:4b",

                // DeepSeek-R1
                "deepseek-r1:1.5b", "deepseek-r1:7b", "deepseek-r1:8b",

                // Qwen 2.5 & Coder
                "qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b",
                "qwen2.5-coder:0.5b", "qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "qwen2.5-coder:7b",

                // Llama 3 family
                "llama3.2:1b", "llama3.2:3b", "llama3.1:8b", "llama3:8b",

                // Mistral & variants
                "mistral:7b", "mistral-nemo:12b",

                // Gemma 2
                "gemma2:2b", "gemma2:9b",

                // Phi models
                "phi3:3.8b", "phi3.5:3.8b", "phi4-mini:3.8b",

                // Granite 4
                "granite4:350m", "granite4:1b", "granite4:3b",

                // SmolLM2
                "smollm2:135m", "smollm2:360m", "smollm2:1.7b",

                // CodeLlama & coding models
                "codellama:7b", "codegemma:2b", "codegemma:7b", "starcoder2:3b", "starcoder2:7b",
                "deepseek-coder:1.3b", "deepseek-coder:6.7b",

                // Dolphin
                "dolphin3:8b", "dolphin-mistral:7b", "dolphin-phi:2.7b",

                // TinyLlama & small models
                "tinyllama:1.1b", "tinydolphin:1.1b",

                // Other popular models
                "orca-mini:3b", "orca-mini:7b", "openchat:7b", "vicuna:7b",
                "neural-chat:7b", "starling-lm:7b", "yi-coder:1.5b", "yi-coder:9b"
        );
    }

    private void showAlert(String title, String content, Alert.AlertType alertType) {
        Alert alert = new Alert(alertType);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(content);
        alert.show();
    }

    private Stage getStage() {
        return (Stage) testSuitePathField.getScene().getWindow();
    }

    // ==================== Inner Classes ====================

    private class ModelListCell extends ListCell<String> {
        private final HBox content;
        private final Label nameLabel;
        private final Button downloadBtn;
        private final Region spacer;

        public ModelListCell() {
            nameLabel = new Label();
            nameLabel.setStyle("-fx-font-weight: bold;");

            spacer = new Region();
            HBox.setHgrow(spacer, Priority.ALWAYS);

            downloadBtn = new Button("Download");
            downloadBtn.setStyle("-fx-background-color: #3498db; -fx-text-fill: white; -fx-font-size: 10px;");
            downloadBtn.setOnAction(event -> {
                String model = getItem();
                if (model != null) {
                    downloadModel(model);
                }
            });

            content = new HBox(10, nameLabel, spacer, downloadBtn);
            content.setAlignment(javafx.geometry.Pos.CENTER_LEFT);
        }

        @Override
        protected void updateItem(String item, boolean empty) {
            super.updateItem(item, empty);

            if (empty || item == null) {
                setGraphic(null);
                return;
            }

            nameLabel.setText(item);

            boolean isInstalled = downloadedModels.contains(item);
            if (isInstalled) {
                downloadBtn.setText("Installed");
                downloadBtn.setDisable(true);
                downloadBtn.setStyle("-fx-background-color: #27ae60; -fx-text-fill: white; -fx-font-size: 10px;");
            } else {
                downloadBtn.setText("Download");
                downloadBtn.setDisable(false);
                downloadBtn.setStyle("-fx-background-color: #3498db; -fx-text-fill: white; -fx-font-size: 10px;");
            }

            setGraphic(content);
        }
    }

    private static class ValidationResult {
        private final boolean valid;
        private final String message;

        private ValidationResult(boolean valid, String message) {
            this.valid = valid;
            this.message = message;
        }

        public boolean isValid() {
            return valid;
        }

        public String getMessage() {
            return message;
        }

        public static ValidationResult valid() {
            return new ValidationResult(true, null);
        }

        public static ValidationResult invalid(String message) {
            return new ValidationResult(false, message);
        }
    }
}