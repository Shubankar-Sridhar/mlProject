"""llama.cpp inference engine."""

import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from llama_cpp import Llama
from .prompt_builder import PromptBuilder
from .structured_output import StructuredOutputParser

logger = logging.getLogger(__name__)


class LlamaEngine:
    """llama.cpp inference engine with KV caching."""
    
    def __init__(self, model_path: str, config: Dict[str, Any]):
        self.model_path = model_path
        self.config = config
        self.llama = None
        self.prompt_builder = PromptBuilder(config)
        self.output_parser = StructuredOutputParser()
        
        self._load_model()
    
    def _load_model(self):
        """Load GGUF model."""
        try:
            self.llama = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get('max_length', 4096),
                n_gpu_layers=self.config.get('n_gpu_layers', -1),
                n_threads=self.config.get('n_threads', 8),
                verbose=False
            )
            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def generate(
        self,
        user_query: str,
        schema: Dict[str, Any],
        business_rules: Dict[str, Any],
        current_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate SQL and intent from user query."""
        # Build prompt
        prompt = self.prompt_builder.build_full_prompt(
            user_query=user_query,
            schema=schema,
            business_rules=business_rules,
            current_date=current_date or datetime.utcnow()
        )
        
        # Generate
        try:
            response = self.llama(
                prompt,
                max_tokens=self.config.get('max_tokens', 512),
                temperature=self.config.get('temperature', 0.1),
                top_p=self.config.get('top_p', 0.9),
                top_k=self.config.get('top_k', 50),
                stop=['<|endoftext|>', '<|user|>', '<|system|>'],
                echo=False
            )
            
            generated_text = response['choices'][0]['text']
            
            # Parse output
            result = self.output_parser.parse(generated_text)
            result['model_version'] = self.config.get('version', 'unknown')
            result['generation_time_ms'] = response.get('generation_time', 0)
            
            logger.info(f"Generated SQL: {result.get('sql', '')[:100]}...")
            return result
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise
    
    def generate_with_cache(
        self,
        user_query: str,
        schema: Dict[str, Any],
        business_rules: Dict[str, Any],
        current_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate with KV caching for repeated static context."""
        # Build static prefix
        static_prompt = self.prompt_builder.build_system_prompt()
        
        # This would use llama.cpp's caching mechanism
        # Implementation depends on llama.cpp version
        
        return self.generate(user_query, schema, business_rules, current_date)
    
    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for text (if supported)."""
        try:
            embeddings = self.llama.create_embedding(text)
            return embeddings['data'][0]['embedding']
        except Exception as e:
            logger.warning(f"Failed to get embeddings: {str(e)}")
            return []