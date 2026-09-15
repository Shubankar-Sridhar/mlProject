"""Execute SQL queries with connection pooling."""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Execute SQL queries with connection pooling."""
    
    def __init__(self, database_url: str, config: Optional[Dict[str, Any]] = None):
        self.database_url = database_url
        self.config = config or {}
        self.pool = None
        self.async_pool = None
        
        self._setup_pool()
    
    def _setup_pool(self):
        """Setup connection pool."""
        try:
            # Sync pool for blocking operations
            self.pool = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.config.get('pool_size', 10),
                max_overflow=self.config.get('max_overflow', 20),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            logger.info("SQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to setup connection pool: {str(e)}")
            raise
    
    async def _setup_async_pool(self):
        """Setup async connection pool."""
        if not self.async_pool:
            try:
                self.async_pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=self.config.get('pool_size', 5),
                    max_size=self.config.get('max_overflow', 10),
                    timeout=self.config.get('timeout', 30)
                )
                logger.info("Async connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to setup async pool: {str(e)}")
                raise
    
    def execute(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query synchronously."""
        start_time = datetime.utcnow()
        
        try:
            with self.pool.connect() as conn:
                result = conn.execute(text(sql))
                
                # Get column names
                columns = result.keys()
                
                # Fetch all rows
                rows = [dict(zip(columns, row)) for row in result]
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Query executed: {len(rows)} rows in {execution_time:.3f}s")
                
                return rows
                
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    async def execute_async(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query asynchronously."""
        await self._setup_async_pool()
        
        start_time = datetime.utcnow()
        
        try:
            async with self.async_pool.acquire() as conn:
                rows = await conn.fetch(sql)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Async query executed: {len(rows)} rows in {execution_time:.3f}s")
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Async query execution failed: {str(e)}")
            raise
    
    async def execute_async_with_params(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SQL query with parameters asynchronously."""
        await self._setup_async_pool()
        
        try:
            async with self.async_pool.acquire() as conn:
                rows = await conn.fetch(sql, *params.values())
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Async query with params failed: {str(e)}")
            raise
    
    def close(self):
        """Close connection pool."""
        if self.pool:
            self.pool.dispose()
        if self.async_pool:
            # Async pool cleanup would be done in async context
            pass
        logger.info("SQL connection pool closed")