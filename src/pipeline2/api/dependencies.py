"""API dependencies."""

from typing import Dict,List, Any, Optional
from fastapi import Request, HTTPException
from dotenv import load_dotenv
import redis
import os
from pprint import pprint
import logging
import datetime

logger = logging.getLogger(__name__)
load_dotenv()

class AuthDependency:
    """Authentication dependency."""
    
    async def __call__(self, request: Request) -> Dict[str, Any]:
        """Authenticate request."""
        # Simple auth - can be extended with JWT
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_KEY', 'default-key')
        
        if api_key and api_key == expected_key:
            return {'authenticated': True, 'user': 'system'}
        
        # Allow development without auth
        if os.getenv('ENV', 'development') == 'development':
            return {'authenticated': True, 'user': 'dev'}
        
        raise HTTPException(status_code=401, detail="Authentication required")


class RateLimiter:
    """Rate limiting dependency."""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            os.getenv('REDIS_URL', 'redis://redis:6379/0'),
            decode_responses=True
        )
    
    async def __call__(self, request: Request) -> bool:
        """Check rate limit."""
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Get current count
        count = self.redis_client.get(key)
        if count is None:
            self.redis_client.setex(key, 60, 1)
            return True
        
        if int(count) >= 60:  # 60 requests per minute
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self.redis_client.incr(key)
        return True


class ModelManager:
    """Model management dependency."""
    
    def __init__(self):
        self.models = {}
        self.default_model = os.getenv('DEFAULT_MODEL_ID', 'qwenModel')
    
    async def get_model(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get model instance."""
        model_id = model_id or self.default_model
        model_path = os.getenv('MODEL_PATH', '/app/models')

        
        if model_id not in self.models:
            # Load model from registry
            try:
                import json
                with open(f"{model_path}/{model_id}/metadata.json", 'r') as f:
                    metadata = json.load(f)
                
                print(model_path)
                print(model_id)
                pprint(metadata)
                self.models[model_id] = {
                    'id': model_id,
                    'path': f"{model_path}/{model_id}/model.gguf",
                    'version': metadata.get('version', '1.0'),
                    'config': metadata.get('config', {})
                }
                logger.info(f"Loaded model: {model_id}")
            except Exception as e:
                logger.error(f"Failed to load model {model_id}: {str(e)}")
                raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        return self.models[model_id]
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        import json
        import os
        
        models = []
        model_dir = os.getenv('MODEL_PATH', "/app/models/registry/models")
        
        if os.path.exists(model_dir):
            for model_id in os.listdir(model_dir):
                try:
                    with open(f"{model_dir}/{model_id}/metadata.json", 'r') as f:
                        metadata = json.load(f)
                    models.append({
                        'id': model_id,
                        'name': metadata.get('name', model_id),
                        'version': metadata.get('version', '1.0'),
                        'created_at': metadata.get('created_at'),
                        'path': f"{model_dir}/{model_id}/model.gguf"
                    })
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {model_id}: {str(e)}")
        return models
    
    async def register_model(self, model_id: str, model_path: str) -> None:
        """Register a new model."""
        import json
        import shutil
        import os
        
        # Copy model to registry
        target_dir = f"/app/models/registry/models/{model_id}"
        os.makedirs(target_dir, exist_ok=True)
        
        shutil.copy(model_path, f"{target_dir}/model.gguf")
        
        # Save metadata
        metadata = {
            'id': model_id,
            'name': f"Enterprise Model {model_id}",
            'version': '1.0',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'config': {}
        }
        
        with open(f"{target_dir}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Registered model: {model_id}")


class DatabaseManager:
    """Database management dependency."""
    
    def __init__(self):
        self.connection_pool = None
        self.schema_cache = None
        self.rules_cache = None
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get schema from cache or database."""
        if self.schema_cache:
            return self.schema_cache
        
        # Load schema
        try:
            import json
            with open("/app/configs/schema.json", 'r') as f:
                self.schema_cache = json.load(f)
            logger.info("Schema loaded from cache")
        except Exception as e:
            logger.error(f"Failed to load schema: {str(e)}")
            self.schema_cache = {}
        
        return self.schema_cache
    
    async def get_business_rules(self) -> Dict[str, Any]:
        """Get business rules from cache."""
        if self.rules_cache:
            return self.rules_cache
        
        try:
            import json
            with open("/app/configs/business_rules.json", 'r') as f:
                self.rules_cache = json.load(f)
            logger.info("Business rules loaded from cache")
        except Exception as e:
            logger.error(f"Failed to load business rules: {str(e)}")
            self.rules_cache = {}
        
        return self.rules_cache