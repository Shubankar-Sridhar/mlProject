
#### `src/pipeline2/inference/structured_output.py`
"""Parse structured output from model."""

import json
import re
from typing import Dict, Any, Optional


class StructuredOutputParser:
    """Parse structured output from model."""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse model output."""
        result = {
            'sql': '',
            'intent': {},
            'raw': text
        }
        
        # Try to extract JSON
        try:
            json_match = re.search(r'```json\s*({.+?})\s*```', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                result['sql'] = data.get('sql', '')
                result['intent'] = data.get('intent', {})
                return result
        except json.JSONDecodeError:
            pass
        
        # Try to find SQL
        sql_match = re.search(r'```sql\s*([^`]+?)\s*```', text, re.DOTALL)
        if sql_match:
            result['sql'] = sql_match.group(1).strip()
        else:
            # Try to find SELECT statement
            select_match = re.search(r'SELECT\s+.*?(?:(?:;)|(?:\n\n))', text, re.DOTALL | re.IGNORECASE)
            if select_match:
                result['sql'] = select_match.group(0).strip()
        
        # Extract intent
        intent_match = re.search(r'intent["\s:]+({[^}]+})', text, re.IGNORECASE)
        if intent_match:
            try:
                result['intent'] = json.loads(intent_match.group(1))
            except json.JSONDecodeError:
                result['intent'] = self._extract_intent_from_text(text)
        else:
            result['intent'] = self._extract_intent_from_text(text)
        
        return result
    
    def _extract_intent_from_text(self, text: str) -> Dict[str, Any]:
        """Extract intent from unstructured text."""
        intent = {
            'type': 'unknown',
            'dimensions': [],
            'measures': [],
            'aggregation': None,
            'time_dimension': None
        }
        
        text_lower = text.lower()
        
        # Detect query type
        if 'group by' in text_lower:
            intent['type'] = 'aggregation'
        elif 'join' in text_lower:
            intent['type'] = 'join'
        elif 'where' in text_lower:
            intent['type'] = 'filter'
        else:
            intent['type'] = 'simple'
        
        # Detect aggregation
        agg_patterns = ['sum', 'avg', 'count', 'max', 'min']
        for agg in agg_patterns:
            if agg in text_lower:
                intent['aggregation'] = agg.upper()
                break
        
        # Detect dimensions
        if 'group by' in text_lower:
            group_by_part = text_lower.split('group by')[1].split('order by')[0].strip()
            intent['dimensions'] = [d.strip() for d in group_by_part.split(',')]
        
        return intent