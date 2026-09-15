"""Parse business rule documents."""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BusinessRuleParser:
    """Parse business rule documents and extract structured knowledge."""
    
    def __init__(self):
        self.rules = {}
        self.definitions = {}
        self.terminology = {}
    
    def parse_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """Parse multiple business rule documents."""
        all_rules = {
            'rules': {},
            'definitions': {},
            'terminology': {},
            'sql_patterns': {}
        }
        
        for path in file_paths:
            content = self._read_file(path)
            parsed = self.parse_document(content)
            
            all_rules['rules'].update(parsed.get('rules', {}))
            all_rules['definitions'].update(parsed.get('definitions', {}))
            all_rules['terminology'].update(parsed.get('terminology', {}))
            all_rules['sql_patterns'].update(parsed.get('sql_patterns', {}))
        
        return all_rules
    
    def parse_document(self, content: str) -> Dict[str, Any]:
        """Parse a single business rule document."""
        result = {
            'rules': {},
            'definitions': {},
            'terminology': {},
            'sql_patterns': {}
        }
        
        # Extract definitions (terms followed by colon and definition)
        definition_pattern = r'([A-Za-z\s_]+?)\s*[:=]\s*(.+?)(?=\n\s*[A-Za-z]|$)'
        definitions = re.findall(definition_pattern, content, re.DOTALL)
        for term, definition in definitions:
            term = term.strip()
            definition = definition.strip()
            result['definitions'][term.lower()] = definition
            
            # Extract conditions from definition
            conditions = self._extract_conditions(definition)
            if conditions:
                result['rules'][term.lower()] = {
                    'definition': definition,
                    'conditions': conditions,
                    'inclusions': self._extract_inclusions(definition),
                    'exclusions': self._extract_exclusions(definition)
                }
        
        # Extract terminology (term -> synonym mappings)
        term_pattern = r'([A-Za-z\s_]+)\s*(?:means|is|are|refers to)\s*(.+?)(?:\n|$)'
        terms = re.findall(term_pattern, content, re.IGNORECASE)
        for term, meaning in terms:
            term = term.strip().lower()
            meaning = meaning.strip()
            result['terminology'][term] = {
                'meaning': meaning,
                'synonyms': self._extract_synonyms(meaning)
            }
        
        # Extract SQL patterns
        sql_pattern = r'```sql\s*(.+?)\s*```'
        sqls = re.findall(sql_pattern, content, re.DOTALL)
        for i, sql in enumerate(sqls):
            result['sql_patterns'][f'pattern_{i+1}'] = sql.strip()
        
        return result
    
    def _read_file(self, path: str) -> str:
        """Read file content."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {path}: {str(e)}")
            return ""
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditions from definition."""
        conditions = []
        
        # Look for "if", "when", "where", "excluding"
        if_pattern = r'(?:if|when|where)\s+(.+?)(?:,|\.|;|$)'
        conditions.extend(re.findall(if_pattern, text, re.IGNORECASE))
        
        return conditions
    
    def _extract_inclusions(self, text: str) -> List[str]:
        """Extract inclusion criteria."""
        inclusions = []
        
        # Look for "includes", "including", "such as"
        include_pattern = r'(?:includes?|including)\s+(.+?)(?:,|\.|;|$)'
        inclusions.extend(re.findall(include_pattern, text, re.IGNORECASE))
        
        return inclusions
    
    def _extract_exclusions(self, text: str) -> List[str]:
        """Extract exclusion criteria."""
        exclusions = []
        
        # Look for "excludes", "excluding", "except"
        exclude_pattern = r'(?:excludes?|excluding|except)\s+(.+?)(?:,|\.|;|$)'
        exclusions.extend(re.findall(exclude_pattern, text, re.IGNORECASE))
        
        return exclusions
    
    def _extract_synonyms(self, text: str) -> List[str]:
        """Extract synonyms from text."""
        synonyms = []
        
        # Look for synonyms in parentheses
        syn_pattern = r'\((?:aka|also known as|or)\s+([^)]+?)\)'
        syns = re.findall(syn_pattern, text, re.IGNORECASE)
        for syn in syns:
            synonyms.extend([s.strip() for s in syn.split(',')])
        
        return synonyms