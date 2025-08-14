# Input parsing utilities
# Provides functions to parse various input formats (JSON, Python literals, CSV, etc.)

import json
import ast
import re
from typing import Any, List, Dict, Union

class InputParser:
    """Parse various input formats"""

    @staticmethod
    def parse_json(input_str: str) -> Any:
        """Parse JSON input"""
        try:
            return json.loads(input_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    @staticmethod
    def parse_python_literal(input_str: str) -> Any:
        """Parse Python literal (list, dict, etc.)"""
        try:
            return ast.literal_eval(input_str)
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Invalid Python literal: {e}")

    @staticmethod
    def parse_csv_line(input_str: str) -> List[str]:
        """Parse comma-separated values"""
        return [item.strip() for item in input_str.split(',')]

    @staticmethod
    def parse_space_separated(input_str: str) -> List[str]:
        """Parse space-separated values"""
        return input_str.split()

    @staticmethod
    def auto_parse(input_str: str) -> Any:
        """Automatically detect and parse input format"""
        input_str = input_str.strip()

        # Try JSON first
        if input_str.startswith(('{', '[')):
            try:
                return InputParser.parse_json(input_str)
            except ValueError:
                pass

        # Try Python literal
        try:
            return InputParser.parse_python_literal(input_str)
        except ValueError:
            pass

        # Try CSV if contains commas
        if ',' in input_str:
            return InputParser.parse_csv_line(input_str)

        # Default to space-separated
        return InputParser.parse_space_separated(input_str)
