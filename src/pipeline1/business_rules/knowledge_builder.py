"""Build enterprise knowledge graph."""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KnowledgeBuilder:
    """Build knowledge graph from schema and business rules."""
    
    def __init__(self, schema: Dict[str, Any], rules: Dict[str, Any]):
        self.schema = schema
        self.rules = rules
        self.knowledge_graph = {
            'entities': {},
            'relationships': {},
            'rules': {},
            'mappings': {}
        }
    
    def build_knowledge_graph(self) -> Dict[str, Any]:
        """Build complete knowledge graph."""
        self._build_entities()
        self._build_relationships()
        self._build_rules()
        self._build_mappings()
        return self.knowledge_graph
    
    def _build_entities(self):
        """Build entity nodes from schema."""
        for schema in self.schema.get('schemas', []):
            for table in schema['tables']:
                entity = {
                    'name': table['name'],
                    'schema': schema['name'],
                    'attributes': [],
                    'business_meaning': self._get_business_meaning(table['name'])
                }
                
                for col in table['columns']:
                    entity['attributes'].append({
                        'name': col['name'],
                        'type': col['type'],
                        'business_meaning': self._get_business_meaning(col['name']),
                        'is_identifier': col.get('primary_key', False)
                    })
                
                self.knowledge_graph['entities'][table['name']] = entity
    
    def _build_relationships(self):
        """Build relationship edges."""
        for table_key, fks in self.schema.get('relationships', {}).items():
            for fk in fks:
                source = table_key
                target = fk['referred_table']
                rel = {
                    'source': source,
                    'target': target,
                    'source_columns': fk['constrained_columns'],
                    'target_columns': fk['referred_columns'],
                    'type': 'foreign_key'
                }
                
                if source not in self.knowledge_graph['relationships']:
                    self.knowledge_graph['relationships'][source] = []
                self.knowledge_graph['relationships'][source].append(rel)
    
    def _build_rules(self):
        """Build business rules."""
        for rule_name, rule_data in self.rules.get('rules', {}).items():
            self.knowledge_graph['rules'][rule_name] = {
                'name': rule_name,
                'definition': rule_data.get('definition', ''),
                'conditions': rule_data.get('conditions', []),
                'inclusions': rule_data.get('inclusions', []),
                'exclusions': rule_data.get('exclusions', []),
                'applicable_tables': self._find_applicable_tables(rule_data)
            }
    
    def _build_mappings(self):
        """Build terminology mappings."""
        for term, info in self.rules.get('terminology', {}).items():
            self.knowledge_graph['mappings'][term] = {
                'term': term,
                'meaning': info.get('meaning', ''),
                'synonyms': info.get('synonyms', []),
                'mapped_tables': self._find_mapped_tables(term),
                'mapped_columns': self._find_mapped_columns(term)
            }
    
    def _get_business_meaning(self, name: str) -> str:
        """Get business meaning from terminology."""
        name_lower = name.lower()
        
        # Check definitions
        for term, definition in self.rules.get('definitions', {}).items():
            if term in name_lower or name_lower in term:
                return definition
        
        # Check terminology
        for term, info in self.rules.get('terminology', {}).items():
            if term in name_lower or name_lower in term:
                return info.get('meaning', '')
        
        return f"Business meaning not defined for {name}"
    
    def _find_applicable_tables(self, rule_data: Dict[str, Any]) -> List[str]:
        """Find tables applicable to a rule."""
        applicable = []
        rule_text = str(rule_data)
        
        for table_name in self.knowledge_graph['entities'].keys():
            if table_name.lower() in rule_text.lower():
                applicable.append(table_name)
        
        return applicable
    
    def _find_mapped_tables(self, term: str) -> List[str]:
        """Find tables mapped to a term."""
        mapped = []
        term_lower = term.lower()
        
        for table_name in self.knowledge_graph['entities'].keys():
            if term_lower in table_name.lower() or table_name.lower() in term_lower:
                mapped.append(table_name)
        
        return mapped
    
    def _find_mapped_columns(self, term: str) -> List[str]:
        """Find columns mapped to a term."""
        mapped = []
        term_lower = term.lower()
        
        for entity in self.knowledge_graph['entities'].values():
            for attr in entity.get('attributes', []):
                if term_lower in attr['name'].lower() or attr['name'].lower() in term_lower:
                    mapped.append({
                        'table': entity['name'],
                        'column': attr['name']
                    })
        
        return mapped