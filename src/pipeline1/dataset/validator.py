"""Validate training dataset examples."""

import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DatasetValidator:
    """Validate dataset examples."""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.table_names = self._extract_table_names()
        self.column_names = self._extract_column_names()
    
    def _extract_table_names(self) -> List[str]:
        """Extract all table names from schema."""
        tables = []
        for schema in self.schema.get('schemas', []):
            for table in schema['tables']:
                tables.append(table['name'])
        return tables
    
    def _extract_column_names(self) -> Dict[str, List[str]]:
        """Extract column names for each table."""
        columns = {}
        for schema in self.schema.get('schemas', []):
            for table in schema['tables']:
                columns[table['name']] = [c['name'] for c in table['columns']]
        return columns
    
    def validate_example(self, example: Dict[str, Any]) -> bool:
        """Validate a single example."""
        try:
            # Check structure
            if 'instruction' not in example:
                return False
            if 'input' not in example or 'question' not in example['input']:
                return False
            if 'output' not in example or 'sql' not in example['output']:
                return False
            
            question = example['input']['question']
            sql = example['output']['sql']
            
            # Validate SQL
            if not self._validate_sql(sql):
                return False
            
            # Validate question
            if not self._validate_question(question):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    
    def _validate_sql(self, sql: str) -> bool:
        """Validate SQL query."""
        if not sql or len(sql.strip()) < 3:
            return False
        
        sql_upper = sql.upper()
        
        # Must start with SELECT
        if not sql_upper.lstrip().startswith('SELECT'):
            return False
        
        # Check for dangerous operations
        dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        for op in dangerous:
            if op in sql_upper:
                return False
        
        # Check for valid table names
        for table in self.table_names:
            if table.upper() in sql_upper:
                return True
        
        # If no valid table found, try to find any table name
        table_pattern = r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(table_pattern, sql_upper)
        if matches:
            return True
        
        # Check for JOIN
        if 'JOIN' in sql_upper:
            join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            matches = re.findall(join_pattern, sql_upper)
            if matches:
                return True
        
        return False
    
    def _validate_question(self, question: str) -> bool:
        """Validate question."""
        if not question or len(question.strip()) < 5:
            return False
        
        # Must be a question or statement
        if not any(word in question.lower() for word in ['what', 'how', 'show', 'list', 'give', 'which']):
            return False
        
        return True
    
    def validate_dataset(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate entire dataset."""
        results = {
            'total': len(examples),
            'valid': 0,
            'invalid': 0,
            'errors': []
        }
        
        for i, example in enumerate(examples):
            if self.validate_example(example):
                results['valid'] += 1
            else:
                results['invalid'] += 1
                results['errors'].append({
                    'index': i,
                    'example': example.get('input', {}).get('question', '')[:50]
                })
        
        results['valid_ratio'] = results['valid'] / results['total'] if results['total'] > 0 else 0
        return results
    
    def check_data_leakage(self, examples: List[Dict[str, Any]]) -> List[str]:
        """Check for potential data leakage."""
        leakage = []
        
        # Check for hardcoded values
        value_pattern = r"'(?:'|[^'])*'"
        for example in examples:
            sql = example.get('output', {}).get('sql', '')
            values = re.findall(value_pattern, sql)
            
            # Ignore date values
            dates = [v for v in values if any(d in v.lower() for d in ['202', '201', 'date'])]
            values = [v for v in values if v not in dates]
            
            if values and len(values) > 3:
                leakage.append(f"Hardcoded values found: {', '.join(values[:3])}")
        
        return leakage