"""Generate Vega-Lite specifications."""

from typing import Dict, List, Any, Optional


class VegaLiteGenerator:
    """Generate Vega-Lite chart specifications."""
    
    def __init__(self):
        self.base_spec = {
            '$schema': 'https://vega.github.io/schema/vega-lite/v5.json',
            'width': 'container',
            'height': 400
        }
    
    def generate(self, data: List[Dict[str, Any]], candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Vega-Lite specification."""
        if not data or not candidate:
            return self._generate_fallback(data)
        
        chart_type = candidate.get('type', 'bar')
        encoding = candidate.get('encoding', {})
        
        spec = {
            **self.base_spec,
            'mark': self._get_mark(chart_type),
            'encoding': self._build_encoding(encoding, data),
            'data': {'values': data}
        }
        
        # Add chart-specific configurations
        if chart_type in ['pie', 'donut']:
            spec['encoding'] = self._build_pie_encoding(spec['encoding'])
        elif chart_type == 'heatmap':
            spec['mark'] = {'type': 'rect', 'tooltip': True}
        
        return spec
    
    def _get_mark(self, chart_type: str) -> Any:
        """Get mark type."""
        marks = {
            'bar': 'bar',
            'horizontal_bar': 'bar',
            'line': 'line',
            'area': 'area',
            'scatter': 'circle',
            'pie': 'arc',
            'donut': 'arc',
            'heatmap': 'rect'
        }
        return marks.get(chart_type, 'bar')
    
    def _build_encoding(self, encoding: Dict, data: List[Dict]) -> Dict:
        """Build encoding with proper field types."""
        built = {}
        
        for channel, field in encoding.items():
            if not field:
                continue
            
            field_name = field.get('field', '')
            field_type = field.get('type', self._infer_type(field_name, data))
            
            built[channel] = {
                'field': field_name,
                'type': field_type
            }
            
            # Add tooltips
            if channel == 'tooltip':
                continue
            if 'tooltip' not in built:
                built['tooltip'] = []
            built['tooltip'].append({'field': field_name, 'type': field_type})
        
        # Sort fields for consistent tooltips
        if 'tooltip' in built:
            built['tooltip'] = list({tuple(t.items()): t for t in built['tooltip']}.values())
        
        return built
    
    def _build_pie_encoding(self, encoding: Dict) -> Dict:
        """Build pie chart encoding."""
        # Convert to pie chart encoding
        theta_field = encoding.get('y', {}).get('field') or encoding.get('x', {}).get('field')
        color_field = encoding.get('color', {}).get('field')
        
        if not theta_field:
            theta_field = encoding.get('x', {}).get('field')
        
        pie_encoding = {
            'theta': {'field': theta_field, 'type': 'quantitative'},
            'color': {'field': color_field or 'key', 'type': 'nominal'},
            'tooltip': [
                {'field': color_field or 'key', 'type': 'nominal'},
                {'field': theta_field, 'type': 'quantitative'}
            ]
        }
        
        # Add inner radius for donut
        if encoding.get('innerRadius'):
            pie_encoding['innerRadius'] = encoding['innerRadius']
        
        return pie_encoding
    
    def _infer_type(self, field_name: str, data: List[Dict]) -> str:
        """Infer field type from data."""
        if not data:
            return 'nominal'
        
        values = [row.get(field_name) for row in data if row.get(field_name) is not None]
        if not values:
            return 'nominal'
        
        # Check for numeric
        if all(isinstance(v, (int, float)) for v in values):
            return 'quantitative'
        
        # Check for datetime
        if any(isinstance(v, str) and any(d in v.lower() for d in ['date', 'time']) for v in values):
            return 'temporal'
        
        # Check cardinality
        unique_count = len(set(values))
        if unique_count <= 10:
            return 'nominal'
        
        return 'nominal'
    
    def _generate_fallback(self, data: List[Dict]) -> Dict[str, Any]:
        """Generate fallback specification."""
        if not data:
            return {
                **self.base_spec,
                'mark': 'text',
                'encoding': {
                    'text': {'value': 'No data available'}
                }
            }
        
        # Try to find first columns
        columns = list(data[0].keys())
        if len(columns) >= 2:
            return self.generate(
                data,
                {
                    'type': 'bar',
                    'encoding': {
                        'x': {'field': columns[0], 'type': 'nominal'},
                        'y': {'field': columns[1], 'type': 'quantitative'}
                    }
                }
            )
        
        return {
            **self.base_spec,
            'mark': 'text',
            'encoding': {
                'text': {'value': 'Insufficient data for visualization'}
            }
        }