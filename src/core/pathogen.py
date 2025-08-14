# PathoGen main engine
# Coordinates LLM-guided evolutionary fuzzing to find pathological inputs that maximize resource consumption

import logging
import os
import yaml
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import time
import json
from pathlib import Path

try:
    # Try relative imports first (for package usage)
    from ..llm.factory import LLMFactory
    from .executor import ProgramExecutor
    from .scorer import ResourceScorer
    from .selector import InputSelector
    from ..utils.logger import setup_logger
    from ..utils.metrics import MetricsCollector
    from ..utils.reporting import ResourceTracker, ResourceType, ReportGenerator
    from ..utils.input_spec import InputSpecification
except ImportError:
    # Fall back to absolute imports (for direct execution and tests)
    from llm.factory import LLMFactory
    from core.executor import ProgramExecutor
    from core.scorer import ResourceScorer
    from core.selector import InputSelector
    from utils.logger import setup_logger
    from utils.metrics import MetricsCollector
    from utils.reporting import ResourceTracker, ResourceType, ReportGenerator
    from utils.input_spec import InputSpecification

@dataclass
class FuzzingResult:
    """Results from a fuzzing campaign"""
    best_inputs: List[Tuple[str, float]]
    generation_history: List[Dict]
    total_iterations: int
    total_time: float
    convergence_iteration: int = -1

@dataclass
class GenerationResult:
    """Results from a single generation"""
    inputs: List[str]
    scores: List[float]
    best_input: str
    best_score: float
    generation: int

class PathoGen:
    """Main PathoGen fuzzing engine"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.config_path = config_path
        self.logger = setup_logger(self.config['pathogen']['log_level'])

        # Initialize components
        self.llm = None
        self.executor = ProgramExecutor(self.config['pathogen'])
        self.scorer = ResourceScorer()
        self.selector = InputSelector(self.config['pathogen'])
        self.metrics = MetricsCollector()

        # Initialize reporting system
        self.resource_tracker = None
        self.report_generator = ReportGenerator(
            output_dir=self.config['pathogen'].get('output_dir', 'reports')
        )

        # State
        self.generation = 0
        self.best_inputs = []
        self.generation_history = []

        # Load prompt templates
        self.prompt_templates = self._load_prompt_templates()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_prompt_templates(self) -> Dict:
        """Load prompt templates"""
        if hasattr(self, 'config_path') and self.config_path:
            config_dir = Path(self.config_path).parent
        else:
            config_dir = Path.cwd()
        template_path = config_dir / 'config' / 'prompt_templates.yaml'
        if template_path.exists():
            with open(template_path, 'r') as f:
                return yaml.safe_load(f)['templates']
        return {}

    def initialize_llm(self, provider: str = None, model: str = None) -> None:
        """Initialize the LLM"""
        provider = provider or self.config['pathogen']['llm']['provider']
        model = model or self.config['pathogen']['llm']['model']

        self.llm = LLMFactory.create_llm(
            provider=provider,
            model=model,
            config=self.config['pathogen']['llm']
        )

        self.logger.info(f"Initialized LLM: {provider}/{model}")

    def run_campaign(self, program_path: str, input_spec_file: str, 
                    resource_metric: str = "instruction_count", max_iterations: int = None, 
                    enable_reporting: bool = True) -> FuzzingResult:
        """Run a complete fuzzing campaign"""

        if not self.llm:
            self.initialize_llm()

        # Load input specification (required)
        if not input_spec_file:
            raise ValueError("input_spec_file is required for external programs")
        
        self.input_specification = InputSpecification(input_spec_file)
        input_description = self.input_specification.get_description()

        max_iterations = max_iterations or self.config['pathogen']['max_iterations']
        
        # Get input generation settings
        input_gen_config = self.config['pathogen'].get('input_generation', {})
        inputs_per_iteration = input_gen_config.get('inputs_per_iteration', 15)
        start_size = input_gen_config.get('size_progression', {}).get('start_size', 10)
        increment = input_gen_config.get('size_progression', {}).get('increment', 15)

        # Initialize resource tracking for reporting
        if enable_reporting:
            resource_types = self._get_resource_types_for_metric(resource_metric)
            self.resource_tracker = ResourceTracker(resource_types)
            
            # External programs use stdin by default
            input_method = "stdin"

        self.logger.info(f"Starting fuzzing campaign: {max_iterations} iterations, {inputs_per_iteration} inputs per iteration")

        start_time = time.time()

        # Initialize system prompt
        system_prompt = self._build_system_prompt(
            program_path, input_description, resource_metric
        )

        # Generation loop
        for iteration in range(max_iterations):
            self.logger.info(f"Generation {iteration + 1}/{max_iterations}")

            # Calculate target sizes for this iteration
            target_sizes = [start_size + (i * increment) for i in range(inputs_per_iteration)]
            
            # Generate candidate inputs
            candidates = self._generate_candidates(
                program_path, system_prompt, inputs_per_iteration, target_sizes, iteration
            )

            # Execute and score candidates
            results = self._evaluate_candidates(program_path, candidates, resource_metric, input_method if enable_reporting else None)

            # Select best inputs for next generation
            selected = self.selector.select_best(results, self.best_inputs)

            # Update state
            self._update_state(selected, iteration)

            # Check convergence
            if self._check_convergence():
                self.logger.info(f"Converged at iteration {iteration + 1}")
                break

        total_time = time.time() - start_time

        result = FuzzingResult(
            best_inputs=self.best_inputs[:10],  # Top 10
            generation_history=self.generation_history,
            total_iterations=iteration + 1,
            total_time=total_time,
            convergence_iteration=iteration + 1 if self._check_convergence() else -1
        )

        # Generate report if enabled
        if enable_reporting and self.resource_tracker:
            self.logger.info("Generating campaign report...")
            try:
                import os
                target_name = Path(program_path).name
                
                campaign_data = {
                    'total_iterations': result.total_iterations,
                    'total_time': result.total_time,
                    'convergence_iteration': result.convergence_iteration,
                    'best_inputs': [(inp, score) for inp, score in result.best_inputs],
                    'generation_history': result.generation_history
                }
                
                report_path = self.report_generator.generate_campaign_report(
                    campaign_data, self.resource_tracker, target_name
                )
                self.logger.info(f"Campaign report generated: {report_path}")
                
            except Exception as e:
                self.logger.warning(f"Failed to generate report: {e}")

        return result

    def _build_system_prompt(self, program_path: str, input_spec: str, resource_metric: str) -> str:
        """Build the initial system prompt"""
        template = self.prompt_templates.get('system_prompt', '')

        return template.format(
            program_path=program_path,
            input_description=input_spec,
            resource_metric=resource_metric,
            best_score=0,
            successful_inputs="None yet"
        )

    def _generate_candidates(self, program_path: str, system_prompt: str, num_inputs: int, target_sizes: List[int], iteration: int) -> List[str]:
        """Generate candidate inputs using the LLM"""

        if iteration == 0:
            # First generation - use system prompt only
            prompt = system_prompt + f"\n\nGenerate {num_inputs} diverse initial test inputs with sizes: {target_sizes}."
        else:
            # Subsequent generations - include best inputs
            prompt = self._build_generation_prompt(system_prompt, num_inputs, target_sizes)

        try:
            response = self.llm.generate(prompt)
            candidates = self._parse_candidates(response)

            # Validate candidates through execution
            validated_candidates = self._validate_through_execution(program_path, candidates)
            
            # Ensure we have enough candidates
            while len(validated_candidates) < num_inputs:
                additional_needed = num_inputs - len(validated_candidates)
                additional = self.llm.generate(f"Generate {additional_needed} more inputs with target sizes: {target_sizes}:")
                additional_parsed = self._parse_candidates(additional)
                additional_validated = self._validate_through_execution(program_path, additional_parsed)
                validated_candidates.extend(additional_validated)

            return validated_candidates[:num_inputs]

        except Exception as e:
            self.logger.error(f"Error generating candidates: {e}")
            return self._generate_fallback_candidates(num_inputs)

    def _validate_through_execution(self, program_path: str, candidates: List[str]) -> List[str]:
        """Filter candidates by attempting execution and checking for format errors"""
        valid_candidates = []
        validation_config = self.config['pathogen'].get('input_validation', {})
        max_retries = validation_config.get('max_format_retries', 2)
        
        for candidate in candidates:
            retry_count = 0
            while retry_count <= max_retries:
                result = self.executor.execute(program_path, candidate)
                
                if not hasattr(result, 'is_format_error') or not result.is_format_error:
                    valid_candidates.append(candidate)
                    break
                else:
                    self.logger.debug(f"Rejected input due to format error (attempt {retry_count + 1}): {candidate[:50]}...")
                    retry_count += 1
                    if retry_count <= max_retries and validation_config.get('retry_on_format_error', True):
                        # Could implement input correction logic here
                        break
        
        return valid_candidates

    def _build_generation_prompt(self, system_prompt: str, num_inputs: int, target_sizes: List[int]) -> str:
        """Build prompt for subsequent generations"""
        template = self.prompt_templates.get('generation_prompt', '')

        # Get context from input specification if available
        if self.input_specification:
            context = self.input_specification.get_prompt_context()
            previous_best = self.input_specification.format_previous_best(self.best_inputs)
        else:
            context = {
                'input_description': system_prompt,
                'valid_examples': "No examples available",
                'invalid_examples': "No examples available"
            }
            # Format best inputs with scores (fallback format)
            previous_best = "\n".join([
                f"Input: {input_data} | Score: {score:.0f} instructions"
                for input_data, score in self.best_inputs[:5]
            ]) if self.best_inputs else "No previous successful inputs yet"

        return template.format(
            num_inputs=num_inputs,
            target_sizes=target_sizes,
            previous_best_with_size_and_score=previous_best,
            **context
        )

    def _parse_candidates(self, response: str) -> List[str]:
        """Parse candidate inputs from LLM response"""
        lines = response.strip().split('\n')
        candidates = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Clean up the line - remove prefixes like "Input:", numbers, etc.
                cleaned = line
                for prefix in ['Input:', 'input:', f'{len(candidates)+1}.', f'{len(candidates)+1})', '-']:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):].strip()

                if cleaned:
                    candidates.append(cleaned)

        return candidates

    def _generate_fallback_candidates(self, num_inputs: int) -> List[str]:
        """Generate fallback candidates if LLM fails"""
        self.logger.warning("Using fallback candidate generation")
        # Simple fallback - could be improved based on target type
        return [f"[{i}, {i+1}, {i+2}]" for i in range(num_inputs)]

    def _evaluate_candidates(self, program_path: str, candidates: List[str], resource_metric: str, input_method: str = None) -> List[Tuple[str, float]]:
        """Execute candidates and measure resource usage"""
        results = []

        for candidate in candidates:
            try:
                # Execute the program with this input
                execution_result = self.executor.execute(program_path, candidate)

                # Record measurement for reporting if enabled
                if self.resource_tracker and input_method:
                    self.resource_tracker.add_measurement(candidate, execution_result, input_method)

                # Score based on resource usage
                score = self.scorer.score(execution_result, resource_metric)

                results.append((candidate, score))

                self.logger.debug(f"Input: {candidate[:50]}... Score: {score}")

            except Exception as e:
                self.logger.warning(f"Failed to evaluate candidate {candidate[:50]}...: {e}")
                results.append((candidate, 0.0))

        return results

    def _update_state(self, selected_inputs: List[Tuple[str, float]], iteration: int):
        """Update internal state with new results"""
        # Add to best inputs and sort
        self.best_inputs.extend(selected_inputs)
        self.best_inputs.sort(key=lambda x: x[1], reverse=True)

        # Keep only top performers
        elite_size = self.config['pathogen']['elite_size']
        self.best_inputs = self.best_inputs[:elite_size * 2]  # Keep some extras

        # Record generation history
        generation_data = {
            'generation': iteration + 1,
            'best_score': self.best_inputs[0][1] if self.best_inputs else 0,
            'avg_score': sum(score for _, score in selected_inputs) / len(selected_inputs) if selected_inputs else 0,
            'num_inputs': len(selected_inputs)
        }

        self.generation_history.append(generation_data)

        self.logger.info(f"Generation {iteration + 1}: Best score = {generation_data['best_score']:.2f}")

    def _check_convergence(self) -> bool:
        """Check if the algorithm has converged"""
        if len(self.generation_history) < 5:
            return False

        # Check if best score hasn't improved in last 5 generations
        recent_scores = [gen['best_score'] for gen in self.generation_history[-5:]]
        return len(set(recent_scores)) == 1  # All scores are the same

    def save_results(self, results: FuzzingResult, output_path: str = None):
        """Save results to file"""
        if not output_path:
            output_dir = self.config['pathogen']['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            timestamp = int(time.time())
            output_path = str(Path(output_dir) / f"pathogen_results_{timestamp}.json")

        results_dict = {
            'best_inputs': results.best_inputs,
            'generation_history': results.generation_history,
            'total_iterations': results.total_iterations,
            'total_time': results.total_time,
            'convergence_iteration': results.convergence_iteration,
            'config': self.config
        }

        with open(output_path, 'w') as f:
            json.dump(results_dict, f, indent=2)

        self.logger.info(f"Results saved to: {output_path}")
        return output_path

    def _get_resource_types_for_metric(self, resource_metric: str) -> List[ResourceType]:
        """Convert resource metric string to ResourceType enums - only instruction count"""
        # Always return instruction count as primary metric
        return [ResourceType.INSTRUCTION_COUNT]
