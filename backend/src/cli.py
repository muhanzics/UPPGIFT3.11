"""
Command-line interface for LLM benchmarking system.
"""

import sys
from typing import List, Optional
from pathlib import Path

from .models import TestCase, ModelConfig, TestRunSummary
from .model_manager import ModelManager
from .test_runner import TestRunner
from .results_storage import ResultsStorage, generate_run_id
from .test_suite_loader import TestSuiteLoader


class BenchmarkCLI:
    """Interactive CLI for running LLM benchmarks."""
    
    def __init__(
        self, 
        ollama_url: str = "http://localhost:11434",
        db_path: str = "benchmark_results.db"
    ):
        """
        Initialize the CLI.
        
        Args:
            ollama_url: Ollama API URL
            db_path: Path to results database
        """
        self.model_manager = ModelManager(ollama_url)
        self.test_runner = TestRunner(self.model_manager)
        self.storage = ResultsStorage(db_path)
        self.loader = TestSuiteLoader()
        
        self.current_test_cases: List[TestCase] = []
        self.current_suite_name: str = ""
    
    def run(self):
        """Run the interactive CLI."""
        print("\n" + "="*60)
        print("LLM BENCHMARKING SYSTEM")
        print("="*60)
        
        # Test Ollama connection
        if not self.model_manager.test_connection():
            print("\n✗ Cannot connect to Ollama. Please ensure Ollama is running.")
            print("  Start Ollama and try again.")
            return
        
        # Main menu loop
        self.main_menu()
    
    def main_menu(self):
        """Display and handle main menu."""
        while True:
            print(f"\n{'='*60}")
            print("MAIN MENU")
            print(f"{'='*60}")
            print("1. Load test suite")
            print("2. Run tests")
            print("3. View results")
            print("4. List available models")
            print("5. Clear database")
            print("6. Exit")
            
            if self.current_test_cases:
                print(f"\nCurrent suite: {self.current_suite_name} ({len(self.current_test_cases)} tests)")
            
            try:
                choice = input("\nEnter your choice (1-6): ").strip()
                
                if choice == "1":
                    self.load_test_suite_menu()
                elif choice == "2":
                    self.run_tests_menu()
                elif choice == "3":
                    self.view_results_menu()
                elif choice == "4":
                    self.list_models()
                elif choice == "5":
                    self.clear_database()
                elif choice == "6":
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def load_test_suite_menu(self):
        """Menu for loading test suites."""
        print(f"\n{'='*60}")
        print("LOAD TEST SUITE")
        print(f"{'='*60}")
        
        # List available test suites
        suites = self.loader.list_test_suites()
        
        if not suites:
            print("No test suites found in 'test_suites/' directory.")
            file_path = input("\nEnter path to test suite JSON file (or press Enter to cancel): ").strip()
            if not file_path:
                return
        else:
            print("Available test suites:")
            for i, suite in enumerate(suites, 1):
                print(f"{i}. {suite}")
            
            print(f"{len(suites) + 1}. Enter custom path")
            
            choice = input(f"\nSelect test suite (1-{len(suites) + 1}): ").strip()
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(suites):
                    file_path = suites[idx]
                elif idx == len(suites):
                    file_path = input("Enter path to test suite JSON file: ").strip()
                else:
                    print("Invalid selection.")
                    return
            except ValueError:
                print("Invalid input.")
                return
        
        # Load the test suite
        test_cases = self.loader.load_test_suite(file_path)
        
        if test_cases:
            self.current_test_cases = test_cases
            self.current_suite_name = Path(file_path).stem
            print(f"\n✓ Loaded test suite: {self.current_suite_name}")
            print(f"  Total tests: {len(test_cases)}")
    
    def run_tests_menu(self):
        """Menu for running tests."""
        if not self.current_test_cases:
            print("\n✗ No test suite loaded. Please load a test suite first.")
            return
        
        print(f"\n{'='*60}")
        print("RUN TESTS")
        print(f"{'='*60}")
        print(f"Test Suite: {self.current_suite_name}")
        print(f"Total Tests: {len(self.current_test_cases)}")
        
        # Select model
        models = self.model_manager.list_models()
        
        if not models:
            print("\n✗ No models available. Please download a model using Ollama first.")
            return
        
        print("\nAvailable models:")
        for i, model in enumerate(models, 1):
            print(f"{i}. {model}")
        
        try:
            choice = input(f"\nSelect model (1-{len(models)}): ").strip()
            idx = int(choice) - 1
            
            if not (0 <= idx < len(models)):
                print("Invalid selection.")
                return
            
            model_name = models[idx]
            
        except ValueError:
            print("Invalid input.")
            return
        
        # Ask about few-shot examples
        include_few_shot = input("\nInclude few-shot examples? (Y/n): ").strip().lower() != 'n'
        
        # Create model config
        model_config = ModelConfig(name=model_name)
        
        # Ask about temperature (optional)
        temp_input = input("\nSet temperature (0.0-1.0, or press Enter for default): ").strip()
        if temp_input:
            try:
                model_config.temperature = float(temp_input)
            except ValueError:
                print("Invalid temperature, using default")
        
        print(f"\n{'='*60}")
        print("STARTING TEST RUN")
        print(f"{'='*60}")
        print(f"Model: {model_name}")
        print(f"Test Suite: {self.current_suite_name}")
        print(f"Total Tests: {len(self.current_test_cases)}")
        print(f"Few-shot: {'Yes' if include_few_shot else 'No'}")
        if model_config.temperature is not None:
            print(f"Temperature: {model_config.temperature}")
        print(f"{'='*60}")
        
        confirm = input("\nProceed? (Y/n): ").strip().lower()
        if confirm == 'n':
            print("Cancelled.")
            return
        
        # Run tests
        results = self.test_runner.run_test_suite(
            self.current_test_cases,
            model_config,
            include_few_shot=include_few_shot,
            verbose=True
        )
        
        # Calculate summary
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_time = sum(r.response_time for r in results)
        avg_time = total_time / len(results) if results else 0
        accuracy = (passed / len(results) * 100) if results else 0
        
        # Create summary
        run_id = generate_run_id()
        summary = TestRunSummary(
            run_id=run_id,
            model_name=model_name,
            test_suite_name=self.current_suite_name,
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            total_time=total_time,
            average_time=avg_time,
            accuracy=accuracy
        )
        
        # Save to database
        self.storage.save_test_run(summary, results)
        
        # Display results
        print(f"\n{'='*60}")
        print("TEST RUN COMPLETE")
        print(f"{'='*60}")
        print(f"Run ID: {run_id}")
        print(f"Passed: {passed}/{len(results)} ({accuracy:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Total Time: {total_time:.1f}s")
        print(f"Average Time: {avg_time:.2f}s")
        print(f"{'='*60}")
        
        # Ask to view detailed results
        view = input("\nView detailed results? (y/N): ").strip().lower()
        if view == 'y':
            self.storage.display_results_table(run_id)
    
    def view_results_menu(self):
        """Menu for viewing results."""
        print(f"\n{'='*60}")
        print("VIEW RESULTS")
        print(f"{'='*60}")
        print("1. View latest run")
        print("2. View specific run")
        print("3. View all runs")
        print("4. View model statistics")
        print("5. Back")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            self.storage.display_summary_stats()
            self.storage.display_results_table()
        elif choice == "2":
            run_id = input("Enter run ID: ").strip()
            self.storage.display_summary_stats(run_id)
            self.storage.display_results_table(run_id)
        elif choice == "3":
            runs = self.storage.get_test_runs()
            if not runs:
                print("No test runs found.")
                return
            
            print(f"\n{'='*100}")
            print("ALL TEST RUNS")
            print(f"{'='*100}")
            print(f"{'#':<4} {'Run ID':<30} {'Model':<20} {'Tests':<8} {'Accuracy':<10} {'Time':<10}")
            print("-" * 100)
            
            for i, run in enumerate(runs, 1):
                run_id_short = run['run_id'][:27] + "..." if len(run['run_id']) > 30 else run['run_id']
                model_short = run['model_name'][:17] + "..." if len(run['model_name']) > 20 else run['model_name']
                tests = f"{run['passed_tests']}/{run['total_tests']}"
                accuracy = f"{run['accuracy']:.1f}%"
                time_str = f"{run['total_time']:.1f}s"
                
                print(f"{i:<4} {run_id_short:<30} {model_short:<20} {tests:<8} {accuracy:<10} {time_str:<10}")
        elif choice == "4":
            models = self.model_manager.list_models()
            
            if not models:
                print("No models found.")
                return
            
            print("\nAvailable models:")
            for i, model in enumerate(models, 1):
                print(f"{i}. {model}")
            
            try:
                idx = int(input(f"\nSelect model (1-{len(models)}): ").strip()) - 1
                if 0 <= idx < len(models):
                    stats = self.storage.get_model_statistics(models[idx])
                    if stats:
                        print(f"\n{'='*60}")
                        print(f"MODEL STATISTICS: {stats['model_name']}")
                        print(f"{'='*60}")
                        print(f"Total Runs: {stats['total_runs']}")
                        print(f"Total Tests: {stats['total_tests']}")
                        print(f"Total Passed: {stats['total_passed']}")
                        print(f"Average Accuracy: {stats['avg_accuracy']:.1f}%")
                        print(f"Average Response Time: {stats['avg_response_time']:.2f}s")
                        print(f"Min Response Time: {stats['min_response_time']:.2f}s")
                        print(f"Max Response Time: {stats['max_response_time']:.2f}s")
                        print(f"{'='*60}")
                    else:
                        print("No statistics available for this model.")
            except (ValueError, IndexError):
                print("Invalid selection.")
        elif choice == "5":
            return
    
    def list_models(self):
        """List all available models."""
        print(f"\n{'='*60}")
        print("AVAILABLE MODELS")
        print(f"{'='*60}")
        
        models = self.model_manager.list_models()
        
        if not models:
            print("No models found.")
            print("\nTo download models, use Ollama CLI:")
            print("  ollama pull <model-name>")
            print("\nExample models:")
            print("  ollama pull llama2")
            print("  ollama pull qwen2.5:3b")
            print("  ollama pull mistral")
        else:
            for i, model in enumerate(models, 1):
                print(f"{i}. {model}")
        
        print(f"\nTotal: {len(models)} model(s)")
    
    def clear_database(self):
        """Clear all results from database."""
        print(f"\n{'='*60}")
        print("CLEAR DATABASE")
        print(f"{'='*60}")
        print("⚠️  WARNING: This will delete all test results!")
        
        confirm = input("\nAre you sure? (yes/no): ").strip().lower()
        if confirm == "yes":
            self.storage.clear_all_results()
        else:
            print("Cancelled.")
