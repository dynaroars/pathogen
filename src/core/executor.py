# Program execution and instruction count monitoring
# Executes target programs with input data and monitors instruction count using perf tool

import subprocess
import tempfile
import os
import time
import signal
import json
import re
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import logging

@dataclass
class ExecutionResult:
    """Results from program execution focused on instruction count"""
    success: bool
    instruction_count: int
    output: str
    error: str
    timeout: bool
    exit_code: int
    is_format_error: bool = False

class ProgramExecutor:
    """Executes programs and monitors instruction count"""

    def __init__(self, config: Dict[str, Any]):
        self.timeout = config.get('timeout_seconds', 30)
        self.logger = logging.getLogger(__name__)

        # Check if perf is available - required for instruction counting
        self.perf_available = self._check_perf_availability()
        if not self.perf_available:
            raise RuntimeError(
                "perf tool is not available on this system. "
                "Please install perf to measure instruction counts:\n"
                "  Ubuntu/Debian: sudo apt-get install linux-perf\n"
                "  RHEL/CentOS: sudo yum install perf\n" 
                "  Arch Linux: sudo pacman -S perf\n"
                "PathGen requires perf for accurate instruction counting."
            )

    def _check_perf_availability(self) -> bool:
        """Check if perf is available on the system"""
        try:
            result = subprocess.run(['perf', '--version'],
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def execute(self, program_path: str, input_data: str) -> ExecutionResult:
        """Execute external program with given input"""
        try:
            return self._execute_external(program_path, input_data)

        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            result = ExecutionResult(
                success=False,
                instruction_count=0,
                output="",
                error=str(e),
                timeout=False,
                exit_code=-1
            )
            result.is_format_error = self._is_format_error(result)
            return result


    def _execute_external(self, program_path: str, input_data: str) -> ExecutionResult:
        """Execute external program with perf monitoring for instruction counting"""
        
        try:
            # External programs use stdin by default
            cmd = [program_path]
            stdin_input = input_data
            
            # Set up environment
            env = os.environ.copy()

            # Build perf monitoring command for instruction counting
            perf_cmd = [
                'perf', 'stat',
                '-e', 'instructions:u',  # Only measure instructions
                '-x', ',',  # CSV output
                '--'
            ] + cmd

            # Execute with perf monitoring
            result = subprocess.run(
                perf_cmd,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )

            # Parse perf output for instruction count
            instruction_count = self._parse_perf_output(result.stderr)
            
            if instruction_count == 0:
                self.logger.warning("Failed to parse instruction count from perf output")

            exec_result = ExecutionResult(
                success=result.returncode == 0,
                instruction_count=instruction_count,
                output=result.stdout,
                error=result.stderr,
                timeout=False,
                exit_code=result.returncode
            )
            exec_result.is_format_error = self._is_format_error(exec_result)
            return exec_result

        except subprocess.TimeoutExpired:
            result = ExecutionResult(
                success=False,
                instruction_count=0,
                output="",
                error="Execution timeout",
                timeout=True,
                exit_code=-1
            )
            result.is_format_error = False  # Timeout is not a format error
            return result
            
        except Exception as e:
            result = ExecutionResult(
                success=False,
                instruction_count=0,
                output="",
                error=f"Execution error: {str(e)}",
                timeout=False,
                exit_code=-1
            )
            result.is_format_error = self._is_format_error(result)
            return result

        except subprocess.TimeoutExpired:
            result = ExecutionResult(
                success=False,
                instruction_count=0,
                output="",
                error="Execution timeout",
                timeout=True,
                exit_code=-1
            )
            result.is_format_error = False  # Timeout is not a format error
            return result

    def _is_format_error(self, execution_result) -> bool:
        """Determine if execution failure is due to input format issues"""
        if execution_result.success or execution_result.timeout:
            return False
            
        error_indicators = [
            "parse error", "syntax error", "invalid format", 
            "json.decoder.JSONDecodeError", "ValueError", "TypeError",
            "expected", "invalid literal", "cannot convert",
            "malformed", "unexpected", "invalid input",
            "parsing failed", "format error", "decode error",
            "invalid syntax", "bad input", "wrong format"
        ]
        
        error_text = execution_result.error.lower()
        return any(indicator in error_text for indicator in error_indicators)

    def _parse_perf_output(self, stderr: str) -> int:
        """Parse instruction count from perf output"""
        try:
            # Look for lines with instruction count
            for line in stderr.split('\n'):
                if 'instructions:u' in line:
                    # CSV format: value,unit,event,running,ratio
                    parts = line.split(',')
                    if parts and parts[0].isdigit():
                        return int(parts[0])

            # Fallback: look for any number followed by 'instructions'
            matches = re.findall(r'(\d+).*instructions', stderr)
            if matches:
                return int(matches[0])

        except Exception as e:
            self.logger.warning(f"Failed to parse perf output: {e}")

        return 0

    def _run_with_timeout(self, func, args, timeout_seconds):
        """Run function with timeout (Unix only)"""
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Function execution timeout")

        # Set timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)

        try:
            result = func(*args)
            signal.alarm(0)  # Cancel timeout
            return result
        except TimeoutError:
            return None
        finally:
            signal.signal(signal.SIGALRM, old_handler)
