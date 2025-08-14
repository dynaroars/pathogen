# Environment variable loader
# Safely loads environment variables from .env files

import os
from pathlib import Path

def load_env_file(env_path: str = None):
    """Load environment variables from .env file"""
    if env_path is None:
        # Look for .env file in project root
        current_dir = Path(__file__).parent.parent.parent
        env_path = current_dir / '.env'
    
    env_path = Path(env_path)
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✓ Loaded environment variables from {env_path}")
    else:
        print(f"No .env file found at {env_path}")

def check_api_keys():
    """Check if required API keys are available"""
    keys_status = {
        'GROQ_API_KEY': bool(os.getenv('GROQ_API_KEY')),
        'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY'))
    }
    
    available_keys = [k for k, v in keys_status.items() if v]
    
    if available_keys:
        print(f"✓ Available API keys: {', '.join(available_keys)}")
    else:
        print("⚠ No API keys found. Add them to .env file or set as environment variables.")
    
    return keys_status