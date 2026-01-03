# Muhaned Mahdi
# Enes Özbek

"""
Results storage using SQLite database.
"""

import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .models import TestResult, TestRunSummary


class ResultsStorage:
    """manages storage and retrieval of test results in sqlite."""
    
    def __init__(self, db_path: str = "benchmark_results.db"):
        """
        initialize resultsstorage.
        
        args:
            db_path: path to sqlite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                test_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                expected_answer TEXT,
                actual_answer TEXT,
                raw_response TEXT,
                passed INTEGER NOT NULL,
                response_time REAL NOT NULL,
                timestamp TEXT NOT NULL,
                error TEXT,
                FOREIGN KEY (run_id) REFERENCES test_runs(run_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                model_name TEXT NOT NULL,
                test_suite_name TEXT NOT NULL,
                total_tests INTEGER NOT NULL,
                passed_tests INTEGER NOT NULL,
                failed_tests INTEGER NOT NULL,
                total_time REAL NOT NULL,
                average_time REAL NOT NULL,
                accuracy REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_results_run_id 
            ON test_results(run_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_results_model 
            ON test_results(model_name)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_runs_model 
            ON test_runs(model_name)
        ''')
        
        conn.commit()
        conn.close()
    
    def save_test_run(
        self, 
        summary: TestRunSummary, 
        results: List[TestResult]
    ):
        """
        save a complete test run with all results.
        
        args:
            summary: test run summary
            results: list of individual test results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO test_runs (
                    run_id, model_name, test_suite_name, total_tests,
                    passed_tests, failed_tests, total_time, average_time,
                    accuracy, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary.run_id,
                summary.model_name,
                summary.test_suite_name,
                summary.total_tests,
                summary.passed_tests,
                summary.failed_tests,
                summary.total_time,
                summary.average_time,
                summary.accuracy,
                summary.timestamp.isoformat()
            ))
            
            for result in results:
                cursor.execute('''
                    INSERT INTO test_results (
                        run_id, test_id, test_name, model_name,
                        expected_answer, actual_answer, raw_response,
                        passed, response_time, timestamp, error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    summary.run_id,
                    result.test_id,
                    result.test_name,
                    result.model_name,
                    str(result.expected_answer),
                    str(result.actual_answer),
                    result.raw_response,
                    1 if result.passed else 0,
                    result.response_time,
                    result.timestamp.isoformat(),
                    result.error
                ))
            
            conn.commit()
            print(f"Saved test run {summary.run_id} to database")
            
        except Exception as e:
            conn.rollback()
            print(f"Error saving test run: {e}")
        finally:
            conn.close()
    
    def get_test_runs(
        self, 
        model_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get test run summaries.
        
        Args:
            model_name: Filter by model name (optional)
            limit: Limit number of results (optional)
            
        Returns:
            List of test run summary dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT run_id, model_name, test_suite_name, total_tests,
                   passed_tests, failed_tests, total_time, average_time,
                   accuracy, timestamp
            FROM test_runs
        '''
        params = []
        
        if model_name:
            query += ' WHERE model_name = ?'
            params.append(model_name)
        
        query += ' ORDER BY timestamp DESC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'run_id': row[0],
                'model_name': row[1],
                'test_suite_name': row[2],
                'total_tests': row[3],
                'passed_tests': row[4],
                'failed_tests': row[5],
                'total_time': row[6],
                'average_time': row[7],
                'accuracy': row[8],
                'timestamp': row[9]
            })
        
        return results
    
    def get_test_results(
        self, 
        run_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get individual test results for a run.
        
        Args:
            run_id: Test run ID
            
        Returns:
            List of test result dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_id, test_name, model_name, expected_answer,
                   actual_answer, raw_response, passed, response_time,
                   timestamp, error
            FROM test_results
            WHERE run_id = ?
            ORDER BY id
        ''', (run_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'test_id': row[0],
                'test_name': row[1],
                'model_name': row[2],
                'expected_answer': row[3],
                'actual_answer': row[4],
                'raw_response': row[5],
                'passed': bool(row[6]),
                'response_time': row[7],
                'timestamp': row[8],
                'error': row[9]
            })
        
        return results
    
    def get_model_statistics(
        self, 
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregate statistics for a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Statistics dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                SUM(total_tests) as total_tests,
                SUM(passed_tests) as total_passed,
                AVG(accuracy) as avg_accuracy,
                AVG(average_time) as avg_response_time,
                MIN(average_time) as min_response_time,
                MAX(average_time) as max_response_time
            FROM test_runs
            WHERE model_name = ?
        ''', (model_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            return {
                'model_name': model_name,
                'total_runs': row[0],
                'total_tests': row[1],
                'total_passed': row[2],
                'avg_accuracy': row[3],
                'avg_response_time': row[4],
                'min_response_time': row[5],
                'max_response_time': row[6]
            }
        
        return None
    
    def clear_all_results(self):
        """Clear all test results from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM test_results')
        cursor.execute('DELETE FROM test_runs')
        
        conn.commit()
        conn.close()
        
        print("Database cleared successfully")
    
    def display_results_table(
        self, 
        run_id: Optional[str] = None,
        limit: int = 20
    ):
        """
        Display test results in a formatted table.
        
        Args:
            run_id: Specific run ID to display (optional)
            limit: Maximum number of results to show
        """
        if run_id:
            results = self.get_test_results(run_id)
            title = f"TEST RESULTS FOR RUN: {run_id}"
        else:
            runs = self.get_test_runs(limit=1)
            if not runs:
                print("No test results found in database.")
                return
            
            run_id = runs[0]['run_id']
            results = self.get_test_results(run_id)
            title = f"LATEST TEST RESULTS: {run_id}"
        
        if not results:
            print("No test results found.")
            return
        
        print(f"\n{'='*150}")
        print(title)
        print(f"{'='*150}")
        
        header = f"{'#':<4} {'Test Name':<30} {'Expected':<15} {'Actual':<15} {'Time':<8} {'Status':<8}"
        print(header)
        print("-" * 150)
        
        for i, result in enumerate(results[:limit], 1):
            test_name = (result['test_name'][:27] + "...") if len(result['test_name']) > 30 else result['test_name']
            expected = str(result['expected_answer'])[:15]
            actual = str(result['actual_answer'])[:15]
            time_str = f"{result['response_time']:.2f}s"
            status = "PASS" if result['passed'] else "✗ FAIL"
            
            row = f"{i:<4} {test_name:<30} {expected:<15} {actual:<15} {time_str:<8} {status:<8}"
            print(row)
        
        if len(results) > limit:
            print(f"\n... ({len(results) - limit} more results not shown)")
    
    def display_summary_stats(
        self, 
        run_id: Optional[str] = None
    ):
        """
        Display summary statistics.
        
        Args:
            run_id: Specific run ID (optional, defaults to latest)
        """
        if run_id:
            runs = [r for r in self.get_test_runs() if r['run_id'] == run_id]
            if not runs:
                print(f"No run found with ID: {run_id}")
                return
            run = runs[0]
        else:
            runs = self.get_test_runs(limit=1)
            if not runs:
                print("No test runs found in database.")
                return
            run = runs[0]
        
        print(f"\n{'='*60}")
        print("SUMMARY STATISTICS")
        print(f"{'='*60}")
        print(f"Run ID: {run['run_id']}")
        print(f"Model: {run['model_name']}")
        print(f"Test Suite: {run['test_suite_name']}")
        print(f"Timestamp: {run['timestamp']}")
        print(f"")
        print(f"Total Tests: {run['total_tests']}")
        print(f"Passed: {run['passed_tests']} ({run['accuracy']:.1f}%)")
        print(f"Failed: {run['failed_tests']}")
        print(f"")
        print(f"TIMING:")
        print(f"Total Time: {run['total_time']:.1f}s")
        print(f"Average Time per Test: {run['average_time']:.2f}s")
        print(f"{'='*60}")


def generate_run_id() -> str:
    """Generate a unique run ID."""
    return f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
