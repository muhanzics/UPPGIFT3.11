package com.benchmark;

import java.io.*;
import java.net.URL;

public class DependencyManager {

    private static final String OLLAMA_URL_WIN = "https://ollama.com/download/OllamaSetup.exe";

    // We assume the backend folder is next to the Java app
    public static final String BACKEND_EXE = "backend/dist/backend/backend.exe";

    public interface ProgressCallback {
        void onProgress(String message, double progress);
    }

    public static void ensureEnvironmentReady(ProgressCallback callback) throws Exception {
        if (!isOllamaInstalled()) {
            callback.onProgress("Ollama not found. Downloading...", 0.3);
            File installer = downloadOllamaInstaller();
            callback.onProgress("Installing Ollama...", 0.6);
            runInstaller(installer);
            Thread.sleep(5000);
        } else {
            callback.onProgress("Ollama is ready.", 0.5);
        }

        // 2. Check Backend
        File backend = new File(BACKEND_EXE);
        if (!backend.exists()) {
            // If this happens, your build is missing files
            throw new FileNotFoundException("Backend executable not found at: " + backend.getAbsolutePath());
        }

        callback.onProgress("Backend ready.", 1.0);
    }

    public static Process startBackendServer() throws IOException {
        System.out.println("Starting backend from: " + new File(BACKEND_EXE).getAbsolutePath());

        ProcessBuilder pb = new ProcessBuilder(BACKEND_EXE);
        pb.redirectErrorStream(true);
        return pb.start();
    }

    public static void terminate() {
        try {
            new ProcessBuilder("Get-Process | Where-Object {$_.ProcessName -like '*ollama*'} | Stop-Process").start().waitFor();
        }
        catch (Exception e) {
            System.err.println("Ollama Terminate failed: " + e);
        }
    }

    // --- Helper Methods (Same as before) ---
    private static boolean isOllamaInstalled() {
        try { return new ProcessBuilder("ollama", "--version").start().waitFor() == 0; }
        catch (Exception e) { return false; }
    }

    private static File downloadOllamaInstaller() throws IOException {
        URL url = new URL(OLLAMA_URL_WIN);
        File tempFile = File.createTempFile("OllamaSetup", ".exe");
        try (InputStream in = url.openStream(); FileOutputStream out = new FileOutputStream(tempFile)) {
            byte[] buffer = new byte[1024];
            int bytesRead;
            while ((bytesRead = in.read(buffer)) != -1) out.write(buffer, 0, bytesRead);
        }
        return tempFile;
    }

    private static void runInstaller(File installer) throws Exception {
        new ProcessBuilder(installer.getAbsolutePath()).start().waitFor();
    }
}