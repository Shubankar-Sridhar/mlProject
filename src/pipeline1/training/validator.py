"""Model validation utilities."""

from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ModelValidator:
    """Validate model on various test scenarios."""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
    
    def run_validation_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run complete validation suite."""
        results = {
            'overall': {'pass': True, 'tests': 0, 'passed': 0, 'failed': 0},
            'categories': {},
            'errors': []
        }
        
        # Group test cases by category
        categories = {}
        for test in test_cases:
            category = test.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(test)
        
        # Run tests by category
        for category, tests in categories.items():
            category_results = self._run_category_tests(category, tests)
            results['categories'][category] = category_results
            results['overall']['tests'] += category_results['total']
            results['overall']['passed'] += category_results['passed']
            results['overall']['failed'] += category_results['failed']
            results['errors'].extend(category_results.get('errors', []))
        
        results['overall']['pass'] = results['overall']['failed'] == 0
        return results
    
    def _run_category_tests(self, category: str, tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run tests for a category."""
        results = {
            'category': category,
            'total': len(tests),
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        for test in tests:
            try:
                if self._run_single_test(test):
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': test.get('name', 'Unnamed'),
                        'question': test.get('question', '')[:100]
                    })
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'test': test.get('name', 'Unnamed'),
                    'error': str(e)
                })
        
        return results
    
    def _run_single_test(self, test: Dict[str, Any]) -> bool:
        """Run a single test case."""
        question = test.get('question', '')
        expected = test.get('expected', '')
        
        generated = self.evaluator.generate_sql(question)
        
        # Check if generated SQL is valid
        if not self.evaluator._is_valid_sql(generated):
            return False
        
        # Check if SQL contains expected elements
        expected_elements = test.get('expected_elements', [])
        for element in expected_elements:
            if element.upper() not in generated.upper():
                return False
        
        # Check business rules
        business_rules = test.get('business_rules', [])
        for rule in business_rules:
            if rule not in generated.lower():
                return False
        
        # Check for forbidden elements
        forbidden = test.get('forbidden', [])
        for word in forbidden:
            if word.lower() in generated.lower():
                return False
        
        return True