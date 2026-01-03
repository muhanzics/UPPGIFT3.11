// Muhaned Mahdi
// Enes Özbek

package com.benchmark;

import java.io.*;
import java.nio.file.Path;
import java.nio.file.Paths;

public class DependencyManager {

    private static final boolean IS_WINDOWS = System.getProperty("os.name").toLowerCase().contains("win");

    // Updated paths based on your screenshot
    private static final String BACKEND_DIR = "backend";
    private static final String VENV_DIR = "backend/venv";
    private static final String REQUIREMENTS_FILE = "backend/requirements.txt";
    private static final String SERVER_SCRIPT = "backend/server.py";

    private static String getVenvPythonExecutable() {
        // This logic runs EVERY time it's called, so it sees the new folders
        Path scriptsPath = Paths.get(VENV_DIR, "Scripts", "python.exe");
        Path binPath = Paths.get(VENV_DIR, "bin", "python.exe");
        Path unixPath = Paths.get(VENV_DIR, "bin", "python");

        if (scriptsPath.toFile().exists())
            return scriptsPath.toAbsolutePath().toString();
        if (binPath.toFile().exists())
            return binPath.toAbsolutePath().toString();
        if (unixPath.toFile().exists())
            return unixPath.toAbsolutePath().toString();

        // Fallback for the CREATION step if nothing exists yet
        return IS_WINDOWS ? scriptsPath.toAbsolutePath().toString() : unixPath.toAbsolutePath().toString();
    }

    public interface ProgressCallback {
        void onProgress(String message, double progress);
    }

    public static void ensureEnvironmentReady(ProgressCallback callback) throws Exception {
        File venvFolder = new File(VENV_DIR);

        if (!venvFolder.exists()) {
            callback.onProgress("Creating Virtual Environment...", 0.3);
            setupVirtualEnvironment();

            // IMPORTANT: We don't check for VENV_PYTHON here because
            // the method getVenvPythonExecutable() will now find it
            // since setupVirtualEnvironment() just finished.
        }

        callback.onProgress("Installing requirements...", 0.6);
        installRequirements(); // Inside here, call getVenvPythonExecutable()

        callback.onProgress("Environment Ready!", 1.0);
    }

    private static void setupVirtualEnvironment() throws Exception {
        String pythonCmd = getSystemPython();
        // Use absolute path for the venv directory to avoid confusion
        File venvLocation = new File(VENV_DIR);

        ProcessBuilder pb = new ProcessBuilder(pythonCmd, "-m", "venv", venvLocation.getAbsolutePath());
        executeProcess(pb, "Virtual Environment Creation");
    }

    private static void installRequirements() throws Exception {
        String pythonExec = getVenvPythonExecutable(); // Freshly resolved path
        ProcessBuilder pb = new ProcessBuilder(pythonExec, "-m", "pip", "install", "-r", REQUIREMENTS_FILE);
        executeProcess(pb, "Dependency Installation");
    }

    public static Process startBackendServer() throws IOException {
        String pythonExec = getVenvPythonExecutable();
        ProcessBuilder pb = new ProcessBuilder(pythonExec, SERVER_SCRIPT);
        pb.directory(new File("."));
        pb.redirectErrorStream(true);
        return pb.start();
    }

    // --- Utility Methods ---

    private static String getSystemPython() throws IOException {
        String[] cmds = IS_WINDOWS ? new String[] { "python", "py" } : new String[] { "python3", "python" };
        for (String cmd : cmds) {
            try {
                Process p = new ProcessBuilder(cmd, "--version").start();
                if (p.waitFor() == 0)
                    return cmd;
            } catch (Exception ignored) {
            }
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