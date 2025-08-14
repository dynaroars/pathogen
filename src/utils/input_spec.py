# Input specification file handling
# Loads and processes input specification files with custom size calculation functions

import yaml
import os
import ast
from typing import Dict, List, Any, Callable, Tuple
from pathlib import Path
import logging

class InputSpecification:
    """Handles input specification files with custom size calculation functions"""
    
    def __init__(self, spec_file_path: str):
        self.spec_file_path = Path(spec_file_path)
        self.logger = logging.getLogger(__name__)
        
        if not self.spec_file_path.exists():
            raise FileNotFoundError(f"Input specification file not found: {spec_file_path}")
        
        self._load_specification()
    
    def _load_specification(self):
        """Load and parse the input specification file"""
        try:
            with open(self.spec_file_path, 'r') as f:
                content = f.read()
                
            # Split YAML content and Python functions
            parts = content.split('\n\n# Custom size function')
            yaml_content = parts[0]
            
            # Load YAML specification
            spec_data = yaml.safe_load(yaml_content)
            self.spec = spec_data['input_specification']
            
            # Load custom function if present
            self.custom_function = None
            if len(parts) > 1:
                python_code = parts[1].strip()
                if python_code.startswith('def '):
                    self.custom_function = self._load_custom_function(python_code)
            
            self.logger.info(f"Loaded input specification: {self.spec['name']}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load input specification: {e}")
    
    def _load_custom_function(self, python_code: str) -> Callable:
        """Safely load and compile custom size calculation function"""
        try:
            # Parse the function to ensure it's safe
            tree = ast.parse(python_code)
            
            # Verify it contains only a single function definition
            if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
                raise ValueError("Custom function must contain exactly one function definition")
            
            func_node = tree.body[0]
            func_name = func_node.name
            
            # Execute the function definition in a restricted namespace
            namespace = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'tuple': tuple,
                    'dict': dict,
                    'isinstance': isinstance,
                    'ValueError': ValueError,
                    'TypeError': TypeError,
                    'import': __import__,  # Allow ast import
                }
            }
            
            exec(compile(tree, '<input_spec>', 'exec'), namespace)
            
            if func_name not in namespace:
                raise ValueError(f"Function {func_name} not found after execution")
            
            self.logger.info(f"Loaded custom size function: {func_name}")
            return namespace[func_name]
            
        except Exception as e:
            raise RuntimeError(f"Failed to load custom function: {e}")
    
    def calculate_size(self, input_str: str) -> int:
        """Calculate input size based on specified method"""
        try:
            calculation_method = self.spec['size_calculation']
            
            if calculation_method == 'length':
                return len(input_str)
            elif calculation_method == 'bytes':
                return len(input_str.encode('utf-8'))
            elif self.custom_function:
                return self.custom_function(input_str)
            else:
                # If custom function name specified but not loaded, fall back to length
                self.logger.warning(f"Custom function '{calculation_method}' not found, using length")
                return len(input_str)
                
        except Exception as e:
            self.logger.warning(f"Size calculation failed: {e}, using length as fallback")
            return len(input_str)
    
    def get_name(self) -> str:
        """Get specification name"""
        return self.spec['name']
    
    def get_description(self) -> str:
        """Get input description"""
        return self.spec['description']
    
    def get_valid_examples(self) -> List[str]:
        """Get list of valid input examples"""
        return self.spec.get('valid_examples', [])
    
    def get_invalid_examples(self) -> List[str]:
        """Get list of invalid input examples"""
        return self.spec.get('invalid_examples', [])
    
    def get_prompt_context(self) -> Dict[str, str]:
        """Get context data for prompt template formatting"""
        valid_examples_text = "\n".join([f"- {ex}" for ex in self.get_valid_examples()])
        invalid_examples_text = "\n".join([f"- {ex}" for ex in self.get_invalid_examples()])
        
        return {
            'input_description': self.get_description(),
            'valid_examples': valid_examples_text,
            'invalid_examples': invalid_examples_text,
            'size_calculation': self.spec['size_calculation']
        }
    
    def format_previous_best(self, best_inputs: List[Tuple[str, float]]) -> str:
        """Format previous best inputs with size and score information"""
        if not best_inputs:
            return "No previous successful inputs yet"
        
        formatted_lines = []
        for input_data, score in best_inputs[:5]:  # Show top 5
            size = self.calculate_size(input_data)
            formatted_lines.append(f"Input: {input_data} | Size: {size} | Score: {score:.0f} instructions")
        
        return "\n".join(formatted_lines)
    
    @classmethod
    def create_default_spec_file(cls, target_name: str, output_path: str, 
                                description: str, valid_examples: List[str], 
                                invalid_examples: List[str], size_calculation: str = "length"):
        """Create a default input specification file"""
        spec_content = f"""input_specification:
  name: "{target_name} Input Specification"
  description: |
    {description}
  
  size_calculation: "{size_calculation}"
  
  valid_examples:
{chr(10).join([f'    - "{ex}"' for ex in valid_examples])}
  
  invalid_examples:
{chr(10).join([f'    - "{ex}"' for ex in invalid_examples])}
"""
        
        with open(output_path, 'w') as f:
            f.write(spec_content)
        
        return output_path