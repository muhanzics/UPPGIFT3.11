# Muhaned Mahdi
# Enes Özbek

"""
data models for LLM benchmarking system.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class EvaluationType(Enum):
    """types of evaluation methods for test cases."""
    BOOLEAN = "boolean"
    EXACT_MATCH = "exact_match"
    CONTAINS = "contains"
    REGEX = "regex"         
    JSON_FIELD = "json_field"  


@dataclass
class TestCase:
    """
    represents a single test case for benchmarking an LLM.
    
    attributes:
        id: unique identifier for the test
        name: human-readable test name
        input_text: text input to send to the model
        question: question/instruction for the model
        expected_answer: expected response from the model
        evaluation_type: how to evaluate the response
        system_prompt: optional custom system prompt
        few_shot_examples: optional list of example q&a pairs
        metadata: additional test metadata
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
        """convert to dictionary for json serialization."""
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
        """create testcase from dictionary."""
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
    configuration for an LLM model.
    
    attributes:
        name: model name (e.g., "qwen3:4b-instruct")
        temperature: sampling temperature (0.0-1.0)
        top_p: nucleus sampling parameter
        top_k: top-k sampling parameter
        num_ctx: context window size
        other_params: additional ollama parameters
    """
    name: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    num_ctx: Optional[int] = None
    other_params: Dict[str, Any] = field(default_factory=dict)
    
    # converts AI parameters (temperature, top_p, etc.) to the format ollama API expects
    def to_ollama_options(self) -> Dict[str, Any]:
        """convert to ollama api options format."""
        options = {}
        if self.temperature is not None:  # controls randomness/creativity of responses (0.0 = deterministic, 1.0 = creative)
            options["temperature"] = self.temperature
        if self.top_p is not None:  # nucleus sampling parameter
            options["top_p"] = self.top_p
        if self.top_k is not None:  # top-k sampling parameter
            options["top_k"] = self.top_k
        if self.num_ctx is not None:  # context window size
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
