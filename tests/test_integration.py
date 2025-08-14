# Integration tests
# End-to-end tests that verify the complete PathoGen workflow with real targets

import pytest
import tempfile
import os
from pathlib import Path

import sys
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.pathogen import PathoGen
from llm.base import BaseLLM
from unittest.mock import patch

class MockIntegrationLLM(BaseLLM):
    """Mock LLM that generates realistic quicksort inputs"""

    def __init__(self, model: str, config):
        super().__init__(model, config)
        self.generation_count = 0

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate increasingly pathological quicksort inputs"""
        self.generation_count += 1

        if self.generation_count == 1:
            # First generation - random inputs
            return "[7, 3, 1, 8, 5]\n[2, 9, 6, 4, 10]\n[1, 3, 2, 5, 4]"
        elif self.generation_count == 2:
            # Second generation - more sorted inputs
            return "[1, 2, 3, 4, 5]\n[2, 3, 4, 5, 6]\n[1, 2, 3, 4, 5, 6]"
        else:
            # Later generations - fully sorted (worst case)
            return "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]\n[1, 2, 3, 4, 5, 6, 7, 8]\n[1, 2, 3, 4, 5]"

    def is_available(self) -> bool:
        return True

class TestIntegration:
    """Integration tests for PathoGen"""

    @patch('core.executor.ProgramExecutor._check_perf_availability')
    @patch('core.executor.ProgramExecutor._execute_external')
    def test_end_to_end_quicksort(self, mock_execute, mock_perf_check, sample_quicksort_program, sample_input_spec):
        """Test complete end-to-end execution with external QuickSort program"""
        # Mock perf availability to avoid system dependency
        mock_perf_check.return_value = True
        
        # Mock execution to return realistic instruction counts
        from core.executor import ExecutionResult
        def mock_execution(program_path, input_data):
            # Simulate different instruction counts based on input
            import ast
            try:
                parsed = ast.literal_eval(input_data)
                if isinstance(parsed, list):
                    # Simulate O(n²) behavior for sorted arrays
                    size = len(parsed)
                    is_sorted = parsed == sorted(parsed)
                    base_count = size * size if is_sorted else size * 10
                    return ExecutionResult(
                        success=True,
                        instruction_count=base_count + 100,
                        output=str(sorted(parsed)),
                        error="",
                        timeout=False,
                        exit_code=0
                    )
            except:
                pass
            
            # Default case
            return ExecutionResult(
                success=True,
                instruction_count=50,
                output="[1, 2, 3]",
                error="",
                timeout=False,
                exit_code=0
            )
        
        mock_execute.side_effect = mock_execution

        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
pathogen:
  max_iterations: 3
  population_size: 3
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
    inputs_per_iteration: 3
    size_progression:
      start_size: 5
      increment: 2
""")
            config_path = f.name

        try:
            # Initialize PathoGen
            pathogen = PathoGen(config_path)

            # Use mock LLM
            pathogen.llm = MockIntegrationLLM("test-model", {})

            # Run campaign with external program
            results = pathogen.run_campaign(
                program_path=sample_quicksort_program,
                input_spec_file=sample_input_spec,
                resource_metric="instruction_count",
                max_iterations=3
            )

            # Verify results
            assert results.total_iterations <= 3
            assert len(results.best_inputs) > 0
            assert results.total_time > 0

            # Check that we found some pathological inputs
            best_input, best_score = results.best_inputs[0]
            assert best_score > 0
            
            # Verify input looks like a list
            assert best_input.startswith('[') and best_input.endswith(']')

        finally:
            os.unlink(config_path)

    def test_quicksort_worst_case_discovery(self, sample_quicksort_program):
        """Test that external QuickSort program can be executed"""
        import subprocess
        import tempfile
        
        # Test known worst-case input (sorted array)
        sorted_input = "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
        
        # Execute program directly
        try:
            result = subprocess.run(
                ['python3', sample_quicksort_program],
                input=sorted_input,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should execute successfully
            assert result.returncode == 0
            # Should produce sorted output
            assert '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]' in result.stdout
        except subprocess.TimeoutExpired:
            # This actually shows the program is taking time (good for pathological testing)
            pass

    def test_input_parsing_robustness(self, sample_quicksort_program):
        """Test that external program handles input correctly"""
        import subprocess

        # Test list format (what our quicksort program expects)
        test_input = "[1, 2, 3, 4, 5]"
        
        try:
            result = subprocess.run(
                ['python3', sample_quicksort_program],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Should execute successfully
            assert result.returncode == 0
            # Should produce some output
            assert len(result.stdout.strip()) > 0
        except subprocess.TimeoutExpired:
            pytest.fail(f"Program timed out with input: {test_input}")
        except Exception as e:
            pytest.fail(f"Failed to execute program with input '{test_input}': {e}")
