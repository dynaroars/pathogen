#!/usr/bin/env python3
"""
Example: Testing Regex Engine with PathoGen

This example demonstrates how to use PathoGen to find pathological regex patterns
that cause catastrophic backtracking in the regex engine.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.pathogen import PathoGen
from utils.env_loader import load_env_file

def main():
    """Run regex analysis with external program"""
    print("PathoGen Regex Engine Example")
    print("=" * 40)

    # Load environment variables
    load_env_file()

    # Path to external regex program
    regex_program = Path(__file__).parent / "regex_matcher.py"
    input_spec_file = Path(__file__).parent.parent / "input_specs" / "regex_spec.yaml"

    if not regex_program.exists():
        print(f"Error: Regex program not found at {regex_program}")
        print("Make sure regex_matcher.py exists in the examples/ directory")
        return

    if not input_spec_file.exists():
        print(f"Error: Input specification not found at {input_spec_file}")
        return

    print(f"Program: {regex_program}")
    print(f"Input specification: {input_spec_file}")
    print()

    # Initialize PathoGen
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    pathogen = PathoGen(str(config_path))

    # Use Groq with Llama2-70B (free cloud option)
    print("Initializing LLM (Groq Llama2-70B)...")
    pathogen.initialize_llm("groq", "llama2-70b-4096")

    # Run fuzzing campaign
    print("Starting fuzzing campaign...")
    results = pathogen.run_campaign(
        program_path=str(regex_program),
        input_spec_file=str(input_spec_file),
        resource_metric="instruction_count",
        max_iterations=30  # More iterations for regex complexity
    )

    # Display results
    print("\nResults:")
    print(f"Total iterations: {results.total_iterations}")
    print(f"Total time: {results.total_time:.2f} seconds")

    print("\nTop 5 pathological regex patterns found:")
    for i, (input_data, score) in enumerate(results.best_inputs[:5], 1):
        print(f"{i}. Score: {score:.0f} instructions")
        print(f"   Input: {input_data}")
        print()

    # Save results
    output_file = pathogen.save_results(results)
    print(f"Full results saved to: {output_file}")

if __name__ == '__main__':
    main()