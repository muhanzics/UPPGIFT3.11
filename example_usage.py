#!/usr/bin/env python3
"""
Quick example of using the benchmarking system programmatically
(without the CLI)
"""

from src import (
    TestCase, 
    ModelConfig, 
    ModelManager, 
    TestRunner, 
    ResultsStorage,
    generate_run_id,
    TestRunSummary,
    EvaluationType
)


def main():
    # Initialize components
    model_manager = ModelManager("http://localhost:11434")
    test_runner = TestRunner(model_manager)
    storage = ResultsStorage("example_results.db")
    
    # Test connection
    if not model_manager.test_connection():
        print("Cannot connect to Ollama!")
        return
    
    # Create a simple test case
    test_cases = [
        TestCase(
            id="example_001",
            name="Dog detection",
            input_text="I saw a golden retriever at the park.",
            question="Does this text mention a dog?",
            expected_answer=True,
            evaluation_type=EvaluationType.BOOLEAN
        ),
        TestCase(
            id="example_002",
            name="No dog mention",
            input_text="I went to the store to buy groceries.",
            question="Does this text mention a dog?",
            expected_answer=False,
            evaluation_type=EvaluationType.BOOLEAN
        )
    ]
    
    # Configure model (use whatever model you have downloaded)
    model_config = ModelConfig(
        name="qwen2.5:3b",  # Change to your model
        temperature=0.0     # Deterministic responses
    )
    
    # Run tests
    print(f"\nRunning {len(test_cases)} tests against {model_config.name}...")
    results = test_runner.run_test_suite(
        test_cases,
        model_config,
        include_few_shot=False,
        verbose=True
    )
    
    # Calculate summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    total_time = sum(r.response_time for r in results)
    avg_time = total_time / len(results) if results else 0
    accuracy = (passed / len(results) * 100) if results else 0
    
    # Create and save summary
    run_id = generate_run_id()
    summary = TestRunSummary(
        run_id=run_id,
        model_name=model_config.name,
        test_suite_name="example_suite",
        total_tests=len(results),
        passed_tests=passed,
        failed_tests=failed,
        total_time=total_time,
        average_time=avg_time,
        accuracy=accuracy
    )
    
    storage.save_test_run(summary, results)
    
    # Display results
    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Passed: {passed}/{len(results)}")
    print(f"Average time: {avg_time:.2f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
