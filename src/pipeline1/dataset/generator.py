"""Generate training dataset for fine-tuning."""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .template_engine import TemplateEngine
from .validator import DatasetValidator

logger = logging.getLogger(__name__)


class DatasetGenerator:
    """Generate training examples for fine-tuning."""
    
    def __init__(self, schema: Dict[str, Any], knowledge: Dict[str, Any]):
        self.schema = schema
        self.knowledge = knowledge
        self.template_engine = TemplateEngine()
        self.validator = DatasetValidator(schema)
        
        self.examples = []
        self._sample_sql_patterns = self._build_sql_patterns()
    
    def generate_examples(self, num_examples: int = 1000) -> List[Dict[str, Any]]:
        """Generate training examples."""
        examples = []
        
        # Generate different types of examples
        examples.extend(self._generate_basic_queries(int(num_examples * 0.3)))
        examples.extend(self._generate_aggregation_queries(int(num_examples * 0.2)))
        examples.extend(self._generate_join_queries(int(num_examples * 0.2)))
        examples.extend(self._generate_filter_queries(int(num_examples * 0.15)))
        examples.extend(self._generate_complex_queries(int(num_examples * 0.15)))
        
        # Shuffle and validate
        random.shuffle(examples)
        validated = [ex for ex in examples if self.validator.validate_example(ex)]
        
        logger.info(f"Generated {len(validated)} valid examples")
        return validated
    
    def _generate_basic_queries(self, count: int) -> List[Dict[str, Any]]:
        """Generate basic SELECT queries."""
        examples = []
        tables = self._get_tables()
        
        for _ in range(count):
            table = random.choice(tables)
            columns = self._get_columns(table)
            col = random.choice(columns) if columns else {'name': '*', 'type': 'unknown'}
            
            question = f"Show me the {self._get_business_name(col['name'])} from {self._get_business_name(table['name'])}"
            sql = f"SELECT {col['name']} FROM {table['name']}"
            
            if col['name'] != '*':
                question = f"What is the {self._get_business_name(col['name'])} for each {self._get_business_name(table['name'])}?"
                sql = f"SELECT {col['name']} FROM {table['name']}"
            
            examples.append(self._create_example(question, sql, 'simple'))
        
        return examples
    
    def _generate_aggregation_queries(self, count: int) -> List[Dict[str, Any]]:
        """Generate aggregation queries."""
        examples = []
        
        for _ in range(count):
            table = random.choice(self._get_tables())
            measure = self._find_measure_column(table)
            if not measure:
                continue
            
            dimension = self._find_dimension_column(table)
            aggregation = random.choice(['SUM', 'AVG', 'COUNT', 'MAX', 'MIN'])
            
            if dimension:
                question = f"What is the {aggregation.lower()} of {self._get_business_name(measure['name'])} by {self._get_business_name(dimension['name'])}?"
                sql = f"SELECT {dimension['name']}, {aggregation}({measure['name']}) FROM {table['name']} GROUP BY {dimension['name']}"
            else:
                question = f"What is the total {self._get_business_name(measure['name'])}?"
                sql = f"SELECT {aggregation}({measure['name']}) FROM {table['name']}"
            
            examples.append(self._create_example(question, sql, 'aggregation'))
        
        return examples
    
    def _generate_join_queries(self, count: int) -> List[Dict[str, Any]]:
        """Generate JOIN queries."""
        examples = []
        relationships = self.schema.get('relationships', {})
        
        if not relationships:
            return examples
        
        for _ in range(count):
            # Find a relationship to use
            source_tables = list(relationships.keys())
            if not source_tables:
                continue
            
            source = random.choice(source_tables)
            rels = relationships[source]
            if not rels:
                continue
            
            rel = random.choice(rels)
            target = rel['target']
            
            # Get source and target columns
            source_cols = self._get_columns({'name': source})
            target_cols = self._get_columns({'name': target})
            
            if not source_cols or not target_cols:
                continue
            
            source_measure = self._find_measure_column({'name': source})
            target_dimension = self._find_dimension_column({'name': target})
            
            if not source_measure or not target_dimension:
                continue
            
            question = f"Show {self._get_business_name(target_dimension['name'])} with {self._get_business_name(source_measure['name'])}"
            sql = f"""
                SELECT {target}.{target_dimension['name']}, SUM({source}.{source_measure['name']}) 
                FROM {source} 
                JOIN {target} ON {source}.{rel['source_columns'][0]} = {target}.{rel['target_columns'][0]} 
                GROUP BY {target}.{target_dimension['name']}
            """.strip()
            
            examples.append(self._create_example(question, sql, 'join'))
        
        return examples
    
    def _generate_filter_queries(self, count: int) -> List[Dict[str, Any]]:
        """Generate queries with filters."""
        examples = []
        
        for _ in range(count):
            table = random.choice(self._get_tables())
            columns = self._get_columns(table)
            
            if not columns:
                continue
            
            col = random.choice(columns)
            filter_col = random.choice(columns)
            
            question = f"Show {self._get_business_name(col['name'])} where {self._get_business_name(filter_col['name'])} is {self._get_filter_value(filter_col)}"
            sql = f"SELECT {col['name']} FROM {table['name']} WHERE {filter_col['name']} = '{self._get_filter_value(filter_col)}'"
            
            examples.append(self._create_example(question, sql, 'filter'))
        
        return examples
    
    def _generate_complex_queries(self, count: int) -> List[Dict[str, Any]]:
        """Generate complex queries with multiple operations."""
        examples = []
        
        for _ in range(count):
            # Combine patterns
            table = random.choice(self._get_tables())
            measure = self._find_measure_column(table)
            dimension = self._find_dimension_column(table)
            
            if not measure or not dimension:
                continue
            
            # Add date filter if available
            date_col = self._find_date_column(table)
            
            if date_col:
                question = f"What is the {self._get_business_name(measure['name'])} by {self._get_business_name(dimension['name'])} for {self._get_date_filter(date_col)}?"
                sql = f"""
                    SELECT {dimension['name']}, SUM({measure['name']}) 
                    FROM {table['name']} 
                    WHERE {date_col['name']} >= '2026-01-01' 
                    GROUP BY {dimension['name']} 
                    ORDER BY SUM({measure['name']}) DESC
                """.strip()
            else:
                question = f"What is the {self._get_business_name(measure['name'])} by {self._get_business_name(dimension['name'])}?"
                sql = f"""
                    SELECT {dimension['name']}, SUM({measure['name']}) 
                    FROM {table['name']} 
                    GROUP BY {dimension['name']} 
                    ORDER BY SUM({measure['name']}) DESC
                """.strip()
            
            examples.append(self._create_example(question, sql, 'complex'))
        
        return examples
    
    def _create_example(self, question: str, sql: str, example_type: str) -> Dict[str, Any]:
        """Create a single training example."""
        return {
            "instruction": "Convert the user's question into SQL query.",
            "input": {
                "schema": self._get_schema_context(),
                "business_rules": self._get_business_rules_context(),
                "question": question
            },
            "output": {
                "sql": sql,
                "intent": self._extract_intent(question, sql),
                "type": example_type
            }
        }
    
    def _get_schema_context(self) -> str:
        """Get schema context for prompt."""
        lines = []
        for schema in self.schema.get('schemas', []):
            for table in schema['tables']:
                cols = [f"{c['name']} {c['type']}" for c in table['columns']]
                lines.append(f"{table['name']}({', '.join(cols)})")
        return "\n".join(lines)
    
    def _get_business_rules_context(self) -> str:
        """Get business rules context."""
        rules = []
        for rule_name, rule_data in self.knowledge.get('rules', {}).items():
            rules.append(f"{rule_name}: {rule_data.get('definition', '')}")
        return "\n".join(rules) if rules else "No specific business rules."
    
    def _extract_intent(self, question: str, sql: str) -> Dict[str, Any]:
        """Extract intent from query."""
        intent = {
            "type": "unknown",
            "dimensions": [],
            "measures": [],
            "aggregation": None,
            "time_dimension": None
        }
        
        # Check for aggregation
        for agg in ['SUM', 'AVG', 'COUNT', 'MAX', 'MIN']:
            if agg in sql.upper():
                intent['aggregation'] = agg
                break
        
        # Extract dimensions (GROUP BY columns)
        if 'GROUP BY' in sql.upper():
            group_by_part = sql.upper().split('GROUP BY')[1].split('ORDER BY')[0].strip()
            intent['dimensions'] = [d.strip() for d in group_by_part.split(',')]
        
        # Extract measures (aggregated columns)
        if 'SUM(' in sql.upper() or 'AVG(' in sql.upper():
            measure_match = re.search(r'(SUM|AVG|COUNT|MAX|MIN)\(([^)]+)\)', sql.upper())
            if measure_match:
                intent['measures'] = [measure_match.group(2)]
        
        return intent
    
    def _get_tables(self) -> List[Dict[str, Any]]:
        """Get all tables from schema."""
        tables = []
        for schema in self.schema.get('schemas', []):
            tables.extend(schema['tables'])
        return tables
    
    def _get_columns(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get columns for a table."""
        return table.get('columns', [])
    
    def _get_business_name(self, technical_name: str) -> str:
        """Get business name for a technical name."""
        # Try to find in terminology
        for term, info in self.knowledge.get('terminology', {}).items():
            if term in technical_name.lower() or technical_name.lower() in term:
                return term
        
        # Return human-readable version
        return technical_name.replace('_', ' ').title()
    
    def _find_measure_column(self, table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a measure column."""
        columns = self._get_columns(table)
        numeric_cols = [c for c in columns if 'int' in c['type'].lower() or 'decimal' in c['type'].lower() or 'float' in c['type'].lower()]
        
        if numeric_cols:
            # Prefer columns not named '*_id'
            for col in numeric_cols:
                if not col['name'].endswith('_id') and not col['name'].endswith('_id'):
                    return col
            return numeric_cols[0]
        return None
    
    def _find_dimension_column(self, table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a dimension column."""
        columns = self._get_columns(table)
        string_cols = [c for c in columns if 'varchar' in c['type'].lower() or 'text' in c['type'].lower()]
        
        if string_cols:
            return string_cols[0]
        return None
    
    def _find_date_column(self, table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a date column."""
        columns = self._get_columns(table)
        date_cols = [c for c in columns if 'date' in c['type'].lower() or 'time' in c['type'].lower()]
        
        if date_cols:
            return date_cols[0]
        return None
    
    def _get_filter_value(self, col: Dict[str, Any]) -> str:
        """Get a sample filter value."""
        if 'int' in col['type'].lower():
            return str(random.randint(1, 100))
        elif 'varchar' in col['type'].lower() or 'text' in col['type'].lower():
            values = ['New York', 'London', 'Tokyo', 'Paris', 'Berlin']
            return random.choice(values)
        else:
            return '1'
    
    def _get_date_filter(self, col: Dict[str, Any]) -> str:
        """Get a date filter value."""
        return "the current year"
    
    def _build_sql_patterns(self) -> Dict[str, str]:
        """Build SQL patterns for template engine."""
        return {
            'select': "SELECT {columns} FROM {table}",
            'select_where': "SELECT {columns} FROM {table} WHERE {condition}",
            'select_join': "SELECT {columns} FROM {table1} JOIN {table2} ON {join_condition}",
            'select_group': "SELECT {columns} FROM {table} GROUP BY {group_by}",
            'select_order': "SELECT {columns} FROM {table} ORDER BY {order_by}",
            'select_agg': "SELECT {agg}({column}) FROM {table}"
        }
    
    def export_to_jsonl(self, examples: List[Dict[str, Any]], filepath: str):
        """Export examples to JSONL format."""
        with open(filepath, 'w') as f:
            for ex in examples:
                f.write(json.dumps(ex) + '\n')
        logger.info(f"Exported {len(examples)} examples to {filepath}")
    
    def create_splits(self, examples: List[Dict[str, Any]], train_ratio: float = 0.8) -> Dict[str, List[Dict[str, Any]]]:
        """Create train/val/test splits."""
        random.shuffle(examples)
        n = len(examples)
        train_n = int(n * train_ratio)
        val_n = int(n * 0.1)
        
        return {
            'train': examples[:train_n],
            'valid': examples[train_n:train_n + val_n],
            'test': examples[train_n + val_n:]
        }