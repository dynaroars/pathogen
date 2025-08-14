#!/usr/bin/env python3
"""
Test runner for PathoGen tests
This handles path setup and runs pytest
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run tests with proper environment setup"""
    print("PathoGen Test Runner")
    print("=" * 40)
    
    # Get project root
    project_root = Path(__file__).parent
    src_path = project_root / 'src'
    
    # Change to project directory
    os.chdir(project_root)
    
    # Set up environment with proper Python path
    env = os.environ.copy()
    current_path = env.get('PYTHONPATH', '')
    if current_path:
        env['PYTHONPATH'] = f"{src_path}:{current_path}"
    else:
        env['PYTHONPATH'] = str(src_path)
    
    # Run pytest with verbose output and proper environment
    cmd = [
        sys.executable, '-m', 'pytest', 
        'tests/', 
        '-v',
        '--tb=short',
        '-x'  # Stop on first failure
    ]
    
    try:
        print(f"Running: {' '.join(cmd)}")
        print(f"PYTHONPATH: {env['PYTHONPATH']}")
        print()
        
        result = subprocess.run(cmd, env=env, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)