"""Schema serialization to various formats."""

import json
from typing import Dict, Any, List
from datetime import datetime


class SchemaSerializer:
    """Serialize schema to various formats."""
    
    def serialize(self, schema_data: Dict[str, Any]) -> str:
        """Serialize schema to JSON."""
        return json.dumps(schema_data, indent=2, default=str)
    
    def to_markdown(self, schema_data: Dict[str, Any]) -> str:
        """Convert schema to Markdown."""
        lines = [
            "# Database Schema Documentation",
            f"\n**Extracted At:** {schema_data.get('extracted_at', 'Unknown')}",
            f"**Database:** {schema_data.get('database', {}).get('type', 'Unknown')}",
            "\n## Tables\n"
        ]
        
        for schema in schema_data.get('schemas', []):
            lines.append(f"\n### Schema: {schema['name']}\n")
            
            for table in schema['tables']:
                lines.append(f"\n#### Table: {table['name']}")
                if table.get('description'):
                    lines.append(f"*{table['description']}*")
                
                lines.append("\n| Column | Type | Nullable | PK | FK |")
                lines.append("|--------|------|----------|----|----|")
                
                for col in table['columns']:
                    pk = "✓" if col.get('primary_key') else ""
                    fk = "✓" if col.get('foreign_key') else ""
                    lines.append(
                        f"| {col['name']} | {col['type']} | "
                        f"{'Yes' if col.get('nullable') else 'No'} | "
                        f"{pk} | {fk} |"
                    )
        
        return "\n".join(lines)
    
    def to_yaml(self, schema_data: Dict[str, Any]) -> str:
        """Convert schema to YAML."""
        import yaml
        return yaml.dump(schema_data, default_flow_style=False)