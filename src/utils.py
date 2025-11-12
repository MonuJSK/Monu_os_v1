"""
Utility functions for the Monu OS v1 market update pipeline.
"""

import logging
import os
from datetime import datetime, date
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monu_os.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_env_var(var_name: str, required: bool = True) -> Optional[str]:
    """
    Get environment variable with optional requirement check.

    Args:
        var_name: Name of the environment variable
        required: Whether the variable is required

    Returns:
        The environment variable value or None if not required and not found

    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(var_name)
    if required and not value:
        raise ValueError(f"Required environment variable '{var_name}' not found")
    return value

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging level.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.getLogger().setLevel(numeric_level)

def format_date(dt: datetime) -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object

    Returns:
        Formatted date string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_today_date() -> str:
    """
    Get today's date as string.

    Returns:
        Today's date in YYYY-MM-DD format
    """
    return date.today().strftime("%Y-%m-%d")

def safe_float(value: Any) -> float:
    """
    Safely convert value to float.

    Args:
        value: Value to convert

    Returns:
        Float value or 0.0 if conversion fails
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calculate percentage change between two values.

    Args:
        current: Current value
        previous: Previous value

    Returns:
        Percentage change
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100

def validate_config() -> Dict[str, str]:
    """
    Validate and return configuration from environment variables.

    Returns:
        Dictionary of configuration values

    Raises:
        ValueError: If required configuration is missing
    """
    config = {
        'tvdata_username': get_env_var('TVDATA_USERNAME'),
        'tvdata_password': get_env_var('TVDATA_PASSWORD'),
        'google_sa_json_path': get_env_var('GOOGLE_SA_JSON_PATH'),
        'sheets_id': get_env_var('SHEETS_ID'),
        'telegram_bot_token': get_env_var('TELEGRAM_BOT_TOKEN'),
        'telegram_chat_id': get_env_var('TELEGRAM_CHAT_ID'),
        'claude_api_key': get_env_var('CLAUDE_API_KEY', required=False)
    }

    logger.info("Configuration validated successfully")
    return config
