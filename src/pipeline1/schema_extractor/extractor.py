"""Complete schema extractor using SQLAlchemy inspector."""

from typing import Dict, List, Optional, Any
from .inspector import DatabaseInspector
from .profiler import DataProfiler
from .serializer import SchemaSerializer
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extract complete database schema using SQLAlchemy inspector methods."""
    
    def __init__(self, database_url: str):
        """
        Initialize schema extractor.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.inspector = None
        self.serializer = SchemaSerializer()
        self.profiler = None
    
    def extract_full_schema(self, profile: bool = True) -> Dict[str, Any]:
        """
        Extract complete schema using SQLAlchemy inspector methods.
        
        Uses only inspector.get_tables(), get_columns(), get_foreign_keys(), etc.
        
        Args:
            profile: Whether to include data profiling
            
        Returns:
            Complete schema dictionary
        """
        with DatabaseInspector(self.database_url) as inspector:
            self.inspector = inspector
            
            # Get all schemas
            schemas = inspector.get_schemas()
            
            schema_data = {
                'version': '1.0',
                'extracted_at': datetime.utcnow().isoformat() + 'Z',
                'database': {
                    'url': self._mask_url(self.database_url),
                    'type': 'postgresql'
                },
                'schemas': []
            }
            
            # Extract each schema
            for schema_name in schemas:
                if schema_name in ['information_schema', 'pg_catalog']:
                    continue
                    
                schema_dict = {
                    'name': schema_name,
                    'tables': []
                }
                
                # Get tables in schema
                tables = inspector.get_tables(schema=schema_name)
                
                for table_name in tables:
                    table_dict = self._extract_table(schema_name, table_name)
                    schema_dict['tables'].append(table_dict)
                
                if schema_dict['tables']:
                    schema_data['schemas'].append(schema_dict)
            
            # Build relationship graph
            schema_data['relationships'] = inspector.get_relationship_info()
            
            # Profile data if requested
            if profile:
                self.profiler = DataProfiler(inspector)
                schema_data['profiles'] = self.profiler.profile_all_schemas(schemas)
            
            return schema_data
    
    def _extract_table(self, schema: str, table_name: str) -> Dict[str, Any]:
        """
        Extract a single table's schema.
        
        Args:
            schema: Schema name
            table_name: Table name
            
        Returns:
            Table dictionary with columns, keys, and constraints
        """
        # Get columns with full metadata
        columns = self.inspector.get_columns(table_name, schema=schema)
        
        # Get primary keys
        pk_columns = self.inspector.get_primary_keys(table_name, schema=schema)
        pk_set = set(pk_columns)
        
        # Mark primary keys in columns
        for col in columns:
            if col['name'] in pk_set:
                col['primary_key'] = True
        
        # Get foreign keys
        foreign_keys = self.inspector.get_foreign_keys(table_name, schema=schema)
        
        # Get indexes
        indexes = self.inspector.get_indexes(table_name, schema=schema)
        
        # Get table comment
        comment = self.inspector.get_table_comment(table_name, schema=schema)
        
        table_dict = {
            'name': table_name,
            'description': comment or '',
            'columns': columns,
            'primary_keys': pk_columns,
            'foreign_keys': foreign_keys,
            'indexes': indexes,
            'schema': schema
        }
        
        logger.info(f"Extracted table '{schema}.{table_name}' with {len(columns)} columns")
        return table_dict
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive information in database URL."""
        import re
        # Replace password in URL
        masked = re.sub(r':[^:@]+@', ':***@', url)
        return masked
    
    def extract_single_table(self, schema: str, table_name: str) -> Dict[str, Any]:
        """
        Extract a single table's schema.
        
        Args:
            schema: Schema name
            table_name: Table name
            
        Returns:
            Table schema dictionary
        """
        with DatabaseInspector(self.database_url) as inspector:
            self.inspector = inspector
            return self._extract_table(schema, table_name)
    
    def export_to_canonical(self, schema_data: Dict[str, Any]) -> str:
        """
        Export schema to canonical JSON format.
        
        Args:
            schema_data: Schema dictionary
            
        Returns:
            JSON string
        """
        return self.serializer.serialize(schema_data)
    
    def export_to_markdown(self, schema_data: Dict[str, Any]) -> str:
        """
        Export schema to Markdown for documentation.
        
        Args:
            schema_data: Schema dictionary
            
        Returns:
            Markdown string
        """
        return self.serializer.to_markdown(schema_data)