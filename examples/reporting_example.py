#!/usr/bin/env python3
"""
Example: PathoGen Reporting System Demo

This example demonstrates the comprehensive reporting features including:
- Input size vs instruction count graphs
- Instruction count consumption over iterations
- Runtime execution tracking and analysis
- PDF and JSON report generation
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.pathogen import PathoGen
from utils.reporting import ResourceType
from utils.env_loader import load_env_file

def main():
    """Run PathoGen with reporting enabled"""
    print("PathoGen Reporting System Example")
    print("=" * 50)

    try:
        # Load environment variables
        load_env_file()

        # Path to external quicksort program
        from pathlib import Path
        quicksort_program = Path(__file__).parent / "quicksort.py"
        input_spec_file = Path(__file__).parent.parent / "input_specs" / "quicksort_spec.yaml"

        if not quicksort_program.exists():
            print(f"Error: QuickSort program not found at {quicksort_program}")
            return

        if not input_spec_file.exists():
            print(f"Error: Input specification not found at {input_spec_file}")
            return

        # Initialize PathoGen
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        pathogen = PathoGen(str(config_path))

        # Use Groq with Llama2-70B (free cloud option)
        print("Initializing LLM (Groq Llama2-70B)...")
        pathogen.initialize_llm("groq", "llama2-70b-4096")

        print("Target program: QuickSort")
        print("Expected input format: List of integers")
        print()

        # Run fuzzing campaign with reporting enabled
        print("Starting fuzzing campaign with reporting...")
        results = pathogen.run_campaign(
            program_path=str(quicksort_program),
            input_spec_file=str(input_spec_file),
            resource_metric="instruction_count",
            max_iterations=25,  # More iterations for better graphs
            enable_reporting=True  # Enable reporting
        )

        # Display results
        print("\nCampaign Results:")
        print(f"Total iterations: {results.total_iterations}")
        print(f"Total time: {results.total_time:.2f} seconds")
        print(f"Convergence iteration: {results.convergence_iteration}")

        print(f"\nTop 5 inputs found:")
        for i, (input_data, score) in enumerate(results.best_inputs[:5], 1):
            print(f"{i}. Score: {score:.0f} instructions")
            print(f"   Input: {input_data}")
            print()

        print("\nReporting Features Demonstrated:")
        print("✓ Input Size vs Instruction Count scatter plot")
        print("✓ Instruction count progress over iterations")
        print("✓ Instruction count distribution histogram")
        print("✓ Instruction count by input size categories")
        print("✓ Summary statistics and top inputs analysis")
        print("✓ JSON data export for further analysis")
        
        print(f"\nCheck the 'reports/' directory for generated PDF and JSON files!")
        
        # Show what graphs were created
        print("\nGraph Types Generated:")
        print("1. Input Size vs Instruction Count - Shows relationship between input complexity and runtime cost")
        print("2. Instruction Count Progress - Shows how the highest instruction count evolved over time")
        print("3. Instruction Count Distribution - Histogram of all instruction count measurements")
        print("4. Size Category Analysis - Instruction count grouped by input size categories")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()