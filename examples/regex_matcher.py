#!/usr/bin/env python3
"""
Regex matching program for PathoGen testing.
This can exhibit exponential time complexity with certain patterns
due to catastrophic backtracking.
"""

import sys
import re
import json

def main():
    try:
        # Read input from stdin
        input_line = sys.stdin.read().strip()
        
        # Parse JSON input with pattern and text
        data = json.loads(input_line)
        
        # Validate input structure
        if not isinstance(data, dict):
            print(f"Error: Expected JSON object, got {type(data).__name__}", file=sys.stderr)
            sys.exit(1)
            
        if 'pattern' not in data or 'text' not in data:
            print("Error: JSON must contain 'pattern' and 'text' fields", file=sys.stderr)
            sys.exit(1)
        
        pattern = data['pattern']
        text = data['text']
        
        # Validate types
        if not isinstance(pattern, str) or not isinstance(text, str):
            print("Error: Both 'pattern' and 'text' must be strings", file=sys.stderr)
            sys.exit(1)
        
        # Compile and match regex
        try:
            compiled_pattern = re.compile(pattern)
            match = compiled_pattern.search(text)
            
            if match:
                result = {
                    "matched": True,
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end()
                }
            else:
                result = {"matched": False}
            
            print(json.dumps(result))
            
        except re.error as e:
            print(f"Error: Invalid regex pattern - {e}", file=sys.stderr)
            sys.exit(1)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()