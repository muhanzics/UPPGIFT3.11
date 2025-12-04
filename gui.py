import streamlit as st
import pandas as pd
import time
import subprocess
import os
import re
import threading
from src import (
    ModelManager,
    TestRunner,
    TestSuiteLoader,
    ResultsStorage,
    ModelConfig,
    TestRunSummary,
    TestCase,
    generate_run_id,
    EvaluationType
)

# --- Configuration & Setup ---
st.set_page_config(page_title="LLM Benchmark Dashboard", page_icon="🤖", layout="wide")

# Initialize Core Classes
if 'manager' not in st.session_state:
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    st.session_state.manager = ModelManager(ollama_url)

if 'storage' not in st.session_state:
    st.session_state.storage = ResultsStorage("benchmark_results.db")

if 'runner' not in st.session_state:
    st.session_state.runner = TestRunner(st.session_state.manager)

if 'loader' not in st.session_state:
    st.session_state.loader = TestSuiteLoader()

if 'new_suite_tests' not in st.session_state:
    st.session_state.new_suite_tests = []

# --- Sidebar Navigation ---
st.sidebar.title("🤖 LLM Benchmarker")
page = st.sidebar.radio("Navigate", ["Run Tests", "Results Viewer", "Test Suite Manager", "Model Manager"])

# --- PAGE: Run Tests ---
if page == "Run Tests":
    st.title("🚀 Run Benchmark Tests")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Select Test Suite")
        available_suites = st.session_state.loader.list_test_suites()
        
        if not available_suites:
            st.warning("No test suites found.")
            selected_suite_path = None
        else:
            selected_suite_path = st.selectbox("Choose a suite file", available_suites)
            
        if selected_suite_path:
            test_cases = st.session_state.loader.load_test_suite(selected_suite_path)
            st.info(f"Loaded {len(test_cases)} test cases.")

    with col2:
        st.subheader("2. Select Model")
        models = st.session_state.manager.list_models()
        if not models:
            st.error("No models found. Go to 'Model Manager' to download one.")
            selected_model = None
        else:
            selected_model = st.selectbox("Choose a Model", models)
            
        temperature = st.slider("Temperature", 0.0, 1.0, 0.0)

    if st.button("▶️ Start Benchmark", type="primary", disabled=(not selected_suite_path or not selected_model)):
        st.divider()
        st.write(f"Running **{len(test_cases)}** tests on **{selected_model}**...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_container = st.container()
        
        config = ModelConfig(name=selected_model, temperature=temperature)
        results = []
        
        for i, test_case in enumerate(test_cases):
            status_text.text(f"Running test {i+1}/{len(test_cases)}: {test_case.name}...")
            result = st.session_state.runner.run_test(test_case, config)
            results.append(result)
            progress_bar.progress((i + 1) / len(test_cases))
            
            with result_container:
                if result.passed:
                    st.success(f"✅ **{test_case.name}** | {result.response_time:.2f}s")
                else:
                    st.error(f"❌ **{test_case.name}** | Exp: {result.expected_answer} | Got: {result.actual_answer}")

        # Save Results
        passed = sum(1 for r in results if r.passed)
        summary = TestRunSummary(
            run_id=generate_run_id(),
            model_name=selected_model,
            test_suite_name=selected_suite_path,
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=len(results) - passed,
            total_time=sum(r.response_time for r in results),
            average_time=sum(r.response_time for r in results) / len(results),
            accuracy=(passed / len(results)) * 100
        )
        st.session_state.storage.save_test_run(summary, results)
        st.balloons()
        st.success(f"Done! Accuracy: {summary.accuracy:.1f}%")

# --- PAGE: Results Viewer ---
elif page == "Results Viewer":
    st.title("📊 Analysis & Results")
    runs_data = st.session_state.storage.get_test_runs()
    
    if runs_data:
        df = pd.DataFrame(runs_data)
        st.dataframe(df[['run_id', 'model_name', 'accuracy', 'average_time', 'timestamp']], use_container_width=True)
        
        selected_run_id = st.selectbox("Inspect Run Details", df['run_id'].unique())
        if selected_run_id:
            results = st.session_state.storage.get_test_results(selected_run_id)
            res_df = pd.DataFrame(results)
            st.dataframe(res_df[['test_name', 'passed', 'expected_answer', 'actual_answer', 'response_time']], use_container_width=True)
    else:
        st.info("No results found.")

# --- PAGE: Test Suite Manager ---
elif page == "Test Suite Manager":
    st.title("📂 Test Suite Manager")
    
    tab1, tab2 = st.tabs(["Create New Suite (No Code)", "View Existing"])
    
    with tab1:
        st.subheader("Add Test Cases")
        
        with st.form("add_test_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                t_name = st.text_input("Test Name", placeholder="e.g. Sentiment Check")
                t_input = st.text_area("Input Text", placeholder="The text to analyze...")
            with col_b:
                t_question = st.text_input("Question/Instruction", placeholder="e.g. Is this positive?")
                t_expected = st.text_input("Expected Answer", placeholder="e.g. Positive")
                t_type = st.selectbox("Evaluation Type", ["exact_match", "contains", "boolean"])
            
            # --- NEW: Advanced Options ---
            with st.expander("Advanced: System Prompt & Few-Shot Examples"):
                t_system = st.text_input("System Prompt", placeholder="You are a helpful assistant...")
                
                st.caption("Add examples below. Format: `Input: ... Output: ...` separated by `---`")
                t_few_shot_raw = st.text_area("Few-Shot Examples", height=150, 
                    placeholder="Input: I love this!\nOutput: Positive\n---\nInput: I hate this.\nOutput: Negative")

            submitted = st.form_submit_button("Add Test Case")
            
            if submitted:
                if t_name and t_question:
                    # --- Parse Few Shots ---
                    parsed_few_shots = []
                    if t_few_shot_raw.strip():
                        # Split by separator '---'
                        raw_examples = t_few_shot_raw.split("---")
                        for ex in raw_examples:
                            # Simple regex to find Input: ... Output: ...
                            # Note: DOTALL flag allows . to match newlines
                            in_match = re.search(r'Input:(.*?)(?=Output:|$)', ex, re.IGNORECASE | re.DOTALL)
                            out_match = re.search(r'Output:(.*?)(?=$)', ex, re.IGNORECASE | re.DOTALL)
                            
                            if in_match and out_match:
                                parsed_few_shots.append({
                                    "input": in_match.group(1).strip(),
                                    "output": out_match.group(1).strip()
                                })
                    
                    new_test = TestCase(
                        id=str(len(st.session_state.new_suite_tests) + 1),
                        name=t_name,
                        input_text=t_input,
                        question=t_question,
                        expected_answer=t_expected,
                        evaluation_type=EvaluationType(t_type),
                        system_prompt=t_system if t_system else None,
                        few_shot_examples=parsed_few_shots if parsed_few_shots else None
                    )
                    st.session_state.new_suite_tests.append(new_test)
                    st.success(f"Added '{t_name}' ({len(parsed_few_shots)} examples)")
                else:
                    st.error("Name and Question are required.")

        # Staging Area Display
        if st.session_state.new_suite_tests:
            st.divider()
            st.write(f"### Staging Area ({len(st.session_state.new_suite_tests)} tests)")
            
            preview_data = [{
                "Name": t.name, 
                "Question": t.question, 
                "Expected": t.expected_answer,
                "Examples": len(t.few_shot_examples) if t.few_shot_examples else 0
            } for t in st.session_state.new_suite_tests]
            st.table(preview_data)
            
            col_save_1, col_save_2 = st.columns([3, 1])
            with col_save_1:
                file_name = st.text_input("Filename (e.g., 'history_tests.json')")
            with col_save_2:
                st.write("") 
                st.write("") 
                if st.button("💾 Save Suite"):
                    if not file_name.endswith(".json"):
                        file_name += ".json"
                    full_path = os.path.join("test_suites", file_name)
                    os.makedirs("test_suites", exist_ok=True)
                    st.session_state.loader.save_test_suite(st.session_state.new_suite_tests, full_path)
                    st.success(f"Saved to {full_path}")
                    st.session_state.new_suite_tests = []
                    st.rerun()
            
            if st.button("Clear Staging Area"):
                st.session_state.new_suite_tests = []
                st.rerun()

    with tab2:
        suites = st.session_state.loader.list_test_suites()
        if suites:
            sel_suite = st.selectbox("Select Suite to View", suites)
            content = st.session_state.loader.load_test_suite(sel_suite)
            st.json([t.to_dict() for t in content])

# --- PAGE: Model Manager ---
elif page == "Model Manager":
    st.title("🧠 Model Manager")
    
    st.subheader("Download New Model")
    
    # --- NEW: Popular Models Dropdown ---
    POPULAR_MODELS = [
        "Select a model...",
        "llama3.3",
        "llama3.2",
        "llama3.2:1b",
        "llama3.2-vision",
        "llama3.1",
        "llama3",
        "gemma3",
        "gemma2",
        "gemma2:2b",
        "gemma2:9b",
        "gemma2:27b",
        "mistral",
        "mistral-nemo",
        "mistral-small",
        "mixtral",
        "qwen2.5",
        "qwen2.5:0.5b",
        "qwen2.5:7b",
        "qwen2.5:14b",
        "qwen2.5:32b",
        "qwen2.5-coder",
        "phi4",
        "phi3",
        "phi3:14b",
        "deepseek-r1",
        "deepseek-v3",
        "deepseek-coder",
        "codellama",
        "yi",
        "llava",
        "llava-llama3",
        "tinyllama",
        "vicuna",
        "orca-mini",
        "nomic-embed-text",
        "mxbai-embed-large",
        "starling-lm",
        "dolphin-mixtral",
        "command-r",
        "qwq",
        "neural-chat",
        "openhermes",
        "wizardlm2",
        "zephyr",
        "solar",
        "hermes3",
        "aya",
        "granite-code",
        "llama2",
        "falcon"
    ]
    
    col_dl_1, col_dl_2 = st.columns([3, 1])

    st.divider()

    st.subheader("Installed Models")
    current_models = st.session_state.manager.list_models()
    if current_models:
        for m in current_models:
            st.text(f"• {m}")
    else:
        st.warning("No models installed.")
    
    with col_dl_1:
        # Allow user to pick from list OR type their own
        quick_select = st.selectbox("Quick Select", POPULAR_MODELS)
        
        # If user selects something valid, use it; otherwise clear the box
        default_val = quick_select if quick_select != "Select a popular model..." else ""
        
        new_model_name = st.text_input("Model Name (or type custom)", value=default_val)
        st.caption("See full library at [ollama.com/library](https://ollama.com/library)")
    
    with col_dl_2:
        st.write("") 
        st.write("")
        download_btn = st.button("⬇️ Download")
    
    if download_btn and new_model_name:
        # Create a container that tracks the high-level status
        status_box = st.status(f"Requesting {new_model_name}...", expanded=True)
        
        # Create placeholders INSIDE the status box
        # This allows us to overwrite lines instead of appending them
        p_bar = status_box.progress(0)
        log_line = status_box.empty()
        
        try:
            process = subprocess.Popen(
                ["ollama", "pull", new_model_name],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=1,            # Line buffered
                universal_newlines=True
            )
            
            # Read line by line
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    clean_msg = output.strip()
                    # Update the text line (overwrites previous text)
                    log_line.text(clean_msg)
                    
                    # OPTIONAL: Extract percentage for the progress bar
                    # Looks for numbers followed by % (e.g., "45%")
                    match = re.search(r'(\d+)%', clean_msg)
                    if match:
                        percent = int(match.group(1))
                        p_bar.progress(percent / 100)
            
            if process.returncode == 0:
                p_bar.progress(1.0) # Fill bar
                status_box.update(label=f"✅ Successfully downloaded {new_model_name}!", state="complete", expanded=False)
                time.sleep(1)
                st.rerun()
            else:
                status_box.update(label="❌ Download failed", state="error")
                
        except Exception as e:
            status_box.update(label="❌ Error executing command", state="error")
            st.error(f"Error: {e}")