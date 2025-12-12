"""
Core data models for LLM benchmarking system.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class EvaluationType(Enum):
    """Types of evaluation methods for test cases."""
    BOOLEAN = "boolean"              # True/False comparison
    EXACT_MATCH = "exact_match"      # Exact string match
    CONTAINS = "contains"            # Check if response contains keyword
    REGEX = "regex"                  # Regex pattern matching
    JSON_FIELD = "json_field"        # Compare specific JSON field


@dataclass
class TestCase:
    """
    Represents a single test case for benchmarking an LLM.
    
    Attributes:
        id: Unique identifier for the test
        name: Human-readable test name
        input_text: Text input to send to the model
        question: Question/instruction for the model
        expected_answer: Expected response from the model
        evaluation_type: How to evaluate the response
        system_prompt: Optional custom system prompt
        few_shot_examples: Optional list of example Q&A pairs
        metadata: Additional test metadata
    """
    id: str
    name: str
    input_text: str
    question: str
    expected_answer: Any
    evaluation_type: EvaluationType = EvaluationType.BOOLEAN
    system_prompt: Optional[str] = None
    few_shot_examples: Optional[List[Dict[str, str]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "input_text": self.input_text,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "evaluation_type": self.evaluation_type.value,
            "system_prompt": self.system_prompt,
            "few_shot_examples": self.few_shot_examples,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Create TestCase from dictionary."""
        eval_type = data.get("evaluation_type", "boolean")
        if isinstance(eval_type, str):
            eval_type = EvaluationType(eval_type)
        
        return cls(
            id=data["id"],
            name=data["name"],
            input_text=data["input_text"],
            question=data["question"],
            expected_answer=data["expected_answer"],
            evaluation_type=eval_type,
            system_prompt=data.get("system_prompt"),
            few_shot_examples=data.get("few_shot_examples"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ModelConfig:
    """
    Configuration for an LLM model.
    
    Attributes:
        name: Model name (e.g., "qwen3:4b-instruct")
        temperature: Sampling temperature (0.0-1.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        num_ctx: Context window size
        other_params: Additional Ollama parameters
    """
    name: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    num_ctx: Optional[int] = None
    other_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_ollama_options(self) -> Dict[str, Any]:
        """Convert to Ollama API options format."""
        options = {}
        if self.temperature is not None:
            options["temperature"] = self.temperature
        if self.top_p is not None:
            options["top_p"] = self.top_p
        if self.top_k is not None:
            options["top_k"] = self.top_k
        if self.num_ctx is not None:
            options["num_ctx"] = self.num_ctx
        options.update(self.other_params)
        return options


@dataclass
class TestResult:
    """
    Results from running a single test case.
    
    Attributes:
        test_id: ID of the test case
        test_name: Name of the test case
        model_name: Model that was tested
        expected_answer: What was expected
        actual_answer: What the model returned
        raw_response: Full raw response from model
        passed: Whether the test passed
        response_time: Time taken for model response (seconds)
        timestamp: When the test was run
        error: Error message if test failed to execute
    """
    test_id: str
    test_name: str
    model_name: str
    expected_answer: Any
    actual_answer: Any
    raw_response: str
    passed: bool
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "model_name": self.model_name,
            "expected_answer": self.expected_answer,
            "actual_answer": self.actual_answer,
            "raw_response": self.raw_response,
            "passed": self.passed,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error
        }


@dataclass
class TestRunSummary:
    """
    Summary statistics for a test run.
    
    Attributes:
        run_id: Unique run identifier
        model_name: Model that was tested
        test_suite_name: Name of test suite
        total_tests: Total number of tests
        passed_tests: Number of passing tests
        failed_tests: Number of failing tests
        total_time: Total execution time
        average_time: Average time per test
        accuracy: Percentage of tests passed
        timestamp: When the run started
    """
    run_id: str
    model_name: str
    test_suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_time: float
    average_time: float
    accuracy: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "run_id": self.run_id,
            "model_name": self.model_name,
            "test_suite_name": self.test_suite_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "total_time": self.total_time,
            "average_time": self.average_time,
            "accuracy": self.accuracy,
            "timestamp": self.timestamp.isoformat()
        }
