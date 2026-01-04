# Muhaned Mahdi
# Enes Özbek

"""
test runner - executes test cases against LLM models.
"""

import time
import json
import re
from typing import List, Optional, Any
from datetime import datetime

from .models import TestCase, TestResult, ModelConfig, EvaluationType
from .model_manager import ModelManager


class TestRunner:
    """runs test cases against LLM models and evaluates results."""
    
    def __init__(self, model_manager: ModelManager):
        """
        initialize TestRunner.
        
        args:
            model_manager: ModelManager instance for API calls
        """
        self.model_manager = model_manager
    # creates the prompt that gets sent to the AI model
    def build_prompt(
        self, 
        test_case: TestCase, 
        include_few_shot: bool = True
    ) -> str:
        """
        build the complete prompt for a test case.
        
        args:
            test_case: The test case to build prompt for
            include_few_shot: Whether to include few-shot examples
            
        returns:
            complete formatted prompt
        """
        parts = []
        
        if test_case.system_prompt:
            parts.append(test_case.system_prompt)
            parts.append("")
        
        if include_few_shot and test_case.few_shot_examples: # if the user decides to use few-shot examples to see the differences. 
            parts.append("Examples:")
            for example in test_case.few_shot_examples:
                parts.append(f"Input: {example.get('input', '')}")
                parts.append(f"Output: {example.get('output', '')}")
                parts.append("")
        
        parts.append("Text:")
        parts.append(test_case.input_text)
        parts.append("")
        parts.append("Question:")
        parts.append(test_case.question)
        parts.append("")
        
        # provide specific format instructions based on evaluation type
        if test_case.evaluation_type == EvaluationType.BOOLEAN:
            parts.append("Respond with JSON only in this exact format:")
            parts.append('{"answer": true} or {"answer": false}')
            parts.append("Use only true or false, nothing else.")
        else:
            parts.append("Respond with JSON only in this format:")
            parts.append('{"answer": <your answer>}')
        
        return "\n".join(parts)
    
    # extracts the AIs answer from its raw text response, then handles different formats the model might return
    def parse_response(
        self, 
        response_text: str, 
        evaluation_type: EvaluationType
    ) -> Any:
        """
        parse the model's response to extract the answer.
        
        args:
            response_text: raw response from model
            evaluation_type: type of evaluation to determine parsing
            
        returns:
            parsed answer value
        """
        try:
            # look for json object in the models response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                answer = data.get('answer')
                
                # convert the answer based on what type of evaluation is expected
                if evaluation_type == EvaluationType.BOOLEAN:
                    if isinstance(answer, bool):
                        return answer
                    elif isinstance(answer, str):
                        return answer.lower() in ['true', 'yes', '1']
                    else:
                        return bool(answer)
                else:
                    return answer
            else:
                # no json found, try to extract boolean from plain text if needed
                if evaluation_type == EvaluationType.BOOLEAN:
                    lower_text = response_text.lower()
                    if 'true' in lower_text or 'yes' in lower_text:
                        return True
                    elif 'false' in lower_text or 'no' in lower_text:
                        return False
                
                return response_text.strip()
                
        except json.JSONDecodeError:
            return response_text.strip()
        except Exception as e:
            print(f"Warning: Error parsing response: {e}")
            return response_text.strip()
    
    def evaluate_result(
        self, 
        expected: Any, 
        actual: Any, 
        evaluation_type: EvaluationType
    ) -> bool:
        """
        Evaluate if the actual result matches the expected result.
        
        Args:
            expected: Expected answer
            actual: Actual answer from model
            evaluation_type: How to compare the values
            
        Returns:
            True if test passed, False otherwise
        """
        try:
            if evaluation_type == EvaluationType.BOOLEAN:
                expected_bool = bool(expected) if not isinstance(expected, str) else expected.lower() in ['true', 'yes', '1']
                actual_bool = bool(actual) if not isinstance(actual, str) else actual.lower() in ['true', 'yes', '1']
                return expected_bool == actual_bool
            
            elif evaluation_type == EvaluationType.EXACT_MATCH:
                return str(expected).strip() == str(actual).strip()
            
            elif evaluation_type == EvaluationType.CONTAINS:
                return str(expected).lower() in str(actual).lower()
            
            elif evaluation_type == EvaluationType.REGEX:
                pattern = re.compile(str(expected))
                return pattern.search(str(actual)) is not None
            
            elif evaluation_type == EvaluationType.JSON_FIELD:
                return expected == actual
            
            else:
                return expected == actual
                
        except Exception as e:
            print(f"Warning: Error evaluating result: {e}")
            return False
    
    def run_test(
        self, 
        test_case: TestCase, 
        model_config: ModelConfig,
        include_few_shot: bool = True
    ) -> TestResult:
        """
        Run a single test case against a model.
        
        Args:
            test_case: Test case to run
            model_config: Model configuration
            include_few_shot: Whether to include few-shot examples
            
        Returns:
            TestResult with execution results
        """
        start_time = time.time()
        error = None
        raw_response = ""
        actual_answer = None
        passed = False
        
        try:
            prompt = self.build_prompt(test_case, include_few_shot)
            
            # send the prompt to the AI model and get its response
            raw_response = self.model_manager.generate_response(
                prompt, 
                model_config
            )
            
            if raw_response is None:
                raise Exception("model returned None response")
            
            # extract the actual answer from the AIs response text
            actual_answer = self.parse_response(
                raw_response, 
                test_case.evaluation_type
            )
            
            passed = self.evaluate_result(
                test_case.expected_answer,
                actual_answer,
                test_case.evaluation_type
            )
            
        except Exception as e:
            error = str(e)
            passed = False
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return TestResult(
            test_id=test_case.id,
            test_name=test_case.name,
            model_name=model_config.name,
            expected_answer=test_case.expected_answer,
            actual_answer=actual_answer,
            raw_response=raw_response,
            passed=passed,
            response_time=response_time,
            error=error
        )
    
    def run_test_suite(
        self, 
        test_cases: List[TestCase], 
        model_config: ModelConfig,
        include_few_shot: bool = True,
        verbose: bool = True
    ) -> List[TestResult]:
        """
        Run multiple test cases against a model.
        
        Args:
            test_cases: List of test cases to run
            model_config: Model configuration
            include_few_shot: Whether to include few-shot examples
            verbose: Whether to print progress
            
        Returns:
            List of TestResult objects
        """
        results = []
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"RUNNING {len(test_cases)} TESTS")
            print(f"Model: {model_config.name}")
            print(f"{'='*80}")
        
        for i, test_case in enumerate(test_cases, 1):
            if verbose:
                print(f"\n[{i}/{len(test_cases)}] Running: {test_case.name}")
            
            result = self.run_test(test_case, model_config, include_few_shot)
            results.append(result)
            
            if verbose:
                status = "PASS" if result.passed else "FAIL"
                print(f"  Expected: {result.expected_answer}")
                print(f"  Actual: {result.actual_answer}")
                print(f"  Time: {result.response_time:.2f}s")
                print(f"  Result: {status}")
                
                if result.error:
                    print(f"  Error: {result.error}")
        
        return results
