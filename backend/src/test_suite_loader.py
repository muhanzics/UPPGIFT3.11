# Muhaned Mahdi
# Enes Özbek

"""
Utility functions for loading and managing test suites.
"""

import json
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
