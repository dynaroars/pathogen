#!/usr/bin/env python3
"""
Individual test components
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_resource_scorer():
    """Test ResourceScorer functionality"""
    print("Testing ResourceScorer...")
    
    from core.executor import ExecutionResult
    from core.scorer import ResourceScorer
    
    # Test scoring
    scorer = ResourceScorer(['instruction_count'])
    
    result = ExecutionResult(
        success=True,
        instruction_count=1500,
        output="",
        error="",
        timeout=False,
        exit_code=0
    )
    
    score = scorer.score(result, 'instruction_count')
    assert score == 1500.0
    print("✓ ResourceScorer works correctly")

def test_input_selector():
    """Test InputSelector functionality"""
    print("Testing InputSelector...")
    
    from core.selector import InputSelector
    
    config = {'elite_size': 3, 'mutation_rate': 0.3, 'crossover_rate': 0.7}
    selector = InputSelector(config)
    
    # Test selection
    current_results = [
        ("[1,2,3]", 100.0),
        ("[3,2,1]", 200.0), 
        ("[5,4,3,2,1]", 300.0)
    ]
    
    selected = selector.select_best(current_results, [])
    assert len(selected) > 0
    print("✓ InputSelector works correctly")

def test_external_program_execution():
    """Test external program execution"""
    print("Testing external program execution...")
    
    import subprocess
    
    quicksort_path = project_root / "examples" / "quicksort.py"
    
    # Test with different inputs
    test_cases = [
        ("[1,2,3,4,5]", "sorted array"),
        ("[5,4,3,2,1]", "reverse sorted"),
        ("[3,1,4,1,5,9,2,6]", "random array")
    ]
    
    for test_input, description in test_cases:
        result = subprocess.run(
            ['python3', str(quicksort_path)],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        assert result.returncode == 0, f"Failed on {description}"
        print(f"✓ {description}: {result.stdout.strip()}")

def test_input_specification():
    """Test input specification loading"""
    print("Testing input specification...")
    
    from utils.input_spec import InputSpecification
    
    spec_path = project_root / "input_specs" / "quicksort_spec.yaml"
    if spec_path.exists():
        spec = InputSpecification(str(spec_path))
        description = spec.get_description()
        assert len(description) > 0
        print("✓ Input specification loads correctly")
    else:
        print("⚠ Input specification file not found, skipping")

def main():
    """Run individual tests"""
    print("PathoGen Individual Test Components")
    print("=" * 45)
    
    tests = [
        test_resource_scorer,
        test_input_selector, 
        test_external_program_execution,
        test_input_specification
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
    
    print(f"\nResults: {passed}/{total} individual tests passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())