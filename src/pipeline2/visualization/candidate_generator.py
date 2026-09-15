"""Generate chart candidates based on data and roles."""

from typing import Dict, List, Any


class CandidateGenerator:
    """Generate chart candidates."""
    
    def __init__(self):
        self.chart_templates = {
            'bar': {
                'name': 'Bar Chart',
                'mark': 'bar',
                'encoding': {}
            },
            'horizontal_bar': {
                'name': 'Horizontal Bar Chart',
                'mark': 'bar',
                'encoding': {'x': None, 'y': None}
            },
            'line': {
                'name': 'Line Chart',
                'mark': 'line',
                'encoding': {}
            },
            'area': {
                'name': 'Area Chart',
                'mark': 'area',
                'encoding': {}
            },
            'scatter': {
                'name': 'Scatter Plot',
                'mark': 'circle',
                'encoding': {}
            },
            'pie': {
                'name': 'Pie Chart',
                'mark': 'arc',
                'encoding': {}
            },
            'donut': {
                'name': 'Donut Chart',
                'mark': 'arc',
                'encoding': {'innerRadius': 50}
            },
            'heatmap': {
                'name': 'Heatmap',
                'mark': 'rect',
                'encoding': {}
            }
        }
    
    def generate(self, roles: Dict[str, List[str]], profiles: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Generate chart candidates."""
        candidates = []
        
        dimensions = [col for col, role_list in roles.items() if 'dimension' in role_list]
        measures = [col for col, role_list in roles.items() if 'measure' in role_list]
        temporals = [col for col, role_list in roles.items() if 'temporal' in role_list]
        
        # Dimension + Measure -> Bar charts
        if dimensions and measures:
            candidates.extend(self._generate_bar_candidates(dimensions[0], measures[0]))
        
        # Temporal + Measure -> Line/Area charts
        if temporals and measures:
            candidates.extend(self._generate_time_series_candidates(temporals[0], measures[0]))
        
        # Dimension + Dimension + Measure -> Heatmap/Grouped
        if len(dimensions) >= 2 and measures:
            candidates.extend(self._generate_multi_dimension_candidates(dimensions[:2], measures[0]))
        
        # Measure + Measure -> Scatter
        if len(measures) >= 2:
            candidates.extend(self._generate_scatter_candidates(measures[0], measures[1]))
        
        # Dimension + Measure (single) -> Pie
        if dimensions and measures and len(dimensions) == 1 and len(measures) == 1:
            candidates.extend(self._generate_pie_candidates(dimensions[0], measures[0]))
        
        return candidates
    
    def _generate_bar_candidates(self, dimension: str, measure: str) -> List[Dict[str, Any]]:
        """Generate bar chart candidates."""
        return [
            {
                'type': 'bar',
                'name': 'Bar Chart',
                'encoding': {
                    'x': {'field': dimension, 'type': 'nominal'},
                    'y': {'field': measure, 'type': 'quantitative'}
                },
                'score': 0.0
            },
            {
                'type': 'horizontal_bar',
                'name': 'Horizontal Bar Chart',
                'encoding': {
                    'y': {'field': dimension, 'type': 'nominal'},
                    'x': {'field': measure, 'type': 'quantitative'}
                },
                'score': 0.0
            }
        ]
    
    def _generate_time_series_candidates(self, temporal: str, measure: str) -> List[Dict[str, Any]]:
        """Generate time series candidates."""
        return [
            {
                'type': 'line',
                'name': 'Line Chart',
                'encoding': {
                    'x': {'field': temporal, 'type': 'temporal'},
                    'y': {'field': measure, 'type': 'quantitative'}
                },
                'score': 0.0
            },
            {
                'type': 'area',
                'name': 'Area Chart',
                'encoding': {
                    'x': {'field': temporal, 'type': 'temporal'},
                    'y': {'field': measure, 'type': 'quantitative'}
                },
                'score': 0.0
            }
        ]
    
    def _generate_multi_dimension_candidates(self, dimensions: List[str], measure: str) -> List[Dict[str, Any]]:
        """Generate multi-dimension chart candidates."""
        return [
            {
                'type': 'heatmap',
                'name': 'Heatmap',
                'encoding': {
                    'x': {'field': dimensions[0], 'type': 'nominal'},
                    'y': {'field': dimensions[1], 'type': 'nominal'},
                    'color': {'field': measure, 'type': 'quantitative'}
                },
                'score': 0.0
            }
        ]
    
    def _generate_scatter_candidates(self, measure1: str, measure2: str) -> List[Dict[str, Any]]:
        """Generate scatter plot candidates."""
        return [
            {
                'type': 'scatter',
                'name': 'Scatter Plot',
                'encoding': {
                    'x': {'field': measure1, 'type': 'quantitative'},
                    'y': {'field': measure2, 'type': 'quantitative'}
                },
                'score': 0.0
            }
        ]
    
    def _generate_pie_candidates(self, dimension: str, measure: str) -> List[Dict[str, Any]]:
        """Generate pie chart candidates."""
        return [
            {
                'type': 'pie',
                'name': 'Pie Chart',
                'encoding': {
                    'theta': {'field': measure, 'type': 'quantitative'},
                    'color': {'field': dimension, 'type': 'nominal'}
                },
                'score': 0.0
            },
            {
                'type': 'donut',
                'name': 'Donut Chart',
                'encoding': {
                    'theta': {'field': measure, 'type': 'quantitative'},
                    'color': {'field': dimension, 'type': 'nominal'}
                },
                'score': 0.0
            }
        ]