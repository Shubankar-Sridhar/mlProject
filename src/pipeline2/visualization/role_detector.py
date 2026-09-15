"""Detect semantic roles of columns."""

from typing import Dict, List, Any, Set
import re


class SemanticRoleDetector:
    """Detect semantic roles for columns."""
    
    def __init__(self):
        self.role_patterns = {
            'identifier': [r'_id$', r'^id$', r'^pk_'],
            'temporal': [r'date', r'time', r'timestamp', r'created_at', r'updated_at'],
            'measure': [r'amount', r'total', r'sum', r'avg', r'count', r'price', r'cost', r'revenue'],
            'dimension': [r'name', r'category', r'type', r'status', r'city', r'country', r'region']
        }
    
    def detect_roles(self, profiles: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Detect roles for each column."""
        roles = {}
        
        for col_name, profile in profiles.items():
            roles[col_name] = self._detect_single_role(col_name, profile)
        
        return roles
    
    def _detect_single_role(self, col_name: str, profile: Dict[str, Any]) -> List[str]:
        """Detect roles for a single column."""
        roles = []
        
        col_lower = col_name.lower()
        
        # Check patterns
        for role, patterns in self.role_patterns.items():
            if any(re.search(p, col_lower) for p in patterns):
                roles.append(role)
        
        # Type-based roles
        col_type = profile.get('type', 'unknown')
        if col_type == 'quantitative' and 'measure' not in roles:
            roles.append('measure')
        elif col_type in ['categorical', 'nominal'] and 'dimension' not in roles:
            roles.append('dimension')
        elif col_type == 'temporal' and 'temporal' not in roles:
            roles.append('temporal')
        
        # Unique ratio based roles
        unique_ratio = profile.get('unique_ratio', 0)
        if unique_ratio > 0.9 and 'identifier' not in roles:
            roles.append('identifier')
        
        # If still no roles, assign based on type
        if not roles:
            if col_type == 'quantitative':
                roles.append('measure')
            elif col_type in ['categorical', 'nominal']:
                roles.append('dimension')
            else:
                roles.append('unknown')
        
        return roles
    
    def identify_dimensions(self, roles: Dict[str, List[str]]) -> List[str]:
        """Identify dimension columns."""
        return [col for col, role_list in roles.items() if 'dimension' in role_list]
    
    def identify_measures(self, roles: Dict[str, List[str]]) -> List[str]:
        """Identify measure columns."""
        return [col for col, role_list in roles.items() if 'measure' in role_list]
    
    def identify_temporal(self, roles: Dict[str, List[str]]) -> List[str]:
        """Identify temporal columns."""
        return [col for col, role_list in roles.items() if 'temporal' in role_list]