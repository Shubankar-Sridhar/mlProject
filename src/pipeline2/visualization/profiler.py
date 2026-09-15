"""Profile query results for visualization."""

from typing import Dict, List, Any, Optional
import datetime
import statistics


class ResultProfiler:
    """Profile result data for visualization."""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.profiles = {}
    
    def profile_columns(self) -> Dict[str, Dict[str, Any]]:
        """Profile all columns."""
        if not self.data:
            return {}
        
        for col_name in self.data[0].keys():
            self.profiles[col_name] = self._profile_column(col_name)
        
        return self.profiles
    
    def _profile_column(self, col_name: str) -> Dict[str, Any]:
        """Profile a single column."""
        values = [row.get(col_name) for row in self.data if row.get(col_name) is not None]
        
        if not values:
            return {
                'type': 'unknown',
                'null_ratio': 1.0,
                'cardinality': 0
            }
        
        # Detect type
        type_info = self._detect_type(values)
        
        # Compute statistics
        profile = {
            'type': type_info['type'],
            'physical_type': type_info.get('physical', 'unknown'),
            'null_ratio': 1 - (len(values) / len(self.data)),
            'cardinality': len(set(values)),
            'unique_ratio': len(set(values)) / len(values) if values else 0
        }
        
        # Additional stats for numeric columns
        if type_info['type'] in ['quantitative', 'numeric']:
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                profile.update({
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'mean': statistics.mean(numeric_values),
                    'median': statistics.median(numeric_values)
                })
                if len(numeric_values) > 1:
                    profile['stdev'] = statistics.stdev(numeric_values)
        
        # Sample values
        sample_size = min(5, len(values))
        profile['sample_values'] = values[:sample_size]
        
        return profile
    
    def _detect_type(self, values: List[Any]) -> Dict[str, str]:
        """Detect column type from values."""
        # Check if all numeric
        all_numeric = all(isinstance(v, (int, float)) for v in values)
        if all_numeric:
            return {'type': 'quantitative', 'physical': 'numeric'}
        
        # Check if all boolean
        all_bool = all(isinstance(v, bool) for v in values)
        if all_bool:
            return {'type': 'nominal', 'physical': 'boolean'}
        
        # Check if all datetime
        all_datetime = all(
            isinstance(v, (datetime.datetime, str)) and (
                isinstance(v, datetime.datetime) or 
                (isinstance(v, str) and any(d in v.lower() for d in ['date', 'time']))
            ) for v in values
        )
        if all_datetime:
            return {'type': 'temporal', 'physical': 'datetime'}
        
        # Default to string/categorical
        unique_ratio = len(set(values)) / len(values) if values else 0
        if unique_ratio < 0.2:
            return {'type': 'categorical', 'physical': 'string'}
        else:
            return {'type': 'nominal', 'physical': 'string'}