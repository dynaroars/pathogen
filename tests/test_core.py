# Core functionality tests
# Tests for the main PathoGen engine, resource scoring, and input selection components

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

import sys
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.pathogen import PathoGen, FuzzingResult
from core.executor import ExecutionResult
from core.scorer import ResourceScorer
from core.selector import InputSelector

class TestPathoGen:
    """Test PathoGen core functionality"""

    @patch('core.executor.ProgramExecutor._check_perf_availability')
    def test_pathogen_init(self, mock_perf_check):
        """Test PathoGen initialization"""
        # Mock perf availability to avoid system dependency
        mock_perf_check.return_value = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
pathogen:
  max_iterations: 10
  population_size: 5
  elite_size: 2
  log_level: INFO
  output_dir: reports
  resource_metrics:
    - instruction_count
  llm:
    provider: groq
    model: llama2-70b-4096
  input_generation:
    inputs_per_iteration: 5
    size_progression:
      start_size: 10
      increment: 5
""")
            config_path = f.name

        try:
            pathogen = PathoGen(config_path)
            assert pathogen.config['pathogen']['max_iterations'] == 10
            assert pathogen.config['pathogen']['population_size'] == 5
        finally:
            os.unlink(config_path)

    @patch('core.executor.ProgramExecutor._check_perf_availability')
    def test_pathogen_with_mock_llm(self, mock_perf_check, sample_quicksort_program, sample_input_spec):
        """Test PathoGen with mocked LLM and external program"""
        # Mock perf availability to avoid system dependency
        mock_perf_check.return_value = True
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
pathogen:
  max_iterations: 2
  population_size: 3
  elite_size: 1
  log_level: INFO
  output_dir: reports
  resource_metrics:
    - instruction_count
  llm:
    provider: groq
    model: llama2-70b-4096
  input_generation:
    inputs_per_iteration: 3
    size_progression:
      start_size: 5
      increment: 2
""")
            config_path = f.name

        try:
            pathogen = PathoGen(config_path)

            # Mock LLM
            mock_llm = Mock()
            mock_llm.generate.return_value = "[1,2,3]\n[3,2,1]\n[5,4,3,2,1]"
            pathogen.llm = mock_llm

            # Run short campaign with external program
            results = pathogen.run_campaign(
                program_path=sample_quicksort_program,
                input_spec_file=sample_input_spec,
                max_iterations=2
            )

            assert isinstance(results, FuzzingResult)
            assert results.total_iterations > 0
            assert len(results.best_inputs) > 0

        finally:
            os.unlink(config_path)

class TestResourceScorer:
    """Test resource scoring functionality"""

    def test_scorer_initialization(self):
        """Test scorer initialization"""
        metrics = ['instruction_count']
        scorer = ResourceScorer(metrics)
        assert scorer.metrics == metrics
        assert len(scorer.score_history) == 0

    def test_instruction_count_scoring(self):
        """Test instruction count scoring"""
        scorer = ResourceScorer(['instruction_count'])

        # Mock execution result
        result = ExecutionResult(
            success=True,
            instruction_count=1000,
            output="",
            error="",
            timeout=False,
            exit_code=0
        )

        score = scorer.score(result, 'instruction_count')
        assert score == 1000.0
        assert len(scorer.score_history) == 1

    def test_failed_execution_scoring(self):
        """Test scoring of failed executions"""
        scorer = ResourceScorer(['instruction_count'])

        # Mock failed execution result
        result = ExecutionResult(
            success=False,
            instruction_count=0,
            output="",
            error="Error occurred",
            timeout=False,
            exit_code=1
        )

        score = scorer.score(result, 'instruction_count')
        assert score == 0.0

class TestInputSelector:
    """Test input selection functionality"""

    def test_selector_initialization(self):
        """Test selector initialization"""
        config = {
            'elite_size': 3,
            'mutation_rate': 0.3,
            'crossover_rate': 0.7
        }
        selector = InputSelector(config)

        assert selector.elite_size == 3
        assert selector.mutation_rate == 0.3
        assert selector.crossover_rate == 0.7

    def test_select_best(self):
        """Test selection of best inputs"""
        config = {'elite_size': 2, 'mutation_rate': 0.3, 'crossover_rate': 0.7}
        selector = InputSelector(config)

        current_results = [
            ("[1,2,3]", 100.0),
            ("[3,2,1]", 200.0),
            ("[5,4,3,2,1]", 300.0)
        ]

        previous_best = [
            ("[1,2,3,4]", 150.0),
            ("[6,5,4,3,2,1]", 350.0)
        ]

        selected = selector.select_best(current_results, previous_best)

        # Should prioritize highest scores
        assert len(selected) > 0
        scores = [score for _, score in selected]
        assert max(scores) == 350.0  # Best from previous

        # Should be sorted by score (highest first)
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
