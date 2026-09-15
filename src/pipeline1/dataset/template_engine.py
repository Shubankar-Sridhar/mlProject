"""Template engine for generating SQL and questions."""

import re
import random
from typing import Dict, List, Any, Optional


class TemplateEngine:
    """Generate SQL and questions from templates."""
    
    def __init__(self):
        self.templates = {
            'sql': self._init_sql_templates(),
            'questions': self._init_question_templates()
        }
    
    def _init_sql_templates(self) -> Dict[str, str]:
        """Initialize SQL templates."""
        return {
            'simple_select': "SELECT {columns} FROM {table}",
            'select_limit': "SELECT {columns} FROM {table} LIMIT {limit}",
            'select_where': "SELECT {columns} FROM {table} WHERE {condition}",
            'select_where_limit': "SELECT {columns} FROM {table} WHERE {condition} LIMIT {limit}",
            'select_order': "SELECT {columns} FROM {table} ORDER BY {order_column} {order_dir}",
            'select_group': "SELECT {group_columns}, {agg_function}({agg_column}) FROM {table} GROUP BY {group_columns}",
            'select_group_order': "SELECT {group_columns}, {agg_function}({agg_column}) FROM {table} GROUP BY {group_columns} ORDER BY {agg_function}({agg_column}) DESC",
            'select_join': "SELECT {columns} FROM {table1} JOIN {table2} ON {join_condition}",
            'select_join_group': "SELECT {group_columns}, {agg_function}({agg_column}) FROM {table1} JOIN {table2} ON {join_condition} GROUP BY {group_columns}",
            'select_join_group_order': "SELECT {group_columns}, {agg_function}({agg_column}) FROM {table1} JOIN {table2} ON {join_condition} GROUP BY {group_columns} ORDER BY {agg_function}({agg_column}) DESC",
            'select_subquery': "SELECT {columns} FROM {table} WHERE {column} IN (SELECT {sub_column} FROM {sub_table} WHERE {sub_condition})",
            'select_with_cte': "WITH {cte_name} AS (SELECT {cte_columns} FROM {cte_table}) SELECT {columns} FROM {cte_name}"
        }
    
    def _init_question_templates(self) -> Dict[str, List[str]]:
        """Initialize question templates."""
        return {
            'simple_select': [
                "Show me {columns} from {table}",
                "What are the {columns} in {table}?",
                "Give me {columns} for {table}",
                "List the {columns} of {table}"
            ],
            'select_where': [
                "Show me {columns} from {table} where {condition}",
                "What are the {columns} where {condition} in {table}?",
                "Give me {columns} for {table} with {condition}",
                "List the {columns} of {table} where {condition}"
            ],
            'select_group': [
                "Show me {agg_function} of {agg_column} by {group_columns}",
                "What is the {agg_function} of {agg_column} for each {group_columns}?",
                "Give me {agg_function} of {agg_column} grouped by {group_columns}",
                "List the {agg_function} of {agg_column} by {group_columns}"
            ],
            'select_join': [
                "Show me {columns} from {table1} and {table2}",
                "What are the {columns} joining {table1} and {table2}?",
                "Give me {columns} combining {table1} with {table2}",
                "List the {columns} from {table1} and {table2}"
            ],
            'select_join_group': [
                "Show me {agg_function} of {agg_column} by {group_columns} using {table1} and {table2}",
                "What is the {agg_function} of {agg_column} for each {group_columns} joining {table1} and {table2}?",
                "Give me {agg_function} of {agg_column} grouped by {group_columns} with {table1} and {table2}",
                "List the {agg_function} of {agg_column} by {group_columns} combining {table1} and {table2}"
            ]
        }
    
    def render_sql(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render SQL from template."""
        template = self.templates['sql'].get(template_name)
        if not template:
            return ""
        
        return template.format(**context)
    
    def render_question(self, template_type: str, context: Dict[str, Any]) -> str:
        """Render question from template."""
        templates = self.templates['questions'].get(template_type, [])
        if not templates:
            return ""
        
        template = random.choice(templates)
        return template.format(**context)
    
    def generate_pair(self, sql_template: str, question_type: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate a SQL-question pair."""
        return {
            'sql': self.render_sql(sql_template, context),
            'question': self.render_question(question_type, context)
        }