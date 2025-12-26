package com.benchmark;

import java.io.*;
import java.nio.file.*;
import java.util.*;

public class DependencyManager {

    private static final boolean IS_WINDOWS = System.getProperty("os.name").toLowerCase().contains("win");

    // Updated paths based on your screenshot
    private static final String BACKEND_DIR = "backend";
    private static final String VENV_DIR = "backend/venv";
    private static final String REQUIREMENTS_FILE = "backend/requirements.txt";
    private static final String SERVER_SCRIPT = "backend/server.py";

    // Virtual Environment Python Path
    private static final String VENV_PYTHON = IS_WINDOWS ?
            VENV_DIR + "/Scripts/python.exe" : VENV_DIR + "/bin/python";

    public interface ProgressCallback {
        void onProgress(String message, double progress);
    }

    public static void ensureEnvironmentReady(ProgressCallback callback) throws Exception {
        // 1. (Optional) Your existing Ollama check logic goes here...

        // 2. Check for Virtual Environment
        File venvExec = new File(VENV_PYTHON);
        if (!venvExec.exists()) {
            callback.onProgress("Initializing Python environment...", 0.4);
            setupVirtualEnvironment();

            callback.onProgress("Installing requirements from backend/requirements.txt...", 0.7);
            installRequirements();
        } else {
            callback.onProgress("Python environment ready.", 0.8);
        }

        callback.onProgress("Backend systems verified.", 1.0);
    }

    private static void setupVirtualEnvironment() throws Exception {
        String pythonCmd = getSystemPython();
        // Creates the 'venv' folder inside 'backend'
        ProcessBuilder pb = new ProcessBuilder(pythonCmd, "-m", "venv", "venv");
        pb.directory(new File(BACKEND_DIR));
        executeProcess(pb, "Virtual Environment Creation");
    }

    private static void installRequirements() throws Exception {
        // Run pip install using the python executable inside the venv
        ProcessBuilder pb = new ProcessBuilder(VENV_PYTHON, "-m", "pip", "install", "-r", REQUIREMENTS_FILE);
        executeProcess(pb, "Dependency Installation");
    }

    public static Process startBackendServer() throws IOException {
        System.out.println("Launching Python API (server.py)...");
        // We run 'python backend/server.py' using the venv interpreter
        ProcessBuilder pb = new ProcessBuilder(VENV_PYTHON, SERVER_SCRIPT);

        // This ensures relative imports in server.py (like from src.models) work
        pb.directory(new File("."));

        pb.redirectErrorStream(true);
        return pb.start();
    }

    // --- Utility Methods ---

    private static String getSystemPython() throws IOException {
        String[] cmds = IS_WINDOWS ? new String[]{"python", "py"} : new String[]{"python3", "python"};
        for (String cmd : cmds) {
            try {
                Process p = new ProcessBuilder(cmd, "--version").start();
                if (p.waitFor() == 0) return cmd;
            } catch (Exception ignored) {}
        }
        throw new IOException("Python 3 not found. Please ensure Python is installed and added to PATH.");
    }

    private static void executeProcess(ProcessBuilder pb, String stepName) throws Exception {
        pb.inheritIO();
        Process p = pb.start();
        if (p.waitFor() != 0) {
            throw new RuntimeException(stepName + " failed. Check terminal for errors.");
        }
    }
}