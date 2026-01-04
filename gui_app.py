# Muhaned Mahdi
# Enes Özbek

"""
CustomTkinter GUI for LLM Benchmarking System
Direct integration with backend - no HTTP/FastAPI needed
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import csv

# direct imports from backend
from backend.src.model_manager import ModelManager
from backend.src.test_runner import TestRunner
from backend.src.test_suite_loader import TestSuiteLoader
from backend.src.results_storage import ResultsStorage, generate_run_id
from backend.src.models import ModelConfig, TestRunSummary


class LoadingWindow(ctk.CTk):
    """loading window to show startup progress"""
    
    def __init__(self):
        super().__init__()
        
        self.title("LLM Benchmark - Starting")
        self.geometry("400x200")
        
        # center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Initializing...",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=30)
        
        # progress bar
        self.progress = ctk.CTkProgressBar(self, width=300)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        self.ollama_process = None
    
    def update_status(self, message, progress=None):
        """update status message and progress"""
        self.status_label.configure(text=message)
        if progress is not None:
            self.progress.set(progress)
        self.update()
    
    def check_ollama_installed(self):
        """check if ollama is installed"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            # ollama command not found
            return False
        except:
            return False
    
    def is_ollama_running(self):
        """check if ollama server is already running"""
        try:
            manager = ModelManager("http://localhost:11434")
            return manager.test_connection()
        except:
            return False
    
    def start_ollama(self):
        """start ollama server"""
        try:
            # check if already running
            if self.is_ollama_running():
                return True
            
            self.update_status("Starting Ollama server...", 0.3)
            
            # start ollama serve in background
            if sys.platform == "win32":
                # on windows, use CREATE_NO_WINDOW flag
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # on linux/mac
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # wait for server to start
            self.update_status("Waiting for Ollama to start...", 0.5)
            for i in range(10):
                time.sleep(1)
                if self.is_ollama_running():
                    self.update_status("Ollama started successfully!", 0.8)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error starting Ollama: {e}")
            return False
    
    def initialize(self):
        """run initialization sequence"""
        try:
            # check if ollama is installed
            self.update_status("Checking Ollama installation...", 0.1)
            if not self.check_ollama_installed():
                result = messagebox.askyesno(
                    "Ollama Not Installed",
                    "Ollama is required but not installed.\n\n"
                    "Would you like to download it now?\n\n"
                    "(This will open the Ollama website in your browser)",
                    icon='warning'
                )
                
                if result:
                    # open ollama download page
                    import webbrowser
                    webbrowser.open('https://ollama.ai/download')
                    messagebox.showinfo(
                        "Installation Instructions",
                        "Please install Ollama and restart this application.\n\n"
                        "After installation:\n"
                        "1. Restart your computer (or terminal)\n"
                        "2. Run this application again"
                    )
                
                self.destroy()
                return False
            
            # try to start ollama
            self.update_status("Checking Ollama status...", 0.2)
            if not self.start_ollama():
                result = messagebox.askyesno(
                    "Ollama Error",
                    "Failed to start Ollama server automatically.\n\n"
                    "Would you like to try starting it manually?",
                    icon='warning'
                )
                
                if result:
                    messagebox.showinfo(
                        "Manual Start Instructions",
                        "Please open a terminal/command prompt and run:\n\n"
                        "    ollama serve\n\n"
                        "Then click OK to continue."
                    )
                    
                    # check again if user started it manually
                    if self.is_ollama_running():
                        self.update_status("Ollama connected!", 0.8)
                        self.update_status("Launching application...", 1.0)
                        time.sleep(0.5)
                        return True
                
                self.destroy()
                return False
            
            self.update_status("Launching application...", 1.0)
            time.sleep(0.5)
            return True
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize: {str(e)}")
            self.destroy()
            return False


class BenchmarkApp(ctk.CTk):
    """main application window for llm benchmarking"""
    
    def __init__(self):
        super().__init__()
        
        # window setup
        self.title("LLM Benchmark Tool")
        self.geometry("1000x750")
        
        # initialize backend components directly
        self.model_manager = ModelManager("http://localhost:11434")
        self.test_runner = TestRunner(self.model_manager)
        self.loader = TestSuiteLoader()
        self.storage = ResultsStorage("benchmark_results.db")
        
        # state variables
        self.downloaded_models = []
        self.available_models = []
        self.is_running = False
        self.current_thread = None
        self.selected_model = None
        self.selected_downloaded_index = None
        self.selected_available_index = None
        
        # setup ui
        self.setup_ui()
        
        # initial model refresh
        self.refresh_models()
    
    def setup_ui(self):
        """create all ui components"""
        
        # header
        header = ctk.CTkLabel(
            self, 
            text="Ollama LLM Benchmark Tool",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=20)
        
        # configuration section
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            config_frame,
            text="Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # test suite path
        suite_frame = ctk.CTkFrame(config_frame)
        suite_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(suite_frame, text="Test Suite:", width=100).pack(side="left", padx=5)
        self.suite_path_entry = ctk.CTkEntry(
            suite_frame, 
            placeholder_text="Select test suite JSON file"
        )
        self.suite_path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(
            suite_frame, 
            text="Browse", 
            width=80,
            command=self.browse_test_suite
        ).pack(side="left", padx=5)
        
        # export path
        export_frame = ctk.CTkFrame(config_frame)
        export_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(export_frame, text="Export Path:", width=100).pack(side="left", padx=5)
        self.export_path_entry = ctk.CTkEntry(
            export_frame,
            placeholder_text="Select export folder"
        )
        self.export_path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(
            export_frame,
            text="Browse",
            width=80,
            command=self.browse_export_path
        ).pack(side="left", padx=5)
        
        # few-shot prompt section
        fewshot_frame = ctk.CTkFrame(config_frame)
        fewshot_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(fewshot_frame, text="Few-Shot CSV:", width=100).pack(side="left", padx=5)
        self.fewshot_path_entry = ctk.CTkEntry(
            fewshot_frame,
            placeholder_text="Select few-shot examples CSV (optional)"
        )
        self.fewshot_path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(
            fewshot_frame,
            text="Browse",
            width=80,
            command=self.browse_fewshot_csv
        ).pack(side="left", padx=5)
        
        self.fewshot_toggle = ctk.CTkSwitch(
            fewshot_frame,
            text="Enable",
            command=self.toggle_fewshot
        )
        self.fewshot_toggle.pack(side="left", padx=5)
        
        # model lists section
        lists_frame = ctk.CTkFrame(self)
        lists_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # downloaded models
        downloaded_frame = ctk.CTkFrame(lists_frame)
        downloaded_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(
            downloaded_frame,
            text="Downloaded Models",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        self.downloaded_listbox = ctk.CTkTextbox(downloaded_frame, height=150)
        self.downloaded_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # available models
        available_frame = ctk.CTkFrame(lists_frame)
        available_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        ctk.CTkLabel(
            available_frame,
            text="Available Models",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        self.available_listbox = ctk.CTkTextbox(available_frame, height=150)
        self.available_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # bind click events for model selection
        self.downloaded_listbox.bind("<Button-1>", self.on_downloaded_click)
        self.available_listbox.bind("<Button-1>", self.on_available_click)
        
        # refresh models button
        refresh_btn_frame = ctk.CTkFrame(self)
        refresh_btn_frame.pack(fill="x", padx=20)
        
        ctk.CTkButton(
            refresh_btn_frame,
            text="Refresh Models",
            command=self.refresh_models
        ).pack(side="right", padx=5, pady=5)
        
        # control section
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        control_inner = ctk.CTkFrame(control_frame)
        control_inner.pack(fill="x", padx=10, pady=10)
        
        # terminate button
        ctk.CTkLabel(control_inner, text="Process Control:").pack(side="left", padx=5)
        self.terminate_btn = ctk.CTkButton(
            control_inner,
            text="TERMINATE",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.terminate_process
        )
        self.terminate_btn.pack(side="left", padx=5)
        
        # separator
        ctk.CTkLabel(control_inner, text="|").pack(side="left", padx=10)
        
        # temperature control
        ctk.CTkLabel(control_inner, text="Temperature:").pack(side="left", padx=5)
        self.temperature_slider = ctk.CTkSlider(
            control_inner,
            from_=0.0,
            to=1.0,
            number_of_steps=10,
            width=150,
            command=self.update_temperature_label
        )
        self.temperature_slider.set(0.7)
        self.temperature_slider.pack(side="left", padx=5)
        
        self.temperature_label = ctk.CTkLabel(
            control_inner,
            text="0.7",
            font=ctk.CTkFont(weight="bold")
        )
        self.temperature_label.pack(side="left", padx=5)
        
        # run benchmark button
        self.run_btn = ctk.CTkButton(
            control_inner,
            text="Run Benchmark",
            fg_color="#27ae60",
            hover_color="#229954",
            command=self.run_benchmark,
            width=150
        )
        self.run_btn.pack(side="right", padx=5)
        
        # progress bar
        self.progress_bar = ctk.CTkProgressBar(control_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # status label
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # terminal/log output section
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            log_frame,
            text="Test Execution Log",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=120,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text.configure(state="disabled")
    
    def update_temperature_label(self, value):
        """update temperature label when slider moves"""
        self.temperature_label.configure(text=f"{value:.1f}")
    
    def browse_test_suite(self):
        """open file dialog to select test suite"""
        filename = filedialog.askopenfilename(
            title="Select Test Suite",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.suite_path_entry.delete(0, "end")
            self.suite_path_entry.insert(0, filename)
            self.update_status(f"Test suite loaded: {Path(filename).name}")
    
    def browse_export_path(self):
        """open directory dialog to select export folder"""
        directory = filedialog.askdirectory(title="Select Export Folder")
        if directory:
            self.export_path_entry.delete(0, "end")
            self.export_path_entry.insert(0, directory)
    
    def browse_fewshot_csv(self):
        """open file dialog to select few-shot csv"""
        filename = filedialog.askopenfilename(
            title="Select Few-Shot Examples CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.fewshot_path_entry.delete(0, "end")
            self.fewshot_path_entry.insert(0, filename)
            self.log_message(f"Few-shot CSV loaded: {Path(filename).name}")
    
    def toggle_fewshot(self):
        """handle few-shot toggle"""
        if self.fewshot_toggle.get():
            self.log_message("Few-shot prompting enabled")
        else:
            self.log_message("Few-shot prompting disabled")
    
    def update_status(self, message, progress=None):
        """update status label and optionally progress bar"""
        self.status_label.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress)
    
    def log_message(self, message):
        """add message to the log terminal"""
        self.log_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def refresh_models(self):
        """fetch models from ollama"""
        self.update_status("Connecting to backend...")
        
        def fetch():
            try:
                if not self.model_manager.test_connection():
                    self.after(0, lambda: messagebox.showerror(
                        "Connection Error",
                        "Could not connect to Ollama. Is it running?"
                    ))
                    self.after(0, lambda: self.update_status("Failed to connect to Ollama"))
                    return
                
                models = self.model_manager.list_models()
                self.downloaded_models = models
                
                # update ui on main thread
                self.after(0, self.update_model_lists)
                self.after(0, lambda: self.update_status("Models refreshed from Ollama."))
            
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh models: {str(e)}"))
                self.after(0, lambda: self.update_status("Failed to refresh models"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_model_lists(self):
        """update the model listboxes"""
        # update downloaded models with highlighting
        self.downloaded_listbox.configure(state="normal")
        self.downloaded_listbox.delete("1.0", "end")
        self.downloaded_listbox.tag_config("selected", background="#1f538d", foreground="white")
        
        for i, model in enumerate(self.downloaded_models):
            start_index = self.downloaded_listbox.index("end-1c")
            self.downloaded_listbox.insert("end", f"📦 {model}\n")
            end_index = self.downloaded_listbox.index("end-1c")
            
            # highlight if selected
            if self.selected_downloaded_index == i:
                self.downloaded_listbox.tag_add("selected", start_index, end_index)
        
        self.downloaded_listbox.configure(state="disabled")
        
        # populate available models
        self.populate_available_models()
    
    def populate_available_models(self):
        """populate available models list with common ollama models"""
        # hardcoded list of available ollama models (matching java gui)
        common_models = [
            # latest qwen3 models
            "qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b",
            
            # gemma 3
            "gemma3:1b", "gemma3:4b",
            
            # deepseek-r1
            "deepseek-r1:1.5b", "deepseek-r1:7b", "deepseek-r1:8b",
            
            # qwen 2.5 & coder
            "qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b",
            "qwen2.5-coder:0.5b", "qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "qwen2.5-coder:7b",
            
            # llama 3 family
            "llama3.2:1b", "llama3.2:3b", "llama3.1:8b", "llama3:8b",
            
            # mistral & variants
            "mistral:7b", "mistral-nemo:12b",
            
            # gemma 2
            "gemma2:2b", "gemma2:9b",
            
            # phi models
            "phi3:3.8b", "phi3.5:3.8b", "phi4-mini:3.8b",
            
            # granite 4
            "granite4:350m", "granite4:1b", "granite4:3b",
            
            # smollm2
            "smollm2:135m", "smollm2:360m", "smollm2:1.7b",
            
            # codellama & coding models
            "codellama:7b", "codegemma:2b", "codegemma:7b", "starcoder2:3b", "starcoder2:7b",
            "deepseek-coder:1.3b", "deepseek-coder:6.7b",
            
            # dolphin
            "dolphin3:8b", "dolphin-mistral:7b", "dolphin-phi:2.7b",
            
            # tinyllama & small models
            "tinyllama:1.1b", "tinydolphin:1.1b",
            
            # other popular models
            "orca-mini:3b", "orca-mini:7b", "openchat:7b", "vicuna:7b",
            "neural-chat:7b", "starling-lm:7b", "yi-coder:1.5b", "yi-coder:9b"
        ]
        
        # filter out already downloaded
        self.available_models = [m for m in common_models if m not in self.downloaded_models]
        
        self.available_listbox.configure(state="normal")
        self.available_listbox.delete("1.0", "end")
        self.available_listbox.tag_config("selected", background="#1f538d", foreground="white")
        
        for i, model in enumerate(self.available_models):
            start_index = self.available_listbox.index("end-1c")
            self.available_listbox.insert("end", f"⬇️ {model}\n")
            end_index = self.available_listbox.index("end-1c")
            
            # highlight if selected
            if self.selected_available_index == i:
                self.available_listbox.tag_add("selected", start_index, end_index)
        
        self.available_listbox.configure(state="disabled")
    
    def on_downloaded_click(self, event):
        """handle click on downloaded model"""
        try:
            # get line number from click position
            index = self.downloaded_listbox.index("@%s,%s" % (event.x, event.y))
            line_num = int(index.split('.')[0])
            
            if line_num <= len(self.downloaded_models):
                self.selected_downloaded_index = line_num - 1
                self.selected_available_index = None
                self.selected_model = self.downloaded_models[line_num - 1]
                self.update_status(f"Selected model: {self.selected_model}")
                self.log_message(f"Selected model: {self.selected_model}")
                self.update_model_lists()
        except:
            pass
    
    def on_available_click(self, event):
        """handle click on available model to download"""
        try:
            index = self.available_listbox.index("@%s,%s" % (event.x, event.y))
            line_num = int(index.split('.')[0])
            
            if line_num <= len(self.available_models):
                model = self.available_models[line_num - 1]
                self.download_model(model)
        except:
            pass
    
    def download_model(self, model_name):
        """download a model from ollama"""
        result = messagebox.askyesno(
            "Download Model",
            f"Download {model_name}? This may take several minutes."
        )
        
        if not result:
            return
        
        self.update_status(f"Downloading {model_name}...", 0)
        self.log_message(f"Starting download: {model_name}")
        self.run_btn.configure(state="disabled")
        
        def download():
            try:
                # stream download progress
                for line in self.model_manager.pull_model_generator(model_name):
                    # update ui periodically
                    self.after(0, lambda: self.update_status(
                        f"Downloading {model_name}...", 0.5
                    ))
                
                self.after(0, lambda: self.log_message(f"Download complete: {model_name}"))
                self.after(0, lambda: messagebox.showinfo(
                    "Download Complete",
                    f"Model {model_name} has been successfully downloaded."
                ))
                self.after(0, self.refresh_models)
                self.after(0, lambda: self.update_status("Download complete", 1.0))
            
            except Exception as e:
                self.after(0, lambda: self.log_message(f"Download failed: {str(e)}"))
                self.after(0, lambda: messagebox.showerror(
                    "Download Error",
                    f"Failed to download model: {str(e)}"
                ))
                self.after(0, lambda: self.update_status("Download failed"))
            
            finally:
                self.after(0, lambda: self.run_btn.configure(state="normal"))
        
        threading.Thread(target=download, daemon=True).start()
    
    def validate_inputs(self):
        """validate benchmark inputs"""
        if not self.selected_model:
            messagebox.showwarning("Validation Error", "Please select a model to benchmark.")
            return False
        
        if not self.suite_path_entry.get():
            messagebox.showwarning("Validation Error", "Please load a test suite first.")
            return False
        
        if not os.path.exists(self.suite_path_entry.get()):
            messagebox.showwarning("Validation Error", "Test suite file does not exist.")
            return False
        
        if not self.export_path_entry.get():
            messagebox.showwarning("Validation Error", "Please specify an export folder.")
            return False
        
        export_dir = self.export_path_entry.get()
        if not os.path.exists(export_dir) or not os.path.isdir(export_dir):
            messagebox.showwarning("Validation Error", "Export path is not a valid directory.")
            return False
        
        return True
    
    def run_benchmark(self):
        """execute the benchmark"""
        if not self.validate_inputs():
            return
        
        if self.is_running:
            messagebox.showwarning("Already Running", "A benchmark is already in progress.")
            return
        
        self.is_running = True
        self.run_btn.configure(state="disabled")
        self.update_status("Starting benchmark...", 0)
        self.log_message("="*50)
        self.log_message("Starting benchmark execution")
        self.log_message(f"Model: {self.selected_model}")
        self.log_message(f"Temperature: {self.temperature_slider.get():.1f}")
        
        temperature = self.temperature_slider.get()
        use_fewshot = self.fewshot_toggle.get()
        fewshot_path = self.fewshot_path_entry.get() if use_fewshot else None
        
        def execute():
            try:
                # load test suite
                self.after(0, lambda: self.update_status("Loading test suite...", 0.1))
                self.after(0, lambda: self.log_message("Loading test suite..."))
                test_cases = self.loader.load_test_suite(self.suite_path_entry.get())
                
                if not test_cases:
                    raise Exception("Test suite is empty or invalid")
                
                self.after(0, lambda: self.log_message(f"Loaded {len(test_cases)} test cases"))
                
                # load and apply few-shot if enabled
                if use_fewshot and fewshot_path and os.path.exists(fewshot_path):
                    self.after(0, lambda: self.log_message("Loading few-shot examples..."))
                    few_shot_examples = self.loader.load_few_shot_from_csv(fewshot_path)
                    if few_shot_examples:
                        test_cases = self.loader.apply_few_shot_to_suite(test_cases, few_shot_examples)
                        self.after(0, lambda: self.log_message(f"Applied {len(few_shot_examples)} few-shot examples"))
                
                # configure model
                config = ModelConfig(name=self.selected_model, temperature=temperature)
                
                # run tests with progress logging
                self.after(0, lambda: self.update_status(
                    f"Testing model: {self.selected_model}...", 0.3
                ))
                self.after(0, lambda: self.log_message(f"Starting test execution..."))
                
                results = []
                for i, test_case in enumerate(test_cases, 1):
                    if not self.is_running:
                        self.after(0, lambda: self.log_message("Benchmark terminated by user"))
                        break
                    
                    self.after(0, lambda idx=i, total=len(test_cases), name=test_case.name: self.log_message(
                        f"Running test {idx}/{total}: {name}"
                    ))
                    
                    result = self.test_runner.run_test(test_case, config, include_few_shot=use_fewshot)
                    results.append(result)
                    
                    status = "✓ PASS" if result.passed else "✗ FAIL"
                    self.after(0, lambda s=status, t=result.response_time: self.log_message(
                        f"  {s} ({t:.2f}s)"
                    ))
                    
                    progress = 0.3 + (0.5 * i / len(test_cases))
                    self.after(0, lambda p=progress: self.progress_bar.set(p))
                
                if not results:
                    raise Exception("No tests were executed")
                
                # calculate statistics
                total = len(results)
                passed = sum(1 for r in results if r.passed)
                failed = total - passed
                total_time = sum(r.response_time for r in results)
                avg_time = total_time / total if total > 0 else 0
                accuracy = (passed / total) * 100 if total > 0 else 0
                
                self.after(0, lambda: self.log_message(f"Tests completed: {passed}/{total} passed"))
                self.after(0, lambda: self.log_message(f"Accuracy: {accuracy:.1f}%"))
                self.after(0, lambda: self.log_message(f"Total time: {total_time:.2f}s"))
                
                # create summary
                summary = TestRunSummary(
                    run_id=generate_run_id(),
                    model_name=self.selected_model,
                    test_suite_name=Path(self.suite_path_entry.get()).name,
                    total_tests=total,
                    passed_tests=passed,
                    failed_tests=failed,
                    total_time=total_time,
                    average_time=avg_time,
                    accuracy=accuracy,
                    timestamp=datetime.now()
                )
                
                # save to database
                self.after(0, lambda: self.update_status("Saving results...", 0.8))
                self.after(0, lambda: self.log_message("Saving results to database..."))
                self.storage.save_test_run(summary, results)
                
                # save as csv
                output_file = self.generate_output_file()
                self.save_as_csv(results, output_file)
                self.after(0, lambda f=output_file.name: self.log_message(f"Results saved to: {f}"))
                
                self.after(0, lambda f=output_file.name: self.update_status(
                    f"Benchmark complete. Saved: {f}", 1.0
                ))
                
                self.after(0, lambda: self.log_message("="*50))
                self.after(0, lambda: self.log_message("Benchmark completed successfully!"))
                
                self.after(0, lambda acc=accuracy, f=output_file.name: messagebox.showinfo(
                    "Success",
                    f"Benchmark for {self.selected_model} completed!\n"
                    f"Accuracy: {acc:.1f}%\n"
                    f"Results saved to {f}"
                ))
            
            except Exception as e:
                self.after(0, lambda err=str(e): self.log_message(f"ERROR: {err}"))
                self.after(0, lambda err=str(e): messagebox.showerror(
                    "Benchmark Error",
                    f"Benchmark failed: {err}"
                ))
                self.after(0, lambda: self.update_status("Benchmark failed"))
            
            finally:
                self.is_running = False
                self.after(0, lambda: self.run_btn.configure(state="normal"))
        
        self.current_thread = threading.Thread(target=execute, daemon=True)
        self.current_thread.start()
    
    def terminate_process(self):
        """terminate current running process"""
        if not self.is_running:
            messagebox.showinfo("No Process", "No benchmark is currently running.")
            return
        
        # note: python threading doesn't support hard termination
        # the benchmark will complete its current test then stop
        self.is_running = False
        self.update_status("Termination requested...", 0)
        self.log_message("Termination requested - will stop after current test")
        messagebox.showinfo("Terminate", "Process termination requested. Will stop after current test.")
    
    def generate_output_file(self):
        """generate output filename with timestamp"""
        safe_model_name = self.selected_model.replace(":", "_").replace("/", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{safe_model_name}_{timestamp}.csv"
        return Path(self.export_path_entry.get()) / filename
    
    def save_as_csv(self, results, output_file):
        """save results to csv file"""
        if not results:
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
            writer.writeheader()
            for result in results:
                writer.writerow(result.to_dict())


def main():
    """entry point for the application"""
    # set appearance mode and color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # show loading window and initialize
    loading = LoadingWindow()
    loading.update()
    
    if not loading.initialize():
        return
    
    # close loading window
    ollama_process = loading.ollama_process
    loading.destroy()
    
    # launch main app
    app = BenchmarkApp()
    
    # cleanup on exit
    def on_closing():
        if ollama_process and ollama_process.poll() is None:
            # only kill if we started it
            try:
                ollama_process.terminate()
            except:
                pass
        app.destroy()
    
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
