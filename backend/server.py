# Muhaned Mahdi
# Enes Özbek

import uvicorn
import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from datetime import datetime

# Import your existing modules
# Ensure these are in a folder named 'src' or adjust imports accordingly
from src.model_manager import ModelManager
from src.test_runner import TestRunner
from src.test_suite_loader import TestSuiteLoader
from src.results_storage import ResultsStorage, generate_run_id
from src.models import ModelConfig, TestRunSummary

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 8000
OLLAMA_URL = "http://localhost:11434"
DB_PATH = "benchmark_results.db"

# --- App Initialization ---
app = FastAPI(title="LLM Benchmark Server")

# Allow CORS so Java app can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Service Initialization ---
print(f"Initializing services...")
try:
    manager = ModelManager(OLLAMA_URL)
    runner = TestRunner(manager)
    storage = ResultsStorage(DB_PATH)
    loader = TestSuiteLoader()
    print("Services initialized successfully.")
except Exception as e:
    print(f"!! Critical Error initializing services: {e}")
    traceback.print_exc()

# --- Data Models ---
class TestRunRequest(BaseModel):
    model_name: str
    suite_path: str
    temperature: float = 0.0

class PullModelRequest(BaseModel):
    model_name: str

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "running", "ollama_connected": manager.test_connection()}

@app.get("/models")
def get_models():
    """Returns list of available Ollama models."""
    print("Requesting model list...")
    models = manager.list_models()
    print(f"Found {len(models)} models.")
    return models

@app.post("/models/pull")
def pull_model(request: PullModelRequest):
    """
    Streams the download progress of a model.
    """
    print(f"Received request to pull model: {request.model_name}")

    # Use the generator function we just created
    return StreamingResponse(
        manager.pull_model_generator(request.model_name),
        media_type="application/x-ndjson"
    )

@app.post("/run")
def run_benchmark(request: TestRunRequest):
    """
    Executes the benchmark:
    1. Validates file path
    2. Loads test suite
    3. Runs tests via Ollama
    4. Saves results to DB
    5. Returns results to Java
    """
    print(f"\n--- NEW BENCHMARK REQUEST ---")
    print(f"Model: {request.model_name}")
    print(f"Suite: {request.suite_path}")
    print(f"Temp:  {request.temperature}")

    try:
        # 1. Validate File Path
        if not os.path.exists(request.suite_path):
            error_msg = f"File not found on server: {request.suite_path}"
            print(f"{error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # 2. Load Test Suite
        print("Loading test suite...")
        suites = loader.load_test_suite(request.suite_path)
        if not suites:
            raise HTTPException(status_code=400, detail="Test suite is empty or invalid JSON.")
        print(f"Loaded {len(suites)} test cases.")

        # 3. Configure Model
        config = ModelConfig(name=request.model_name, temperature=request.temperature)

        # 4. Run Benchmark
        print("Starting test execution (this may take time)...")
        results = runner.run_test_suite(suites, config, verbose=True)
        print("Benchmark execution complete.")

        # 5. Calculate Statistics for DB Summary
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        total_time = sum(r.response_time for r in results)
        avg_time = total_time / total if total > 0 else 0
        accuracy = (passed / total) * 100 if total > 0 else 0

        summary = TestRunSummary(
            run_id=generate_run_id(),
            model_name=request.model_name,
            test_suite_name=os.path.basename(request.suite_path),
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            total_time=total_time,
            average_time=avg_time,
            accuracy=accuracy,
            timestamp=datetime.now()
        )

        # 6. Save to Database
        print("Saving results to database...")
        storage.save_test_run(summary, results)
        print(f"Saved run {summary.run_id}")

        # 7. Return to Client
        # Using .to_dict() from your models.py TestResult class
        response_data = [r.to_dict() for r in results]
        return response_data

    except HTTPException as he:
        raise he
    except Exception as e:
        print("!!!!!! CRASH DURING BENCHMARK !!!!!!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)