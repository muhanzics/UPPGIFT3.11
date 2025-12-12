"""
Utility functions for loading and managing test suites.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

from .models import TestCase, EvaluationType


class TestSuiteLoader:
    """Loads and manages test suites from JSON files."""
    
    @staticmethod
    def load_test_suite(file_path: str) -> List[TestCase]:
        """
        Load a test suite from a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of TestCase objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Support both array of tests and object with 'tests' key
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
        Save a test suite to a JSON file.
        
        Args:
            test_cases: List of TestCase objects
            file_path: Path to save to
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
        List all test suite files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of test suite file paths
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
