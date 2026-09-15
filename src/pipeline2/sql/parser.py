"""Parse SQL queries."""

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SQLParser:
    """Parse and analyze SQL queries."""
    
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
    
    def parse(self, sql: str) -> Dict[str, Any]:
        """Parse SQL into AST-like structure."""
        result = {
            'type': 'select',
            'tables': [],
            'columns': [],
            'joins': [],
            'filters': [],
            'groups': [],
            'order_by': [],
            'limit': None,
            'valid': True,
            'errors': []
        }
        
        sql_upper = sql.upper()
        
        # Check query type
        if not sql_upper.lstrip().startswith('SELECT'):
            result['valid'] = False
            result['errors'].append('Only SELECT queries are allowed')
            return result
        
        # Extract tables (FROM clause)
        from_match = re.search(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql_upper)
        if from_match:
            result['tables'].append(from_match.group(1))
        
        # Extract joins
        join_matches = re.finditer(r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', sql_upper)
        for match in join_matches:
            result['joins'].append(match.group(1))
            result['tables'].append(match.group(1))
        
        # Extract columns (SELECT clause)
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper, re.DOTALL)
        if select_match:
            columns = [c.strip() for c in select_match.group(1).split(',')]
            result['columns'] = columns
        
        # Extract filters (WHERE clause)
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP BY|\s+ORDER BY|\s+LIMIT|$)', sql_upper, re.DOTALL)
        if where_match:
            result['filters'] = [where_match.group(1).strip()]
        
        # Extract groups (GROUP BY clause)
        group_match = re.search(r'GROUP BY\s+(.+?)(?:\s+ORDER BY|\s+LIMIT|$)', sql_upper, re.DOTALL)
        if group_match:
            result['groups'] = [g.strip() for g in group_match.group(1).split(',')]
        
        # Extract order (ORDER BY clause)
        order_match = re.search(r'ORDER BY\s+(.+?)(?:\s+LIMIT|$)', sql_upper, re.DOTALL)
        if order_match:
            result['order_by'] = [o.strip() for o in order_match.group(1).split(',')]
        
        # Extract limit
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        if limit_match:
            result['limit'] = int(limit_match.group(1))
        
        # Validate tables exist
        for table in result['tables']:
            if table.lower() not in [t.lower() for t in self.table_names]:
                result['valid'] = False
                result['errors'].append(f"Unknown table: {table}")
        
        return result