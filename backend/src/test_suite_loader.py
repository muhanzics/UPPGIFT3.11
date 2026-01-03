# Muhaned Mahdi
# Enes Özbek

"""
Utility functions for loading and managing test suites.
"""

import json
import csv
from typing import List, Dict, Any
from pathlib import Path

from .models import TestCase, EvaluationType


class TestSuiteLoader:
    """loads and manages test suites from json files."""
    
    @staticmethod
    def load_test_suite(file_path: str) -> List[TestCase]:
        """
        load a test suite from a json file.
        
        args:
            file_path: path to json file
            
        returns:
            list of testcase objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                test_data = data
            elif isinstance(data, dict) and 'tests' in data:
                test_data = data['tests']
            else:
                raise ValueError("Invalid test suite format")
            
            test_cases = []
            for item in test_data:
                test_case = TestCase.from_dict(item)
                test_cases.append(test_case)
            
            print(f"Loaded {len(test_cases)} test cases from {file_path}")
            return test_cases
            
        except FileNotFoundError:
            print(f"Test suite file not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in test suite: {e}")
            return []
        except Exception as e:
            print(f"Error loading test suite: {e}")
            return []
    
    @staticmethod
    def save_test_suite(test_cases: List[TestCase], file_path: str):
        """
        save a test suite to a json file.
        
        args:
            test_cases: list of testcase objects
            file_path: path to save to
        """
        try:
            data = {
                "name": Path(file_path).stem,
                "tests": [tc.to_dict() for tc in test_cases]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved {len(test_cases)} test cases to {file_path}")
            
        except Exception as e:
            print(f"Error saving test suite: {e}")
    
    @staticmethod
    def list_test_suites(directory: str = "test_suites") -> List[str]:
        """
        list all test suite files in a directory.
        
        args:
            directory: directory to search
            
        returns:
            list of test suite file paths
        """
        try:
            path = Path(directory)
            if not path.exists():
                return []
            
            json_files = list(path.glob("*.json"))
            return [str(f) for f in json_files]
            
        except Exception as e:
            print(f"Error listing test suites: {e}")
            return []
    
    @staticmethod
    def load_few_shot_from_csv(file_path: str) -> List[Dict[str, str]]:
        """
        load few-shot examples from a csv file.
        
        expected csv format:
        input,output
        "example input text","expected output"
        
        args:
            file_path: path to csv file
            
        returns:
            list of few-shot example dictionaries
        """
        try:
            examples = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'input' in row and 'output' in row:
                        examples.append({
                            'input': row['input'],
                            'output': row['output']
                        })
            
            print(f"Loaded {len(examples)} few-shot examples from {file_path}")
            return examples
            
        except FileNotFoundError:
            print(f"Few-shot CSV file not found: {file_path}")
            return []
        except Exception as e:
            print(f"Error loading few-shot examples: {e}")
            return []
    
    @staticmethod
    def apply_few_shot_to_suite(
        test_cases: List[TestCase], 
        few_shot_examples: List[Dict[str, str]]
    ) -> List[TestCase]:
        """
        apply few-shot examples to all test cases in a suite.
        
        args:
            test_cases: list of testcase objects
            few_shot_examples: list of few-shot example dictionaries
            
        returns:
            updated list of testcase objects with few-shot examples
        """
        for test_case in test_cases:
            test_case.few_shot_examples = few_shot_examples
        
        print(f"Applied {len(few_shot_examples)} few-shot examples to {len(test_cases)} tests")
        return test_cases
