"""
LLM Benchmarking System

A modular system for benchmarking different LLMs against custom test suites.
Tests models on various tasks and tracks accuracy, response time, and other metrics.
"""

from .model_manager import ModelManager
from .test_runner import TestRunner
from .results_storage import ResultsStorage, generate_run_id
from .test_suite_loader import TestSuiteLoader
from .cli import BenchmarkCLI

__version__ = "0.1.0"

__all__ = [
    "TestCase",
    "TestResult",
    "ModelConfig",
    "TestRunSummary",
    "EvaluationType",
    "ModelManager",
    "TestRunner",
    "ResultsStorage",
    "generate_run_id",
    "TestSuiteLoader",
    "BenchmarkCLI",
]
