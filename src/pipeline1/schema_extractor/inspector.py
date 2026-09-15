"""
SQLAlchemy-based database inspector for schema extraction.
Uses get_tables(), get_columns(), get_foreign_keys() for deterministic extraction.
"""

from typing import List, Dict, Optional, Any
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseInspector:
    """Database inspector using SQLAlchemy for schema extraction."""
    
    def __init__(self, database_url: str, pool_size: int = 10, max_overflow: int = 20):
        """
        Initialize database inspector with connection pool.
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
        """
        self.database_url = database_url
        self.engine = None
        self.inspector = None
        self.metadata = MetaData()
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._connect()
    
    def _connect(self) -> None:
        """Establish database connection with connection pooling."""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            self.inspector = inspect(self.engine)
            self.metadata.reflect(bind=self.engine)
            logger.info(f"Connected to database: {self.database_url.split('@')[-1] if '@' in self.database_url else 'unknown'}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    def get_schemas(self) -> List[str]:
        """
        Get all schema names in the database.
        
        Returns:
            List of schema names
        """
        try:
            schemas = self.inspector.get_schema_names()
            logger.info(f"Found {len(schemas)} schemas")
            return schemas
        except SQLAlchemyError as e:
            logger.error(f"Failed to get schemas: {str(e)}")
            return []
    
    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        Get all table names in a schema.
        
        Args:
            schema: Schema name (default: None, uses default schema)
            
        Returns:
            List of table names
        """
        try:
            tables = self.inspector.get_table_names(schema=schema)
            logger.info(f"Found {len(tables)} tables in schema '{schema or 'default'}'")
            return tables
        except SQLAlchemyError as e:
            logger.error(f"Failed to get tables for schema '{schema}': {str(e)}")
            return []
    
    def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get column information for a table using get_columns().
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            List of column dictionaries with complete metadata
        """
        try:
            columns = self.inspector.get_columns(table_name, schema=schema)
            logger.info(f"Found {len(columns)} columns in table '{table_name}'")
            
            # Enrich with additional information
            enriched_columns = []
            for col in columns:
                enriched_col = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col.get('nullable', True),
                    'default': col.get('default', None),
                    'primary_key': False,  # Will be set later
                    'autoincrement': col.get('autoincrement', False),
                    'comment': col.get('comment', None)
                }
                enriched_columns.append(enriched_col)
            
            return enriched_columns
        except SQLAlchemyError as e:
            logger.error(f"Failed to get columns for table '{table_name}': {str(e)}")
            return []
    
    def get_primary_keys(self, table_name: str, schema: Optional[str] = None) -> List[str]:
        """
        Get primary key columns for a table using get_pk_constraint().
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            List of primary key column names
        """
        try:
            pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
            pk_columns = pk_constraint.get('constrained_columns', [])
            logger.info(f"Found {len(pk_columns)} primary keys in table '{table_name}'")
            return pk_columns
        except SQLAlchemyError as e:
            logger.error(f"Failed to get primary keys for table '{table_name}': {str(e)}")
            return []
    
    def get_foreign_keys(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get foreign key relationships using get_foreign_keys().
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            List of foreign key relationship dictionaries
        """
        try:
            fks = self.inspector.get_foreign_keys(table_name, schema=schema)
            logger.info(f"Found {len(fks)} foreign keys in table '{table_name}'")
            
            enriched_fks = []
            for fk in fks:
                enriched_fk = {
                    'constrained_columns': fk.get('constrained_columns', []),
                    'referred_schema': fk.get('referred_schema', schema),
                    'referred_table': fk.get('referred_table', ''),
                    'referred_columns': fk.get('referred_columns', []),
                    'name': fk.get('name', None)
                }
                enriched_fks.append(enriched_fk)
            
            return enriched_fks
        except SQLAlchemyError as e:
            logger.error(f"Failed to get foreign keys for table '{table_name}': {str(e)}")
            return []
    
    def get_indexes(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get index information using get_indexes().
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            List of index dictionaries
        """
        try:
            indexes = self.inspector.get_indexes(table_name, schema=schema)
            logger.info(f"Found {len(indexes)} indexes in table '{table_name}'")
            return indexes
        except SQLAlchemyError as e:
            logger.error(f"Failed to get indexes for table '{table_name}': {str(e)}")
            return []
    
    def get_table_comment(self, table_name: str, schema: Optional[str] = None) -> Optional[str]:
        """
        Get table comment using get_table_comment().
        
        Args:
            table_name: Table name
            schema: Schema name
            
        Returns:
            Table comment or None
        """
        try:
            comment_info = self.inspector.get_table_comment(table_name, schema=schema)
            return comment_info.get('text', None)
        except SQLAlchemyError as e:
            logger.error(f"Failed to get comment for table '{table_name}': {str(e)}")
            return None
    
    def get_relationship_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build complete relationship graph using foreign key information.
        
        Returns:
            Dictionary mapping table names to their foreign key relationships
        """
        relationships = {}
        
        for schema in self.get_schemas():
            for table in self.get_tables(schema):
                table_key = f"{schema}.{table}" if schema else table
                relationships[table_key] = self.get_foreign_keys(table, schema)
        
        return relationships
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a read-only query and return results as dictionaries.
        
        Args:
            query: SQL query string (must be SELECT)
            
        Returns:
            List of row dictionaries
        """
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result]
                logger.info(f"Query executed, returned {len(rows)} rows")
                return rows
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def close(self) -> None:
        """Close database connection and dispose pool."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()