"""Model evaluation utilities."""

import json
import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate model performance on test dataset."""
    
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
    
    def evaluate(self, test_dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate model on test dataset."""
        results = {
            'total': len(test_dataset),
            'correct': 0,
            'incorrect': 0,
            'errors': [],
            'metrics': {}
        }
        
        for i, example in enumerate(test_dataset):
            question = example.get('input', {}).get('question', '')
            expected_sql = example.get('output', {}).get('sql', '')
            
            # Generate SQL
            try:
                generated_sql = self.generate_sql(question)
                if self._compare_sql(generated_sql, expected_sql):
                    results['correct'] += 1
                else:
                    results['incorrect'] += 1
                    results['errors'].append({
                        'index': i,
                        'question': question[:100],
                        'expected': expected_sql[:100],
                        'generated': generated_sql[:100]
                    })
            except Exception as e:
                results['incorrect'] += 1
                results['errors'].append({
                    'index': i,
                    'question': question[:100],
                    'error': str(e)
                })
        
        results['accuracy'] = results['correct'] / results['total'] if results['total'] > 0 else 0
        return results
    
    def generate_sql(self, question: str) -> str:
        """Generate SQL from question using model."""
        prompt = f"<|user|>\n{question}\n<|assistant|>\n"
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.1,
            do_sample=True,
            top_p=0.9
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract SQL
        sql_pattern = r'```sql\s*(.+?)\s*```'
        matches = re.findall(sql_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Try to find SQL without code block
        sql_start = response.find('SELECT')
        if sql_start != -1:
            return response[sql_start:].strip()
        
        return response.strip()
    
    def _compare_sql(self, generated: str, expected: str) -> bool:
        """Compare two SQL queries."""
        # Normalize
        generated = self._normalize_sql(generated)
        expected = self._normalize_sql(expected)
        
        return generated == expected
    
    def _normalize_sql(self, sql: str) -> str:
        """Normalize SQL for comparison."""
        # Remove extra whitespace
        sql = ' '.join(sql.split())
        
        # Uppercase keywords
        keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'GROUP BY', 'ORDER BY', 'LIMIT']
        for kw in keywords:
            sql = sql.replace(kw.lower(), kw)
        
        return sql.strip()
    
    def compute_metrics(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute detailed metrics."""
        metrics = {
            'total': len(predictions),
            'valid_sql': 0,
            'invalid_sql': 0,
            'avg_tokens': 0,
            'types': {}
        }
        
        for pred in predictions:
            sql = pred.get('sql', '')
            if self._is_valid_sql(sql):
                metrics['valid_sql'] += 1
            else:
                metrics['invalid_sql'] += 1
            
            metrics['avg_tokens'] += len(sql.split())
            
            # Track query types
            query_type = self._detect_query_type(sql)
            metrics['types'][query_type] = metrics['types'].get(query_type, 0) + 1
        
        metrics['avg_tokens'] /= len(predictions) if predictions else 1
        metrics['valid_ratio'] = metrics['valid_sql'] / metrics['total'] if metrics['total'] > 0 else 0
        
        return metrics
    
    def _is_valid_sql(self, sql: str) -> bool:
        """Check if SQL is valid."""
        if not sql or len(sql.strip()) < 3:
            return False
        
        sql_upper = sql.upper()
        if not sql_upper.lstrip().startswith('SELECT'):
            return False
        
        dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE']
        for op in dangerous:
            if op in sql_upper:
                return False
        
        return True
    
    def _detect_query_type(self, sql: str) -> str:
        """Detect query type."""
        sql_upper = sql.upper()
        
        if 'JOIN' in sql_upper:
            return 'join'
        if 'GROUP BY' in sql_upper:
            return 'aggregation'
        if 'WHERE' in sql_upper:
            return 'filter'
        if 'ORDER BY' in sql_upper:
            return 'ordered'
        return 'simple'