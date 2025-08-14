#!/usr/bin/env python3
"""
Quicksort implementation for PathoGen testing.
This implementation uses the first element as pivot, which exhibits 
O(n²) worst-case behavior on already sorted arrays.
"""

import sys
import ast

def quicksort(arr):
    """
    Quicksort implementation with first element as pivot.
    This exhibits O(n²) worst-case behavior on sorted arrays.
    """
    if len(arr) <= 1:
        return arr

    pivot = arr[0]  # First element as pivot (worst-case for sorted arrays)
    left = []
    right = []

    for i in range(1, len(arr)):
        if arr[i] <= pivot:
            left.append(arr[i])
        else:
            right.append(arr[i])

    return quicksort(left) + [pivot] + quicksort(right)

def main():
    try:
        # Read input from stdin
        input_line = sys.stdin.read().strip()
        
        # Parse the input as a Python list
        arr = ast.literal_eval(input_line)
        
        # Validate input is a list
        if not isinstance(arr, list):
            print(f"Error: Expected list, got {type(arr).__name__}", file=sys.stderr)
            sys.exit(1)
            
        # Validate all elements are numbers
        for item in arr:
            if not isinstance(item, (int, float)):
                print(f"Error: All elements must be numbers, found {type(item).__name__}: {item}", file=sys.stderr)
                sys.exit(1)
        
        # Sort the array
        sorted_arr = quicksort(arr)
        print(sorted_arr)
        
    except ValueError as e:
        print(f"Error: Invalid input format - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()