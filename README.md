# LLM Benchmarking Tool

Simple Python application to benchmark and compare AI models from Ollama on custom test suites.

## Prerequisites

1. **Python 3.8+**
2. **Ollama** - Download from [ollama.com](https://ollama.com/download)

## Installation

### Windows

```powershell
# Clone or download this repository
cd UPPGIFT3.11

# Install dependencies
pip install -r backend/requirements.txt

# Run the application
python gui_app.py
```

### Linux/Mac

```bash
# Clone or download this repository
cd UPPGIFT3.11

# Install dependencies
pip install -r backend/requirements.txt

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Run the application
python gui_app.py
```

## How to Use

1. **Launch** - Run `python gui_app.py`
   - The app will automatically start Ollama if needed
   - If Ollama isn't installed, you'll be prompted to download it

2. **Select Test Suite** - Click "Browse" next to "Test Suite" and choose a JSON file
   - Example test suites are in the `test_suites/` folder

3. **Select Export Path** - Choose where to save the results CSV file

4. **Select a Model**:
   - From "Downloaded Models" (models already on your system)
   - OR click a model in "Available Models" to download it

5. **(Optional) Few-Shot Prompting**:
   - Browse for a CSV file with example input/output pairs
   - Enable the toggle to use few-shot learning

6. **Adjust Temperature** (0.0-1.0):
   - Lower = more deterministic/consistent
   - Higher = more creative/random

7. **Run Benchmark** - Click the green button

## Test Suite Format

Create a JSON file like this:

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

**Evaluation types:**
- `"boolean"` - true/false answers
- `"exact_match"` - exact text match
- `"contains"` - check if answer contains a keyword

## Few-Shot CSV Format

For few-shot prompting, create a CSV with two columns:

```csv
input,output
"The cat is sleeping","animal: cat, action: sleeping"
"The dog is barking","animal: dog, action: barking"
```

## Results

Results are saved in two places:
1. **CSV file** - In your chosen export folder with timestamp
2. **SQLite database** - `benchmark_results.db` (for historical tracking)

## Troubleshooting

**"Could not connect to Ollama"**
- Make sure Ollama is installed and running
- Try running `ollama serve` manually in a terminal

**"No module named 'customtkinter'"**
- Run: `pip install -r backend/requirements.txt`

**Models not showing up**
- Click "Refresh Models" button
- Check Ollama is running: `ollama list`

## Project Structure

```
UPPGIFT3.11/
├── gui_app.py                  # Main application
├── backend/
│   ├── requirements.txt        # Python dependencies
│   ├── server.py              # FastAPI server (optional)
│   └── src/
│       ├── model_manager.py   # Ollama API interface
│       ├── test_runner.py     # Test execution logic
│       ├── test_suite_loader.py
│       ├── results_storage.py # SQLite database handler
│       └── models.py          # Data models
├── test_suites/               # Example test suites
└── benchmark_results.db       # Results database (auto-created)
```

## Authors

Muhaned Mahdi & Enes Özbek

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

## Troubleshooting

### Alternatives if either zip doesnt work
- Download source code, unzip it and run mvn clean package 

