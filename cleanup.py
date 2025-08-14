#!/usr/bin/env python3
"""
PathoGen Cleanup Utility
Removes all generated reports, results, and temporary files from analysis runs.
"""

import os
import shutil
from pathlib import Path

def clean_generated_files():
    """Clean all generated files from PathoGen runs"""
    print("PathoGen Cleanup Utility")
    print("=" * 40)
    
    project_root = Path(__file__).parent
    
    # Directories to clean
    dirs_to_clean = [
        'reports',
        'results', 
        '.pytest_cache',
        '__pycache__'
    ]
    
    # File patterns to remove
    file_patterns = [
        '*.pyc',
        '*.pyo', 
        '*.log',
        'pathogen_results_*.json',
        'pathogen_*.pdf',
        'pathogen_*.json'
    ]
    
    total_removed = 0
    
    # Clean directories
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            if dir_name in ['reports', 'results']:
                # For reports and results, remove contents but keep directory
                file_count = len(list(dir_path.glob('*')))
                if file_count > 0:
                    for item in dir_path.glob('*'):
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    print(f"✓ Cleaned {file_count} files from {dir_name}/")
                    total_removed += file_count
                else:
                    print(f"  {dir_name}/ already empty")
            else:
                # For cache directories, remove entirely
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    print(f"✓ Removed {dir_name}/ directory")
                    total_removed += 1
        else:
            print(f"  {dir_name}/ doesn't exist")
    
    # Clean file patterns recursively
    pattern_count = 0
    for pattern in file_patterns:
        matches = list(project_root.rglob(pattern))
        for match in matches:
            try:
                match.unlink()
                pattern_count += 1
            except:
                pass
    
    if pattern_count > 0:
        print(f"✓ Removed {pattern_count} cache/temp files")
        total_removed += pattern_count
    
    # Clean empty __pycache__ directories
    pycache_dirs = list(project_root.rglob('__pycache__'))
    for pycache_dir in pycache_dirs:
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                total_removed += 1
            except:
                pass
    
    if pycache_dirs:
        print(f"✓ Removed {len(pycache_dirs)} __pycache__ directories")
    
    print(f"\nCleanup Summary:")
    print(f"📁 Total items removed: {total_removed}")
    
    if total_removed > 0:
        print("🧹 Repository cleaned successfully!")
    else:
        print("✨ Repository was already clean!")
    
    return total_removed

def clean_specific_pattern(pattern: str):
    """Clean files matching a specific pattern"""
    project_root = Path(__file__).parent
    matches = list(project_root.rglob(pattern))
    
    if not matches:
        print(f"No files found matching pattern: {pattern}")
        return 0
    
    print(f"Found {len(matches)} files matching pattern: {pattern}")
    
    for match in matches:
        print(f"  - {match.relative_to(project_root)}")
    
    confirm = input(f"\nRemove these {len(matches)} files? [y/N]: ").strip().lower()
    
    if confirm in ['y', 'yes']:
        removed = 0
        for match in matches:
            try:
                match.unlink()
                removed += 1
            except Exception as e:
                print(f"Error removing {match}: {e}")
        
        print(f"✓ Removed {removed} files")
        return removed
    else:
        print("Cleanup cancelled")
        return 0

def main():
    """Main cleanup interface"""
    import sys
    
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
        clean_specific_pattern(pattern)
    else:
        clean_generated_files()

if __name__ == "__main__":
    main()