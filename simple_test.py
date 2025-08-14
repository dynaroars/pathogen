#!/usr/bin/env python3
"""
Simple test to verify PathoGen functionality
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_basic_functionality():
    """Test basic PathoGen functionality"""
    print("Testing basic PathoGen functionality...")
    
    try:
        # Test imports
        from core.executor import ExecutionResult
        from core.scorer import ResourceScorer
        from core.selector import InputSelector
        print("✓ Core imports work")
        
        # Test ExecutionResult
        result = ExecutionResult(
            success=True,
            instruction_count=1000,
            output="test",
            error="",
            timeout=False,
            exit_code=0
        )
        print("✓ ExecutionResult creation works")
        
        # Test ResourceScorer
        scorer = ResourceScorer(['instruction_count'])
        score = scorer.score(result, 'instruction_count')
        assert score == 1000.0
        print("✓ ResourceScorer works")
        
        # Test InputSelector
        config = {'elite_size': 2, 'mutation_rate': 0.3, 'crossover_rate': 0.7}
        selector = InputSelector(config)
        assert selector.elite_size == 2
        print("✓ InputSelector works")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_external_program():
    """Test external program execution"""
    print("\nTesting external program execution...")
    
    quicksort_path = project_root / "examples" / "quicksort.py"
    if not quicksort_path.exists():
        print("✗ Quicksort program not found")
        return False
    
    try:
        import subprocess
        
        # Test program execution
        result = subprocess.run(
            ['python3', str(quicksort_path)],
            input='[3,1,4,1,5]',
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ External program executes successfully")
            print(f"  Output: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ External program failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ External program test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("PathoGen Simple Test Suite")
    print("=" * 40)
    
    tests = [
        test_basic_functionality,
        test_external_program
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())