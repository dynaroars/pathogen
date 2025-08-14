"""
Pytest configuration file
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for all tests
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

@pytest.fixture
def temp_config():
    """Create temporary configuration file for testing"""
    config_content = """
pathogen:
  max_iterations: 10
  population_size: 5
  elite_size: 2
  timeout_seconds: 10
  log_level: INFO
  output_dir: reports
  resource_metrics:
    - instruction_count
  llm:
    provider: groq
    model: llama2-70b-4096
    temperature: 0.7
  input_generation:
    inputs_per_iteration: 5
    size_progression:
      start_size: 10
      increment: 5
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    yield config_path

    # Cleanup
    try:
        os.unlink(config_path)
    except:
        pass

@pytest.fixture
def sample_execution_result():
    """Create sample execution result for testing"""
    from core.executor import ExecutionResult

    return ExecutionResult(
        success=True,
        instruction_count=1000,
        output="test output",
        error="",
        timeout=False,
        exit_code=0
    )

@pytest.fixture
def sample_quicksort_program():
    """Create temporary quicksort program for testing"""
    program_content = '''#!/usr/bin/env python3
import sys
import ast

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    left = [x for x in arr[1:] if x <= pivot]
    right = [x for x in arr[1:] if x > pivot]
    return quicksort(left) + [pivot] + quicksort(right)

def main():
    try:
        input_line = sys.stdin.read().strip()
        arr = ast.literal_eval(input_line)
        result = quicksort(arr)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(program_content)
        program_path = f.name
    
    # Make executable
    import stat
    os.chmod(program_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
    
    yield program_path
    
    # Cleanup
    try:
        os.unlink(program_path)
    except:
        pass

@pytest.fixture
def sample_input_spec():
    """Create temporary input specification file for testing"""
    spec_content = '''input_specification:
  name: "Test QuickSort Input"
  description: "List of integers for sorting"
  size_calculation: "count_elements"
  
  valid_examples:
    - "[1, 2, 3]"
    - "[5, 2, 8, 1]"
  
  invalid_examples:
    - "not a list"
    - "[a, b, c]"

# Custom size function
def count_elements(input_str: str) -> int:
    import ast
    try:
        parsed = ast.literal_eval(input_str)
        return len(parsed) if isinstance(parsed, list) else len(input_str)
    except:
        return len(input_str)
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(spec_content)
        spec_path = f.name
    
    yield spec_path
    
    # Cleanup
    try:
        os.unlink(spec_path)
    except:
        pass
