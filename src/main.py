#!/usr/bin/env python3
"""
PathoGen - LLM-Guided Performance Testing Tool

A tool for generating inputs that maximize instruction count in external programs
using evolutionary fuzzing guided by Large Language Models.
"""

import argparse
import sys
import os
import yaml
from pathlib import Path

# Add src to path for cross-platform compatibility
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Also add parent directory to handle relative imports
sys.path.insert(0, str(current_dir.parent))

from src.core.pathogen import PathoGen
from src.llm.factory import LLMFactory
from src.utils.logger import setup_logger
from src.utils.env_loader import load_env_file, check_api_keys

def create_arg_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="PathoGen - LLM-Guided Performance Testing Tool for External Programs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test quicksort program with input specification
  python main.py --program ./quicksort.py --input-spec input_specs/quicksort_spec.yaml

  # Test with OpenAI instead of Groq
  python main.py --program ./program --input-spec input_specs/custom_spec.yaml --llm openai

  # List available LLM providers
  python main.py --list-llms
  
  # Clean generated files
  python main.py --clean
        """
    )

    # Required arguments
    parser.add_argument(
        '--program', '--executable',
        dest='program_path',
        help='Path to external program executable (required)'
    )
    parser.add_argument(
        '--input-spec',
        dest='input_spec_file',
        help='Path to input specification YAML file (required)'
    )
    
    # LLM configuration
    llm_group = parser.add_argument_group('LLM configuration')
    llm_group.add_argument(
        '--llm',
        default='groq',
        help='LLM provider: groq (free, fast) or openai (paid, reliable) - default: groq'
    )
    llm_group.add_argument(
        '--model',
        help='LLM model name'
    )
    llm_group.add_argument(
        '--list-llms',
        action='store_true',
        help='List available LLM providers and exit'
    )

    # Fuzzing parameters
    fuzzing_group = parser.add_argument_group('fuzzing parameters')
    fuzzing_group.add_argument(
        '--iterations',
        type=int,
        default=50,
        help='Maximum number of iterations (default: 50)'
    )
    fuzzing_group.add_argument(
        '--metric',
        choices=['instruction_count'],
        default='instruction_count',
        help='Resource metric to maximize (default: instruction_count)'
    )

    # Configuration and output
    config_group = parser.add_argument_group('configuration')
    config_group.add_argument(
        '--config',
        default='config/config.yaml',
        help='Configuration file path (default: config/config.yaml)'
    )
    config_group.add_argument(
        '--output',
        help='Output file for results (default: auto-generated)'
    )
    config_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    config_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output (equivalent to --log-level DEBUG)'
    )
    
    # Reporting options
    reporting_group = parser.add_argument_group('reporting options')
    reporting_group.add_argument(
        '--enable-reporting',
        action='store_true',
        default=True,
        help='Enable campaign reporting with graphs (default: enabled)'
    )
    reporting_group.add_argument(
        '--disable-reporting',
        action='store_false',
        dest='enable_reporting',
        help='Disable campaign reporting'
    )
    
    # Utility options
    utility_group = parser.add_argument_group('utility options')
    utility_group.add_argument(
        '--clean',
        action='store_true',
        help='Clean all generated reports and files'
    )

    return parser

def list_available_llms():
    """List available LLM providers"""
    print("Available LLM Providers:")
    print("=" * 50)

    try:
        availability = LLMFactory.list_available_providers()

        for provider, available in availability.items():
            status = "✓ Available" if available else "✗ Not Available"
            print(f"{provider:15} {status}")

        print("\nNotes:")
        print("- 'groq' offers free tier with ultra-fast 70B parameter models")
        print("- 'openai' requires paid API key but provides excellent reliability")
        print("- Set GROQ_API_KEY or OPENAI_API_KEY environment variables in .env file")

    except Exception as e:
        print(f"Error checking LLM availability: {e}")

def validate_program(program_path: str) -> bool:
    """Validate that the program exists and is executable"""
    path = Path(program_path)
    
    if not path.exists():
        print(f"Error: Program not found: {program_path}")
        return False
    
    if not path.is_file():
        print(f"Error: Path is not a file: {program_path}")
        return False
    
    if not os.access(str(path), os.X_OK):
        print(f"Error: Program is not executable: {program_path}")
        print(f"Try: chmod +x {program_path}")
        return False
    
    return True

def validate_input_spec(input_spec_file: str) -> bool:
    """Validate that the input specification file exists"""
    path = Path(input_spec_file)
    
    if not path.exists():
        print(f"Error: Input specification file not found: {input_spec_file}")
        return False
    
    if not path.suffix == '.yaml' and not path.suffix == '.yml':
        print(f"Error: Input specification file must be YAML: {input_spec_file}")
        return False
    
    return True

def clean_generated_files():
    """Clean all generated files"""
    import subprocess
    import sys
    from pathlib import Path
    
    cleanup_script = Path(__file__).parent.parent / "cleanup.py"
    if cleanup_script.exists():
        subprocess.run([sys.executable, str(cleanup_script)])
    else:
        print("Cleanup script not found. Use: python cleanup.py")
    return 0

def main():
    """Main entry point"""
    # Load environment variables from .env file
    load_env_file()
    
    parser = create_arg_parser()
    args = parser.parse_args()

    # Handle special commands
    if args.list_llms:
        check_api_keys()
        list_available_llms()
        return 0
        
    if args.clean:
        return clean_generated_files()

    # Validate required arguments
    if not args.program_path:
        print("Error: --program is required")
        print("Use --help for usage information")
        return 1
    
    if not args.input_spec_file:
        print("Error: --input-spec is required")
        print("Use --help for usage information")
        return 1

    # Setup logging
    log_level = 'DEBUG' if args.verbose else args.log_level
    logger = setup_logger(log_level)

    try:
        # Validate inputs
        if not validate_program(args.program_path):
            return 1
        
        if not validate_input_spec(args.input_spec_file):
            return 1

        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return 1

        # Initialize PathoGen
        logger.info("Initializing PathoGen...")
        pathogen = PathoGen(str(config_path))

        # Override config with command line arguments
        if args.iterations:
            pathogen.config['pathogen']['max_iterations'] = args.iterations

        # Initialize LLM
        logger.info(f"Initializing LLM: {args.llm}")
        pathogen.initialize_llm(args.llm, args.model)

        # Show program and input spec information
        logger.info(f"Program: {args.program_path}")
        logger.info(f"Input specification: {args.input_spec_file}")

        # Run fuzzing campaign
        logger.info("Starting fuzzing campaign...")
        results = pathogen.run_campaign(
            program_path=args.program_path,
            input_spec_file=args.input_spec_file,
            resource_metric=args.metric,
            max_iterations=args.iterations,
            enable_reporting=args.enable_reporting
        )

        # Display results
        logger.info("Fuzzing campaign completed!")
        logger.info(f"Total iterations: {results.total_iterations}")
        logger.info(f"Convergence iteration: {results.convergence_iteration}")

        print("\nTop 5 Best Inputs:")
        print("=" * 60)
        for i, (input_data, score) in enumerate(results.best_inputs[:5], 1):
            print(f"{i}. Score: {score:.0f} instructions")
            print(f"   Input: {input_data}")
            print()

        # Save results
        output_path = pathogen.save_results(results, args.output)
        logger.info(f"Results saved to: {output_path}")

        # Show reporting information
        if args.enable_reporting:
            logger.info("Campaign report generated with the following graphs:")
            logger.info("- Input Size vs Instruction Count")
            logger.info("- Instruction Count Progress Over Iterations")
            logger.info("- Instruction Count Distribution")
            logger.info("- Instruction Count by Input Size Category")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())