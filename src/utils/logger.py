# Logging configuration utilities
# Provides standardized logging setup for the PathoGen application

import logging
import sys
from typing import Optional

def setup_logger(level: str = "INFO",
                name: Optional[str] = None,
                format_str: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration"""

    if not format_str:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name or 'pathogen')
    logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(format_str)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger
