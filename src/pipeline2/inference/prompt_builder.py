"""Build prompts for runtime inference."""

from typing import Dict, Any, Optional
from datetime import datetime
import json


class PromptBuilder:
    """Build runtime prompts with context."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def build_system_prompt(self) -> str:
        """Build system prompt."""
        return """<|system|>
You are an expert enterprise SQL generator. Your task is to convert natural language questions into SQL queries.

Instructions:
1. Always use the provided database schema
2. Follow business rules exactly
3. Only generate SELECT queries (read-only)
4. Include proper JOIN conditions
5. Use appropriate aggregations
6. Handle date filtering correctly
7. Return SQL and intent as JSON

Output format:
```json
{
    "sql": "SELECT ...",
    "intent": {
        "type": "query_type",
        "dimensions": [],
        "measures": [],
        "aggregation": null,
        "time_dimension": null,
        "filters": []
    }
}
"""