"""Score chart candidates for selection."""

from typing import Dict, List, Any, Optional


class ChartScorer:
    """Score chart candidates."""
    
    def __init__(self):
        self.weights = {
            'semantic_fit': 0.30,
            'cardinality_fit': 0.20,
            'temporal_fit': 0.20,
            'readability': 0.15,
            'intent_fit': 0.15
        }
    
    def score(self, candidate: Dict[str, Any], roles: Dict[str, List[str]], 
              profiles: Dict[str, Dict], intent: Dict[str, Any]) -> float:
        """Score a single candidate."""
        score = 0.0
        
        # Semantic fit
        score += self._score_semantic_fit(candidate, roles) * self.weights['semantic_fit']
        
        # Cardinality fit
        score += self._score_cardinality_fit(candidate, profiles) * self.weights['cardinality_fit']
        
        # Temporal fit
        score += self._score_temporal_fit(candidate, roles) * self.weights['temporal_fit']
        
        # Readability
        score += self._score_readability(candidate) * self.weights['readability']
        
        # Intent fit
        score += self._score_intent_fit(candidate, intent) * self.weights['intent_fit']
        
        return score
    
    def select_best(self, candidates: List[Dict[str, Any]], 
                    roles: Dict[str, List[str]], 
                    profiles: Dict[str, Dict],
                    intent: Dict[str, Any]) -> Dict[str, Any] | None:
        """Select the best chart candidate."""
        if not candidates:
            return None
        
        for candidate in candidates:
            candidate['score'] = self.score(candidate, roles, profiles, intent)
        
        return max(candidates, key=lambda x: x['score'])
    
    def _score_semantic_fit(self, candidate: Dict[str, Any], roles: Dict[str, List[str]]) -> float:
        """Score semantic fit."""
        encoding = candidate.get('encoding', {})
        if not encoding:
            return 0.5
        
        score = 0.0
        total = 0
        
        # Check each encoding channel
        for channel, field in encoding.items():
            if not field:
                continue
            field_name = field.get('field', '')
            field_type = field.get('type', '')
            
            # Check if field type matches role
            field_roles = roles.get(field_name, [])
            if 'dimension' in field_roles and field_type in ['nominal', 'ordinal']:
                score += 1.0
            elif 'measure' in field_roles and field_type == 'quantitative':
                score += 1.0
            elif 'temporal' in field_roles and field_type == 'temporal':
                score += 1.0
            else:
                score += 0.5
            
            total += 1
        
        return score / total if total > 0 else 0.5
    
    def _score_cardinality_fit(self, candidate: Dict[str, Any], 
                                profiles: Dict[str, Dict]) -> float:
        """Score cardinality fit."""
        encoding = candidate.get('encoding', {})
        if not encoding:
            return 0.5
        
        score = 0.0
        total = 0
        
        for channel, field in encoding.items():
            if not field:
                continue
            field_name = field.get('field', '')
            profile = profiles.get(field_name, {})
            cardinality = profile.get('cardinality', 0)
            
            # Bar charts work well with moderate cardinality
            if candidate['type'] in ['bar', 'horizontal_bar']:
                if 1 <= cardinality <= 20:
                    score += 1.0
                elif cardinality <= 50:
                    score += 0.7
                else:
                    score += 0.3
            
            # Pie charts need low cardinality
            elif candidate['type'] in ['pie', 'donut']:
                if 1 <= cardinality <= 7:
                    score += 1.0
                elif cardinality <= 10:
                    score += 0.6
                else:
                    score += 0.1
            
            # Line charts need temporal or ordered data
            elif candidate['type'] in ['line', 'area']:
                if profile.get('type') == 'temporal':
                    score += 1.0
                elif cardinality <= 30:
                    score += 0.7
                else:
                    score += 0.4
            
            # Scatter plots need enough points
            elif candidate['type'] == 'scatter':
                if cardinality >= 10:
                    score += 1.0
                elif cardinality >= 5:
                    score += 0.6
                else:
                    score += 0.2
            
            # Heatmaps need moderate cardinality
            elif candidate['type'] == 'heatmap':
                if 1 <= cardinality <= 10:
                    score += 1.0
                elif cardinality <= 20:
                    score += 0.7
                else:
                    score += 0.3
            
            total += 1
        
        return score / total if total > 0 else 0.5
    
    def _score_temporal_fit(self, candidate: Dict[str, Any], roles: Dict[str, List[str]]) -> float:
        """Score temporal fit."""
        encoding = candidate.get('encoding', {})
        if not encoding:
            return 0.5
        
        # Check if temporal fields are present
        has_temporal = any(
            'temporal' in roles.get(field.get('field', ''), [])
            for field in encoding.values() if field
        )
        
        # Line charts are best for temporal data
        if has_temporal:
            if candidate['type'] in ['line', 'area']:
                return 1.0
            elif candidate['type'] in ['bar']:
                return 0.7
            else:
                return 0.4
        
        return 0.5
    
    def _score_readability(self, candidate: Dict[str, Any]) -> float:
        """Score readability."""
        encoding = candidate.get('encoding', {})
        
        # Check for conflicting encodings
        has_color = 'color' in encoding and encoding['color']
        has_x = 'x' in encoding and encoding['x']
        has_y = 'y' in encoding and encoding['y']
        
        # Simpler charts are more readable
        if candidate['type'] in ['bar', 'line', 'pie']:
            return 0.9
        elif candidate['type'] in ['scatter', 'horizontal_bar']:
            return 0.8
        elif candidate['type'] in ['area', 'donut']:
            return 0.7
        elif candidate['type'] == 'heatmap':
            return 0.6
        else:
            return 0.5
    
    def _score_intent_fit(self, candidate: Dict[str, Any], intent: Dict[str, Any]) -> float:
        """Score intent fit."""
        intent_type = intent.get('type', 'unknown')
        
        # Map intent types to chart types
        intent_chart_map = {
            'ranking': ['bar', 'horizontal_bar'],
            'comparison': ['bar', 'horizontal_bar'],
            'distribution': ['scatter', 'histogram'],
            'trend': ['line', 'area'],
            'part_to_whole': ['pie', 'donut'],
            'correlation': ['scatter'],
            'unknown': ['bar', 'line']
        }
        
        recommended = intent_chart_map.get(intent_type, ['bar'])
        if candidate['type'] in recommended:
            return 1.0
        
        return 0.5