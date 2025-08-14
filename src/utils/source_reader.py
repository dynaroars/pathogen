# Source code reader utility
# Reads and parses source code from various programming languages to provide context for LLMs

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class SourceReader:
    """Utility to read and analyze source code files"""

    # File extension to language mapping
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp', 
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.java': 'java',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective-c',
        '.mm': 'objective-cpp',
        '.pl': 'perl',
        '.sh': 'bash',
        '.lua': 'lua',
        '.dart': 'dart'
    }

    # Language-specific comment patterns
    COMMENT_PATTERNS = {
        'python': [r'#.*$', r'""".*?"""', r"'''.*?'''"],
        'c': [r'//.*$', r'/\*.*?\*/'],
        'cpp': [r'//.*$', r'/\*.*?\*/'],
        'java': [r'//.*$', r'/\*.*?\*/'],
        'javascript': [r'//.*$', r'/\*.*?\*/'],
        'typescript': [r'//.*$', r'/\*.*?\*/'],
        'go': [r'//.*$', r'/\*.*?\*/'],
        'rust': [r'//.*$', r'/\*.*?\*/'],
        'csharp': [r'//.*$', r'/\*.*?\*/'],
        'swift': [r'//.*$', r'/\*.*?\*/'],
        'kotlin': [r'//.*$', r'/\*.*?\*/'],
        'scala': [r'//.*$', r'/\*.*?\*/']
    }

    def __init__(self, max_lines: int = 1000, max_file_size: int = 1024 * 1024):
        """
        Initialize source reader
        
        Args:
            max_lines: Maximum number of lines to read from a file
            max_file_size: Maximum file size in bytes
        """
        self.max_lines = max_lines
        self.max_file_size = max_file_size

    def read_source(self, file_path: str) -> str:
        """
        Read source code from a file with intelligent truncation
        
        Args:
            file_path: Path to source code file
            
        Returns:
            Source code content with metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        if path.stat().st_size > self.max_file_size:
            return f"// Source file too large ({path.stat().st_size} bytes)\n// File: {file_path}\n// Content truncated for analysis"

        language = self._detect_language(path)
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            return f"// Error reading source file: {e}\n// File: {file_path}"

        # Truncate if too many lines
        if len(lines) > self.max_lines:
            lines = lines[:self.max_lines]
            truncated = True
        else:
            truncated = False

        # Process the source code
        processed_code = self._process_source_code(''.join(lines), language)
        
        # Add metadata header
        header = f"// Source file: {file_path}\n"
        header += f"// Language: {language}\n"
        header += f"// Lines: {len(lines)}"
        
        if truncated:
            header += f" (truncated from original)\n"
        else:
            header += "\n"
            
        header += "// " + "="*60 + "\n\n"
        
        return header + processed_code

    def read_multiple_sources(self, file_paths: List[str]) -> str:
        """
        Read multiple source files and combine them
        
        Args:
            file_paths: List of source file paths
            
        Returns:
            Combined source code content
        """
        combined_code = "// Multiple source files combined for analysis\n\n"
        
        for file_path in file_paths:
            try:
                code = self.read_source(file_path)
                combined_code += code + "\n\n"
            except Exception as e:
                combined_code += f"// Error reading {file_path}: {e}\n\n"
                
        return combined_code

    def extract_main_functions(self, file_path: str) -> str:
        """
        Extract main/entry functions from source code
        
        Args:
            file_path: Path to source file
            
        Returns:
            Source code with focus on main functions
        """
        try:
            full_code = self.read_source(file_path)
            language = self._detect_language(Path(file_path))
            
            # Extract relevant sections based on language
            if language == 'c' or language == 'cpp':
                return self._extract_c_main(full_code)
            elif language == 'java':
                return self._extract_java_main(full_code)
            elif language == 'python':
                return self._extract_python_main(full_code)
            else:
                return full_code
                
        except Exception:
            return self.read_source(file_path)

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        extension = file_path.suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(extension, 'unknown')

    def _process_source_code(self, code: str, language: str) -> str:
        """
        Process source code to make it more LLM-friendly
        
        Args:
            code: Raw source code
            language: Programming language
            
        Returns:
            Processed source code
        """
        # Remove excessive whitespace
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            # Remove trailing whitespace but preserve indentation
            line = line.rstrip()
            if line.strip():  # Non-empty lines
                processed_lines.append(line)
            elif processed_lines and processed_lines[-1].strip():  # Single empty line after content
                processed_lines.append('')
                
        return '\n'.join(processed_lines)

    def _extract_c_main(self, code: str) -> str:
        """Extract main function and related functions from C/C++ code"""
        lines = code.split('\n')
        result_lines = []
        
        # Find main function
        in_main = False
        brace_count = 0
        
        for line in lines:
            if not in_main and ('int main' in line or 'void main' in line):
                in_main = True
                brace_count = 0
                result_lines.append(line)
                continue
                
            if in_main:
                result_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and '{' in ''.join(result_lines):
                    break
        
        if result_lines:
            return '\n'.join(result_lines)
        else:
            # Return first 50 lines if no main found
            return '\n'.join(lines[:50])

    def _extract_java_main(self, code: str) -> str:
        """Extract main method from Java code"""
        lines = code.split('\n')
        
        # Look for public static void main
        main_pattern = re.compile(r'public\s+static\s+void\s+main\s*\(')
        
        for i, line in enumerate(lines):
            if main_pattern.search(line):
                # Extract from main method start to end of class
                return '\n'.join(lines[max(0, i-5):min(len(lines), i+50)])
                
        # Return first 50 lines if no main found
        return '\n'.join(lines[:50])

    def _extract_python_main(self, code: str) -> str:
        """Extract main section from Python code"""
        lines = code.split('\n')
        
        # Look for if __name__ == "__main__" or main function definitions
        main_sections = []
        
        for i, line in enumerate(lines):
            if '__name__' in line and '__main__' in line:
                # Include this section
                main_sections.extend(lines[i:min(len(lines), i+20)])
                break
            elif line.strip().startswith('def main('):
                # Include main function
                main_sections.extend(lines[max(0, i-2):min(len(lines), i+30)])
                
        if main_sections:
            return '\n'.join(main_sections)
        else:
            # Return first 50 lines
            return '\n'.join(lines[:50])

    def analyze_complexity_patterns(self, file_path: str) -> Dict[str, List[str]]:
        """
        Analyze source code for complexity patterns
        
        Args:
            file_path: Path to source file
            
        Returns:
            Dictionary with complexity analysis
        """
        try:
            code = self.read_source(file_path)
            language = self._detect_language(Path(file_path))
            
            patterns = {
                'loops': [],
                'recursion': [],
                'data_structures': [],
                'algorithms': []
            }
            
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_lower = line.lower().strip()
                
                # Detect loops
                if any(keyword in line_lower for keyword in ['for', 'while', 'do']):
                    patterns['loops'].append(f"Line {i}: {line.strip()}")
                
                # Detect recursion (function calling itself)
                if language == 'c' or language == 'cpp':
                    # Simple heuristic for C/C++
                    func_match = re.search(r'(\w+)\s*\(', line)
                    if func_match and func_match.group(1) in line:
                        patterns['recursion'].append(f"Line {i}: Possible recursion - {line.strip()}")
                
                # Detect data structures
                if any(ds in line_lower for ds in ['array', 'list', 'vector', 'map', 'set', 'tree', 'graph']):
                    patterns['data_structures'].append(f"Line {i}: {line.strip()}")
                    
                # Detect sorting/searching
                if any(alg in line_lower for alg in ['sort', 'search', 'binary', 'quick', 'merge', 'heap']):
                    patterns['algorithms'].append(f"Line {i}: {line.strip()}")
            
            return patterns
            
        except Exception as e:
            return {'error': [f"Failed to analyze: {e}"]}

    def get_function_signatures(self, file_path: str) -> List[str]:
        """
        Extract function signatures from source code
        
        Args:
            file_path: Path to source file
            
        Returns:
            List of function signatures
        """
        try:
            code = self.read_source(file_path)
            language = self._detect_language(Path(file_path))
            
            signatures = []
            lines = code.split('\n')
            
            if language in ['c', 'cpp']:
                # C/C++ function pattern
                func_pattern = re.compile(r'^\s*(?:static\s+)?(?:inline\s+)?[\w\s\*]+\s+(\w+)\s*\([^)]*\)\s*{?')
                
                for line in lines:
                    match = func_pattern.match(line)
                    if match and not line.strip().startswith('//'):
                        signatures.append(line.strip())
                        
            elif language == 'python':
                # Python function pattern
                func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\([^)]*\):')
                
                for line in lines:
                    match = func_pattern.match(line)
                    if match:
                        signatures.append(line.strip())
                        
            elif language == 'java':
                # Java method pattern
                func_pattern = re.compile(r'^\s*(?:public|private|protected)?\s*(?:static\s+)?[\w\s\<\>\[\]]+\s+(\w+)\s*\([^)]*\)\s*{?')
                
                for line in lines:
                    match = func_pattern.match(line)
                    if match and not line.strip().startswith('//'):
                        signatures.append(line.strip())
            
            return signatures
            
        except Exception as e:
            return [f"Error extracting functions: {e}"]