# PathoGen: LLM-Guided Performance Testing Tool

PathoGen is a novel fuzzing tool that combines evolutionary search with Large Language Model (LLM) guidance to generate inputs that maximize instruction count in external programs. PathoGen analyzes standalone executable programs and generates concrete pathological inputs that exhibit worst-case runtime behavior, measured precisely using the Linux perf tool.

## Features

- **LLM-Guided Generation**: Uses LLMs to generate syntactically valid and semantically meaningful test inputs
- **Size-Aware Input Generation**: Generates inputs of varying sizes (10, 25, 40, 55, ...) to test complexity scaling
- **Instruction Count Optimization**: Focuses exclusively on maximizing runtime execution via perf tool
- **Input Specification Files**: YAML-based input format definitions with custom size calculation functions
- **Error-Based Validation**: Validates inputs through execution rather than complex pre-parsing
- **High-Performance LLMs**: Optimized for Groq (free, fast) and OpenAI (paid, reliable) providers
- **Standalone Program Analysis**: Works with any executable program that reads from stdin

## Quick Start

### Prerequisites

**Required System Dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get install linux-perf

# RHEL/CentOS
sudo yum install perf

# Arch Linux
sudo pacman -S perf
```

### Installation

```bash
git clone https://github.com/your-org/pathogen.git
cd pathogen
pip install -r requirements.txt

# Set up API keys in .env file
echo "GROQ_API_KEY=your_groq_api_key_here" >> .env
echo "# OPENAI_API_KEY=your_openai_api_key_here" >> .env
```

### Basic Usage

```bash
# Test quicksort program with input specification
python src/main.py --program examples/quicksort.py --input-spec input_specs/quicksort_spec.yaml

# Test regex matcher with OpenAI (requires paid API key)
python src/main.py --program examples/regex_matcher.py --input-spec input_specs/regex_spec.yaml --llm openai

# Test your own program
python src/main.py --program ./my_program --input-spec input_specs/custom_spec.yaml

# List available LLM providers
python src/main.py --list-llms

# Clean generated reports and files
python src/main.py --clean
```

### Cleanup Commands

PathoGen generates reports, result files, and cache data during analysis. Clean up with:

```bash
# Method 1: Through main program (recommended)
python src/main.py --clean

# Method 2: Direct cleanup script  
python cleanup.py

# Method 3: Quick shell script
./clean.sh

# Method 4: Manual cleanup
rm -rf reports/* results/* .pytest_cache/
```

### Python API

```python
from src.core.pathogen import PathoGen

# Initialize PathoGen
pathogen = PathoGen("config/config.yaml")
pathogen.initialize_llm("groq", "llama2-70b-4096")

# Run campaign with external program
results = pathogen.run_campaign(
    program_path="examples/quicksort.py",
    input_spec_file="input_specs/quicksort_spec.yaml",
    resource_metric="instruction_count",
    max_iterations=100
)

# Analyze results (shows input, size, and instruction count)
for input_data, score in results.best_inputs[:5]:
    print(f"Input: {input_data}, Score: {score:.0f} instructions")
```

## Architecture

PathoGen follows a modular architecture optimized for performance analysis:

### Core Components
- **PathoGen Engine**: Main fuzzing loop with size-aware input generation (15 inputs per iteration)
- **LLM Abstraction Layer**: Unified interface for high-performance LLM providers
- **Program Executor**: Runs target programs with perf-based instruction counting
- **Resource Scorer**: Evaluates candidates based purely on instruction count
- **Input Specification System**: YAML-based input format definitions with custom size functions
- **Error-Based Validator**: Validates inputs through execution and error message analysis

### Supported LLM Providers
- **Groq** (API): Ultra-fast inference with 70B parameter models, free tier available
- **OpenAI** (API): Reliable GPT-3.5/GPT-4 with excellent algorithmic reasoning

### Sample Programs
- **QuickSort** (`examples/quicksort.py`): Demonstrates O(n²) worst-case behavior on sorted inputs
- **Regex Matcher** (`examples/regex_matcher.py`): Tests catastrophic backtracking patterns
- **JSON Parser** (`examples/json_parser.py`): Explores performance on deeply nested structures
- **Your Programs**: Any executable that reads from stdin and can be measured with perf

### Input Specification Files
PathoGen uses YAML files to define input formats, validation rules, and size calculation methods:

```yaml
input_specification:
  name: "QuickSort Integer List"
  description: "A list of integers for sorting analysis"
  size_calculation: "count_elements"  # or "length", "bytes", custom function
  
  valid_examples:
    - "[5, 2, 8, 1, 9]"
    - "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
  
  invalid_examples:
    - "hello world"
    - "[a, b, c]"

# Custom size function (if needed)
def count_elements(input_str: str) -> int:
    import ast
    parsed = ast.literal_eval(input_str)
    return len(parsed)
```

## Configuration

PathoGen uses YAML configuration files optimized for instruction count analysis:

```yaml
# config/config.yaml
pathogen:
  max_iterations: 100
  elite_size: 3
  
  # Size-aware input generation
  input_generation:
    inputs_per_iteration: 15
    size_progression:
      start_size: 10
      increment: 15

  # High-performance LLM settings
  llm:
    provider: "groq"  # groq (free, fast) or openai (paid, reliable)
    model: "llama2-70b-4096"
    temperature: 0.7
    max_tokens: 1000

  # Focus on instruction count only
  resource_metrics:
    - instruction_count
```

## Examples

### QuickSort Analysis
```bash
cd examples
python quicksort_example.py
```

This demonstrates finding inputs that trigger QuickSort's O(n²) worst-case behavior. PathoGen typically discovers that sorted arrays like `[1,2,3,4,5,6,7,8,9,10]` maximize instruction count.

### Regex Engine Analysis
```bash
cd examples  
python regex_example.py
```

Finds regex patterns causing catastrophic backtracking, such as:
- `{"pattern": "(a+)+", "text": "aaaaaaaaaaaaaaaaaaaaX"}`
- `{"pattern": "^(a|a)*$", "text": "aaaaaaaaaaaaaaaaaa"}`

## Extending PathoGen

### Adding New Programs

To analyze a new program with PathoGen:

1. **Create your executable program** that reads from stdin:
```bash
#!/usr/bin/env python3
import sys
import json

def main():
    input_data = sys.stdin.read().strip()
    # Process input_data
    # Output results to stdout
    print(result)

if __name__ == "__main__":
    main()
```

2. **Create an input specification file** (`my_spec.yaml`):
```yaml
input_specification:
  name: "My Program Input"
  description: "Description of expected input format"
  size_calculation: "length"  # or custom function
  
  valid_examples:
    - "example input 1"
    - "example input 2"
  
  invalid_examples:
    - "bad input"
```

3. **Run PathoGen**:
```bash
python src/main.py --program ./my_program --input-spec my_spec.yaml
```

## File Management

### Generated Files

PathoGen creates several types of files during analysis:

```
pathogen/
├── reports/                     # Generated analysis reports
│   ├── pathogen_program_timestamp_report.pdf
│   └── pathogen_program_timestamp_data.json
├── results/                     # Campaign result exports  
│   └── pathogen_results_timestamp.json
├── .pytest_cache/              # Test cache files
└── **/__pycache__/             # Python bytecode cache
```

### File Types Explained

- **PDF Reports** (`*.pdf`) - Visual reports with graphs and analysis
- **JSON Data** (`*_data.json`) - Raw measurement data for further analysis  
- **Result Files** (`pathogen_results_*.json`) - Complete campaign results
- **Cache Files** (`*.pyc`, `__pycache__/`) - Python compilation cache

### Cleanup Commands

```bash
# Clean everything (recommended)
python src/main.py --clean

# Clean specific file types
python cleanup.py "*.pdf"        # Only PDF reports
python cleanup.py "*timestamp*"  # Specific analysis session

# Manual cleanup
rm -rf reports/* results/*       # Remove all generated files
find . -name "*.pyc" -delete     # Remove Python cache
```

### Cleanup Output

```
PathoGen Cleanup Utility
========================================
✓ Cleaned 24 files from reports/
✓ Cleaned 5 files from results/  
✓ Removed .pytest_cache/ directory
✓ Removed 15 cache/temp files

Cleanup Summary:
📁 Total items removed: 44
🧹 Repository cleaned successfully!
```

### Best Practices

- **Clean regularly** - Reports accumulate quickly during development
- **Before commits** - Always clean before git commits  
- **Backup important results** - Save key analysis files before cleaning
- **Disk space** - Large campaigns can generate MB of data

## Research Applications

PathoGen is designed for:
- **Complexity Analysis**: Generate concrete worst-case inputs
- **Performance Testing**: Find performance bottlenecks and edge cases
- **Security Research**: Discover algorithmic complexity attacks
- **Benchmarking**: Create challenging test suites for algorithms

## Performance Monitoring

PathoGen uses Linux `perf` for precise resource measurement:

```bash
# Instruction counting with perf
perf stat -e instructions:u ./target_program < input.txt

# Memory and cache monitoring  
perf stat -e instructions:u,cache-misses:u,page-faults:u ./program
```

PathoGen requires perf tool for accurate instruction counting - no fallback methods are used.

## Limitations

- **Linux Dependency**: perf-based monitoring requires Linux
- **LLM Quality**: Results depend on LLM's understanding of the target domain
- **Resource Requirements**: Large programs may require significant compute resources
- **Convergence**: May require tuning evolutionary parameters for optimal results

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest tests/`)
5. Submit a pull request

## Development Setup

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Code formatting
black src/ examples/ tests/
isort src/ examples/ tests/

# Linting
flake8 src/ examples/ tests/

# Clean generated files
python src/main.py --clean
```

## License

MIT License - see LICENSE file for details.

## Citation

If you use PathoGen in your research, please cite:

```bibtex
@inproceedings{pathogen2024,
  title={PathoGen: LLM-Guided Performance Testing via Evolutionary Fuzzing},
  author={Your Name},
  booktitle={Conference Proceedings},
  year={2024}
}
```

## Troubleshooting

### Common Issues

**Groq API Error**
```bash
# Check your API key in .env file
echo $GROQ_API_KEY
# Verify account status at https://console.groq.com/
```

**Perf Permission Denied**
```bash
# Enable perf for non-root users
echo 0 | sudo tee /proc/sys/kernel/perf_event_paranoid
```

**Firefox JS Shell Not Found**
```bash
# Install SpiderMonkey on Ubuntu/Debian
sudo apt-get install libmozjs-78-dev
# Or compile from source
wget https://archive.mozilla.org/pub/firefox/releases/.../jsshell-linux-x86_64.zip
```

### Getting Help

- Check the [Issues](https://github.com/your-org/pathogen/issues) page
- Review example scripts in the `examples/` directory
- Consult the configuration files in `config/`
- Enable debug logging with `--log-level DEBUG`

## Roadmap

- [ ] Support for more programming languages (Java, C++, Rust)
- [ ] Integration with popular benchmarking frameworks
- [ ] Web interface for easier usage
- [ ] Advanced evolutionary strategies (multi-objective optimization)
- [ ] Distributed execution for large-scale testing
- [ ] Integration with CI/CD pipelines
- [ ] Support for Windows and macOS resource monitoring

## Acknowledgments

PathoGen builds upon research in:
- Evolutionary fuzzing and genetic algorithms
- Large Language Models for code generation
- Program complexity analysis and worst-case input generation
- Performance testing and benchmarking methodologies
