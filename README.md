# LLM Benchmarking System

**Simple tool to test and compare different AI models on your own test cases.**

## What This Does

You give it:

1. A test suite (JSON file with questions and expected answers)
2. An AI model to test (from Ollama)

It gives you:

- How accurate the model is (% of correct answers)
- How fast it responds (seconds per test)
- Which tests passed/failed
- Historical comparison between different models

## Prerequisites
- Java
- Python (Preferably from python.org)
- Ollama (Installs automatically if not present)

## Quick Start

- Download windows or linux zip folders in the release page
- Unzip it and in the same folder run: ```java -jar ollama-benchmark-tool-1.0-SNAPSHOT.jar```.

### After installation and environment setup

- Select test suite path
- Select export path for results
- Select a model from **Downloaded Models** or download a new one
- Select model temperature
- Run benchmark

## How It Works

### 1. Test Suite Format

Create a JSON file like following:

```json
{
  "name": "my_tests",
  "tests": [
    {
      "id": "test_001",
      "name": "Dog detection",
      "input_text": "I saw a golden retriever at the park.",
      "question": "Does this text mention a dog?",
      "expected_answer": true,
      "evaluation_type": "boolean"
    }
  ]
}
```

**Test fields:**

- `input_text`: The text to analyze
- `question`: What you're asking the model
- `expected_answer`: What the correct answer should be
- `evaluation_type`: How to check if answer is correct
  - `"boolean"` = true/false
  - `"exact_match"` = exact text match
  - `"contains"` = check if answer contains keyword


**(Example test suites are found in source code UPPGIFT3.11/test_suites)**

### 2. Running Tests

The system:

1. Takes your test case
2. Builds a prompt: text + question + "respond with JSON"
3. Sends to the AI model
4. Parses the response
5. Compares actual vs expected answer
6. Records if it passed/failed + how long it took

### 3. Results Storage

Everything is saved to `benchmark_results.db` (SQLite database):

- Individual test results
- Summary statistics per run
- Historical data for comparison

Each test is also saved and exported as a csv file. 

## Project Structure

```
UPPGIFT3.11/
├── ollama-benchmark-tool-1.0-SNAPSHOT.jar  # Main JavaFX application launcher
├── benchmark_results.db                    # SQLite Database (Auto-created)
└── backend/                                # Python Backend Environment
    ├── venv/                               # Python Virtual Environment
    ├── server.py                           # FastAPI / Uvicorn API Server
    ├── requirements.txt                    # Python dependencies
    └── src/                                # Core logic source code
        ├── models.py                       # Data structures (TestCase, TestResult)
        ├── model_manager.py                # Ollama API interaction logic
        ├── test_runner.py                  # Test execution and evaluation
        ├── results_storage.py              # SQLite database operations
        ├── test_suite_loader.py            # JSON file parsing
        └── cli.py                          # Terminal fallback interface
```

### Troubleshooting

### Alternatives if windows zip doesnt work
- Download source code, unzip it and run mvn clean package 

