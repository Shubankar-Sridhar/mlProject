"""Health check endpoint."""

from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any
import os
import redis
from sqlalchemy import create_engine, text
import logging
import traceback

logger = logging.getLogger(__name__)

load_dotenv()

async def health_check() -> Dict[str, Any]:
    """Comprehensive health check."""
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'services': {}
    }
    
    # Check database
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql://admin:secure_password@postgres:5432/metadata')
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        status['services']['database'] = 'healthy'
    except Exception as e:
        status['services']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'degraded'
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check Redis
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
        r = redis.Redis.from_url(redis_url)
        r.ping()
        status['services']['redis'] = 'healthy'
    except Exception as e:
        status['services']['redis'] = f'unhealthy: {str(e)}'
        status['status'] = 'degraded'
        logger.error(f"Redis health check failed: {str(e)}")
    
    # Check model
    try:
        model_path = os.getenv('MODEL_PATH', '/app/models')
        if os.path.exists(model_path):
            status['services']['model'] = 'healthy'
        else:
            status['services']['model'] = 'degraded: model path not found'
            status['status'] = 'degraded'
    except Exception as e:
        status['services']['model'] = f'unhealthy: {str(e)}'
        status['status'] = 'degraded'
    
    # Check disk space
    try:
        import shutil
        usage = shutil.disk_usage('/app')
        free_gb = usage.free / (1024**3)
        if free_gb < 1:
            status['services']['disk'] = f'low: {free_gb:.2f}GB free'
            status['status'] = 'degraded'
        else:
            status['services']['disk'] = f'healthy: {free_gb:.2f}GB free'
    except Exception as e:
        status['services']['disk'] = f'unknown: {str(e)}'
    
    return status