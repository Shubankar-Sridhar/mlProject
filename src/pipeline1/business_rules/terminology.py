"""Terminology extraction and management."""

import re
from typing import Dict, List, Set, Optional
import json
import logging

logger = logging.getLogger(__name__)


class TerminologyExtractor:
    """Extract and manage terminology from business documents."""
    
    def __init__(self):
        self.terminology = {}
        self.acronyms = {}
        self.synonym_groups = {}
    
    def build_terminology_dictionary(self, documents: List[str]) -> Dict[str, Any]:
        """Build terminology dictionary from multiple documents."""
        for doc in documents:
            self._process_document(doc)
        
        return {
            'terminology': self.terminology,
            'acronyms': self.acronyms,
            'synonym_groups': self.synonym_groups
        }
    
    def _process_document(self, content: str):
        """Process a single document for terminology."""
        # Extract term definitions
        term_pattern = r'^([A-Za-z\s_\-]+?)\s*[:=]\s*(.+?)(?=\n\s*[A-Za-z]|$)'
        terms = re.findall(term_pattern, content, re.MULTILINE | re.DOTALL)
        
        for term, definition in terms:
            term = term.strip().lower()
            definition = definition.strip()
            self.terminology[term] = {
                'definition': definition,
                'synonyms': self._extract_synonyms(definition),
                'acronym': self._extract_acronym(term)
            }
            
            if self.terminology[term]['acronym']:
                self.acronyms[self.terminology[term]['acronym']] = term
        
        # Extract acronyms
        acronym_pattern = r'\(([A-Z]{2,})\)'
        acronyms = re.findall(acronym_pattern, content)
        for acronym in acronyms:
            # Try to find the full term before the acronym
            full_match = re.search(r'([A-Za-z\s]+)\s*\(%s\)' % re.escape(acronym), content)
            if full_match:
                full_term = full_match.group(1).strip().lower()
                self.acronyms[acronym.lower()] = full_term
    
    def extract_synonyms(self, terms: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract synonym relationships."""
        synonym_groups = {}
        
        for term, info in terms.items():
            synonyms = info.get('synonyms', [])
            if synonyms:
                # Find or create synonym group
                group_id = None
                for existing_group in synonym_groups.values():
                    if term in existing_group or any(s in existing_group for s in synonyms):
                        group_id = id(existing_group)
                        break
                
                if group_id is None:
                    # Create new group
                    group_id = len(synonym_groups) + 1
                    synonym_groups[str(group_id)] = [term] + synonyms
                else:
                    # Add to existing group
                    for g in synonym_groups.values():
                        if id(g) == group_id:
                            if term not in g:
                                g.append(term)
                            for s in synonyms:
                                if s not in g:
                                    g.append(s)
                            break
        
        return synonym_groups
    
    def _extract_synonyms(self, text: str) -> List[str]:
        """Extract synonyms from definition text."""
        synonyms = []
        
        # Look for "also known as", "or", "aka"
        patterns = [
            r'also known as\s+([^,;.]+)',
            r'\(or\s+([^)]+?)\)',
            r'aka\s+([^,;.]+)',
            r'synonym[s]?\s+([^,;.]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Split by commas and clean
                for syn in re.split(r',|\sand\s', match):
                    syn = syn.strip().lower()
                    if syn and len(syn) > 1:
                        synonyms.append(syn)
        
        return list(set(synonyms))
    
    def _extract_acronym(self, text: str) -> Optional[str]:
        """Extract acronym from text."""
        # Look for acronym in parentheses
        match = re.search(r'\(([A-Z]{2,})\)', text)
        if match:
            return match.group(1)
        return None
    
    def map_terms_to_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Map terminology to schema elements."""
        mappings = {
            'table_mappings': {},
            'column_mappings': {},
            'relationship_mappings': {}
        }
        
        # Map terms to tables
        for term in self.terminology.keys():
            for schema_obj in schema.get('schemas', []):
                for table in schema_obj['tables']:
                    if term in table['name'].lower() or table['name'].lower() in term:
                        mappings['table_mappings'][term] = {
                            'table': table['name'],
                            'schema': schema_obj['name'],
                            'confidence': 'high'
                        }
        
        # Map terms to columns
        for term in self.terminology.keys():
            for schema_obj in schema.get('schemas', []):
                for table in schema_obj['tables']:
                    for col in table['columns']:
                        if term in col['name'].lower() or col['name'].lower() in term:
                            mappings['column_mappings'][term] = {
                                'table': table['name'],
                                'column': col['name'],
                                'schema': schema_obj['name'],
                                'confidence': 'medium'
                            }
        
        return mappings