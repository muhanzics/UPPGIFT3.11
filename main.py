#!/usr/bin/env python3
"""
LLM Benchmarking System - Main Entry Point

A tool for benchmarking different LLMs against custom test suites.
Compare models on accuracy, speed, and performance across different tasks.
"""

import sys
from src.cli import BenchmarkCLI


def main():
    """Main entry point for the benchmarking system."""
    # Initialize CLI with default settings
    # These can be changed via environment variables or config file in the future
    cli = BenchmarkCLI(
        ollama_url="http://localhost:11434",
        db_path="benchmark_results.db"
    )
    
    # Run the interactive CLI
    cli.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
