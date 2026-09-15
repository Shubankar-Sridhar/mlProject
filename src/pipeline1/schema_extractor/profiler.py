"""Data profiling using SQLAlchemy inspector and queries."""

from typing import Dict, List, Any, Optional
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class DataProfiler:
    """Profile data characteristics using SQLAlchemy."""
    
    def __init__(self, inspector):
        """Initialize profiler with database inspector."""
        self.inspector = inspector
        self.engine = inspector.engine
    
    def profile_all_schemas(self, schemas: List[str]) -> Dict[str, Any]:
        """
        Profile all schemas.
        
        Args:
            schemas: List of schema names
            
        Returns:
            Profiling results
        """
        profiles = {}
        for schema in schemas:
            if schema in ['information_schema', 'pg_catalog']:
                continue
            profiles[schema] = self._profile_schema(schema)
        return profiles
    
    def _profile_schema(self, schema: str) -> Dict[str, Any]:
        """Profile a schema."""
        tables = self.inspector.get_tables(schema=schema)
        schema_profile = {
            'table_count': len(tables),
            'tables': {}
        }
        
        for table_name in tables:
            schema_profile['tables'][table_name] = self._profile_table(schema, table_name)
        
        return schema_profile
    
    def _profile_table(self, schema: str, table_name: str) -> Dict[str, Any]:
        """Profile a table."""
        try:
            # Get row count
            row_count_query = f'SELECT COUNT(*) FROM "{schema}"."{table_name}"' if schema else f'SELECT COUNT(*) FROM "{table_name}"'
            with self.engine.connect() as conn:
                result = conn.execute(text(row_count_query))
                row_count = result.scalar()
            
            columns = self.inspector.get_columns(table_name, schema=schema)
            
            # Profile each column
            column_profiles = {}
            for col in columns:
                column_profiles[col['name']] = self._profile_column(schema, table_name, col)
            
            return {
                'row_count': row_count,
                'column_count': len(columns),
                'columns': column_profiles,
                'estimated_size': self._estimate_table_size(schema, table_name)
            }
        except Exception as e:
            logger.error(f"Failed to profile table '{table_name}': {str(e)}")
            return {'error': str(e)}
    
    def _profile_column(self, schema: str, table_name: str, column_info: Dict) -> Dict[str, Any]:
        """Profile a single column."""
        col_name = column_info['name']
        col_type = column_info['type']
        
        try:
            # Build column statistics query
            base_query = f'SELECT COUNT("{col_name}") as total_count'
            base_query += f', COUNT(DISTINCT "{col_name}") as distinct_count'
            base_query += f', COUNT("{col_name}") - COUNT(*) as null_count'
            
            if 'int' in str(col_type).lower() or 'decimal' in str(col_type).lower() or 'float' in str(col_type).lower() or 'numeric' in str(col_type).lower():
                base_query += f', AVG("{col_name}")::float as avg_value'
                base_query += f', MIN("{col_name}") as min_value'
                base_query += f', MAX("{col_name}") as max_value'
            
            query = f'SELECT {base_query} FROM "{schema}"."{table_name}"' if schema else f'SELECT {base_query} FROM "{table_name}"'
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                row = result.fetchone()
                
                profile = {
                    'total_count': row[0],
                    'distinct_count': row[1],
                    'null_count': row[2],
                    'null_ratio': row[2] / row[0] if row[0] > 0 else 1.0,
                    'unique_ratio': row[1] / row[0] if row[0] > 0 else 0.0
                }
                
                if len(row) > 3:
                    profile['avg_value'] = float(row[3]) if row[3] is not None else None
                    profile['min_value'] = float(row[4]) if row[4] is not None else None
                    profile['max_value'] = float(row[5]) if row[5] is not None else None
                
                # Detect semantic type
                profile['semantic_type'] = self._detect_semantic_type(profile, col_type, col_name)
                
                # Get sample values
                sample_query = f'SELECT "{col_name}" FROM "{schema}"."{table_name}" LIMIT 5' if schema else f'SELECT "{col_name}" FROM "{table_name}" LIMIT 5'
                sample_result = conn.execute(text(sample_query))
                profile['sample_values'] = [row[0] for row in sample_result.fetchall()]
                
                return profile
        except Exception as e:
            logger.error(f"Failed to profile column '{col_name}': {str(e)}")
            return {'error': str(e)}
    
    def _detect_semantic_type(self, profile: Dict, col_type: str, col_name: str) -> str:
        """Detect semantic type of column."""
        # Check for identifiers
        if 'id' in col_name.lower() and profile['unique_ratio'] > 0.9:
            return 'identifier'
        
        # Check for temporal columns
        if 'date' in col_name.lower() or 'time' in col_name.lower() or 'timestamp' in col_name.lower():
            return 'temporal'
        
        # Check for categorical columns
        if 'varchar' in str(col_type).lower() or 'text' in str(col_type).lower():
            if profile['unique_ratio'] < 0.1:
                return 'categorical'
            elif profile['unique_ratio'] < 0.3:
                return 'categorical_high_cardinality'
            else:
                return 'text'
        
        # Check for numeric measures
        if 'int' in str(col_type).lower() or 'decimal' in str(col_type).lower() or 'float' in str(col_type).lower() or 'numeric' in str(col_type).lower():
            if 'id' in col_name.lower() or '_id' in col_name.lower():
                return 'identifier'
            if profile['unique_ratio'] < 0.01:
                return 'categorical'
            return 'measure'
        
        # Check for boolean
        if 'bool' in str(col_type).lower():
            return 'boolean'
        
        return 'unknown'
    
    def _estimate_table_size(self, schema: str, table_name: str) -> Dict[str, Any]:
        """Estimate table size."""
        try:
            query = f"""
                SELECT 
                    pg_total_relation_size('"{schema}"."{table_name}"') as total_size,
                    pg_size_pretty(pg_total_relation_size('"{schema}"."{table_name}"')) as total_size_pretty,
                    (SELECT COUNT(*) FROM "{schema}"."{table_name}") as row_count
            """ if schema else f"""
                SELECT 
                    pg_total_relation_size('"{table_name}"') as total_size,
                    pg_size_pretty(pg_total_relation_size('"{table_name}"')) as total_size_pretty,
                    (SELECT COUNT(*) FROM "{table_name}") as row_count
            """
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                row = result.fetchone()
                return {
                    'total_bytes': row[0],
                    'total_pretty': row[1],
                    'row_count': row[2]
                }
        except Exception as e:
            logger.error(f"Failed to estimate table size: {str(e)}")
            return {'error': str(e)}