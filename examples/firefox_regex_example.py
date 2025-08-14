#!/usr/bin/env python3
"""
Example: Testing Firefox Regex Engine with PathoGen

This example demonstrates finding regex patterns that cause
catastrophic backtracking in the Firefox regex engine.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.pathogen import PathoGen
from targets.firefox_regex import FirefoxRegexTarget

def main():
    """Run Firefox regex analysis"""
    print("PathoGen Firefox Regex Example")
    print("=" * 40)

    try:
        # Initialize components
        config_path = "config/config.yaml"
        pathogen = PathoGen(config_path)

        # Use optimized LLMs for performance analysis
        print("Initializing LLM...")

        # Try Groq first (free, fast), fallback to OpenAI
        try:
            pathogen.initialize_llm("groq", "llama2-70b-4096")
            print("Using Groq LLM (free, fast)")
        except:
            pathogen.initialize_llm("openai", "gpt-3.5-turbo")
            print("Using OpenAI LLM (paid, reliable)")

        # Create Firefox regex target
        target = FirefoxRegexTarget()

        print("Target: Firefox SpiderMonkey Regex Engine")
        print("\nInput format:")
        print(target.get_input_description())
        print()

        # Run fuzzing campaign
        print("Starting fuzzing campaign (searching for high instruction count patterns)...")
        results = pathogen.run_campaign(
            target=target,
            input_spec=target.get_input_description(),
            resource_metric="instruction_count",  # Focus on instruction count
            max_iterations=30
        )

        # Display results
        print("\nResults:")
        print(f"Total iterations: {results.total_iterations}")
        print(f"Total time: {results.total_time:.2f} seconds")

        print("\nTop 5 highest instruction count regex patterns found:")
        for i, (input_data, score) in enumerate(results.best_inputs[:5], 1):
            lines = input_data.split('\n')
            pattern = lines[0] if lines else "Invalid"
            test_string = lines[1] if len(lines) > 1 else "Invalid"

            print(f"{i}. Score: {score:.0f} instructions")
            print(f"   Pattern: {pattern}")
            print(f"   Test String: {test_string[:50]}{'...' if len(test_string) > 50 else ''}")
            print()

        # Save results
        output_file = pathogen.save_results(results)
        print(f"Full results saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This example requires Firefox JavaScript shell.")
        print("Install SpiderMonkey or set --js-shell path manually.")

if __name__ == '__main__':
    main()
