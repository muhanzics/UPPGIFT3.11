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

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Make sure Ollama is running (in another terminal)
ollama serve

# 3. Download a model to test
ollama pull qwen2.5:3b

# 4. Run the tool
python main.py
```

Then follow the menu: Load test suite → Run tests → View results

## How It Works

### 1. Test Suite Format

Create a JSON file in `test_suites/` folder:

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

## Project Structure

```
UPPGIFT3.11/
├── main.py                      # Start here - runs the CLI
├── src/                         # Backend code (GUI-ready)
│   ├── models.py               # Data structures (TestCase, TestResult, etc.)
│   ├── model_manager.py        # Talks to Ollama API
│   ├── test_runner.py          # Executes tests and evaluates results
│   ├── results_storage.py      # SQLite database operations
│   ├── test_suite_loader.py    # Loads JSON test files
│   └── cli.py                  # Terminal interface (replace with GUI)
├── test_suites/                # Put your test JSON files here
│   ├── animal_detection_demo.json
│   └── sentiment_analysis.json
└── benchmark_results.db        # Database (auto-created)
```

## For GUI Developer

### Current State

- **Backend is complete and modular**
- **CLI works** (`python main.py`)
- **All core functions are in `src/`** and can be imported

### What You Need to Do

**Replace `src/cli.py` with a GUI that:**

1. **Loads test suites** → Call `TestSuiteLoader.load_test_suite(filepath)`
2. **Lists models** → Call `ModelManager.list_models()`
3. **Runs tests** → Call `TestRunner.run_test_suite(tests, model_config)`
4. **Shows results** → Call `ResultsStorage.get_test_runs()` and display

### Example Code for GUI

```python
from src import (
    ModelManager,
    TestRunner,
    TestSuiteLoader,
    ResultsStorage,
    ModelConfig
)

# Setup
manager = ModelManager("http://localhost:11434")
runner = TestRunner(manager)
storage = ResultsStorage("benchmark_results.db")

# Load tests
tests = TestSuiteLoader.load_test_suite("test_suites/my_tests.json")

# Configure model
model = ModelConfig(name="qwen2.5:3b", temperature=0.0)

# Run tests (this is what takes time - show progress bar)
results = runner.run_test_suite(tests, model, verbose=False)

# Get summary stats
passed = sum(1 for r in results if r.passed)
accuracy = (passed / len(results)) * 100
avg_time = sum(r.response_time for r in results) / len(results)

# Display in your GUI
print(f"Accuracy: {accuracy}%")
print(f"Average time: {avg_time:.2f}s")
```

### Key Classes to Understand

**`TestCase`** - One test (input + question + expected answer)  
**`TestResult`** - Result from running one test (passed/failed, time taken)  
**`ModelConfig`** - Model settings (name, temperature, etc.)  
**`TestRunner`** - Does the actual testing  
**`ResultsStorage`** - Saves/loads from database

All in `src/models.py` with full documentation.

### GUI Functionality Needed

**Main screens:**

1. **Test Suite Manager** - Load/create/edit test suites
2. **Model Selector** - Pick which model to test
3. **Run Tests** - Start tests, show progress, display results
4. **Results Viewer** - Browse past runs, compare models
5. **Settings** - Ollama URL, database path, etc.

**Nice to have:**

- Create tests directly in GUI (no JSON editing)
- Real-time progress during test runs
- Charts comparing models
- Export results to CSV

### Testing Your GUI

Use the example test suites:

- `test_suites/animal_detection_demo.json` (10 simple tests)
- `test_suites/sentiment_analysis.json` (5 tests)

Or look at `example_usage.py` for programmatic usage.

## Notes

- **Temperature**: 0.0 = consistent answers, 1.0 = creative/random
- **Few-shot examples**: Can include example Q&A pairs in test cases
- **Database**: SQLite file, easy to query or migrate
- **Models**: User downloads via Ollama CLI, we just list them

## Troubleshooting

**"Cannot connect to Ollama"** → Run `ollama serve` first  
**"No models"** → Run `ollama pull qwen2.5:3b`  
**Import errors** → Make sure you're in project root directory

---

**That's it!** The backend handles everything. Your job is making it look good and user-friendly. 🎨
