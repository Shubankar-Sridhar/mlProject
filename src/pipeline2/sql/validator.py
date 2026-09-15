"""Validate SQL queries against schema."""

import re
from typing import Dict, List, Any, Tuple, Optional
import logging

from .parser import SQLParser

logger = logging.getLogger(__name__)


class SQLValidator:
    """Validate SQL queries for security and correctness."""
    
    def __init__(self, schema: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        self.schema = schema
        self.config = config or {}
        self.parser = SQLParser(schema)
        
        self.forbidden_keywords = self.config.get('forbidden_keywords', [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE'
        ])
    
    def validate(self, sql: str) -> Tuple[bool, List[str]]:
        """Validate SQL query."""
        errors = []
        
        if not sql or len(sql.strip()) < 3:
            errors.append("Empty or too short SQL query")
            return False, errors
        
        sql_upper = sql.upper()
        
        # Check for forbidden keywords
        for keyword in self.forbidden_keywords:
            if keyword in sql_upper:
                errors.append(f"Forbidden keyword: {keyword}")
                return False, errors
        
        # Must start with SELECT
        if not sql_upper.lstrip().startswith('SELECT'):
            errors.append("Only SELECT queries are allowed")
            return False, errors
        
        # Parse SQL
        parsed = self.parser.parse(sql)
        if not parsed['valid']:
            errors.extend(parsed['errors'])
            return False, errors
        
        # Validate tables exist
        for table in parsed['tables']:
            if table.lower() not in [t.lower() for t in self.parser.table_names]:
                errors.append(f"Unknown table: {table}")
        
        # Validate columns exist
        for table in parsed['tables']:
            columns = self.parser.column_names.get(table, [])
            for col in parsed['columns']:
                # Skip expressions
                if any(op in col.upper() for op in ['SUM', 'AVG', 'COUNT', 'MAX', 'MIN', 'DISTINCT']):
                    continue
                if col not in columns:
                    errors.append(f"Unknown column: {col} in table {table}")
        
        # Check result limit
        max_rows = self.config.get('max_rows', 10000)
        if not parsed['limit']:
            errors.append(f"No LIMIT clause (max {max_rows} rows)")
        elif parsed['limit'] > max_rows:
            errors.append(f"LIMIT exceeds maximum of {max_rows}")
        
        return len(errors) == 0, errors
    
    def repair_sql(self, sql: str, errors: List[str]) -> str:
        """Attempt to repair SQL based on validation errors."""
        repaired = sql
        
        for error in errors:
            # Handle unknown table errors
            if "Unknown table:" in error:
                table = error.split(":")[1].strip()
                # Try to find similar table name
                similar = self._find_similar_table(table)
                if similar:
                    repaired = repaired.replace(table, similar)
            
            # Handle unknown column errors
            if "Unknown column:" in error:
                col = error.split(":")[1].strip()
                # Try to find similar column name
                similar = self._find_similar_column(col)
                if similar:
                    repaired = repaired.replace(col, similar)
            
            # Add LIMIT if missing
            if "No LIMIT clause" in error:
                max_rows = self.config.get('max_rows', 10000)
                repaired = f"{repaired} LIMIT {max_rows}"
        
        return repaired
    
    def _find_similar_table(self, table: str) -> Optional[str]:
        """Find similar table name in schema."""
        table_lower = table.lower()
        for t in self.parser.table_names:
            if t.lower() == table_lower:
                return t
            if t.lower().startswith(table_lower) or table_lower.startswith(t.lower()):
                return t
        return None
    
    def _find_similar_column(self, column: str) -> Optional[str]:
        """Find similar column name in schema."""
        column_lower = column.lower()
        for table, columns in self.parser.column_names.items():
            for col in columns:
                if col.lower() == column_lower:
                    return col
                if col.lower().startswith(column_lower) or column_lower.startswith(col.lower()):
                    return col
        return None