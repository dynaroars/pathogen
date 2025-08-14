#!/usr/bin/env python3
"""
JSON parser for PathoGen testing.
This implementation uses recursive parsing that can be slow
on deeply nested JSON structures.
"""

import sys
import json

def recursive_json_process(data, depth=0):
    """
    Recursively process JSON data with intentional inefficiency
    to create pathological cases for deeply nested structures.
    """
    if depth > 1000:  # Prevent infinite recursion
        return data
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Intentionally inefficient processing
            processed_key = str(key) * (depth + 1) if depth < 10 else key
            result[processed_key] = recursive_json_process(value, depth + 1)
        return result
    elif isinstance(data, list):
        result = []
        for i, item in enumerate(data):
            # More processing for nested arrays
            processed_item = recursive_json_process(item, depth + 1)
            result.append(processed_item)
        return result
    else:
        # Process primitive values
        if isinstance(data, str) and depth > 0:
            return data * min(depth, 5)  # String multiplication based on depth
        return data

def main():
    try:
        # Read input from stdin
        input_line = sys.stdin.read().strip()
        
        # Parse JSON
        try:
            data = json.loads(input_line)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format - {e}", file=sys.stderr)
            sys.exit(1)
        
        # Process the JSON recursively
        processed_data = recursive_json_process(data)
        
        # Output result
        result = {
            "original_type": type(data).__name__,
            "processed": processed_data,
            "depth_processed": True
        }
        
        print(json.dumps(result))
        
    except RecursionError:
        print("Error: JSON structure too deeply nested", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()