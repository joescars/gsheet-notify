"""
Configuration management for the Google Spreadsheet Monitor
Handles loading configuration from environment variables, config files, and API keys.
"""
import os
import sys
import yaml
import logging

try:
    # python-dotenv allows loading environment variables from a .env file
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - handled gracefully if not installed
    load_dotenv = None

def setup_logging():
    """Set up logging configuration"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "app.log")),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def _mask(value: str, keep: int = 4) -> str:
    """Mask sensitive values for logging (keeps last N chars)."""
    if value is None:
        return "None"
    v = str(value)
    if len(v) <= keep * 2:
        return "***"  # too short, mask entirely
    return f"***{v[-keep:]}"


def _load_dotenv_files(base_dir: str):
    """Attempt to load environment variables from .env files.

    Search order:
    1. ENV_FILE environment variable if set
    2. .env in the app base directory (gsheet-notifier-copilot)
    3. .env in the repository root (parent of base_dir)
    4. Fallback to python-dotenv's find_dotenv automatic discovery
    """
    if not load_dotenv:  # library not installed
        logger.debug("python-dotenv not installed; skipping .env loading")
        return

    candidates = []
    if os.environ.get("ENV_FILE"):
        candidates.append(os.environ["ENV_FILE"])
    candidates.append(os.path.join(base_dir, ".env"))
    candidates.append(os.path.join(os.path.dirname(base_dir), ".env"))

    loaded_any = False
    for path in candidates:
        if os.path.isfile(path):
            if load_dotenv(path, override=False):
                logger.info(f"Loaded environment variables from {path}")
                loaded_any = True
            else:
                logger.debug(f"Found {path} but load_dotenv returned False (possibly already loaded)")
    if not loaded_any:
        # Last resort automatic discovery
        try:
            from dotenv import find_dotenv  # local import to avoid unused if missing
            auto_path = find_dotenv(usecwd=True)
            if auto_path:
                if load_dotenv(auto_path, override=False):
                    logger.info(f"Loaded environment variables from discovered {auto_path}")
        except Exception as e:  # pragma: no cover
            logger.debug(f"Automatic .env discovery failed: {e}")


def load_config():
    """Load configuration merging (in precedence order):

    1. Default base values defined in code
    2. config.yaml (if present)
    3. Environment variables (including those populated from .env via python-dotenv)

    Notes:
    - A .env file can be placed in the app directory or repository root.
    - Set ENV_FILE to point to a custom path if needed.
    - Existing process environment variables are NOT overridden by .env (default python-dotenv behavior).
    - Sensitive values are masked in logs.
    """
    # Set default configuration
    config = {
        'spreadsheet_id': None,  # school sheet
        'range_name': None,
        'polling_interval': None,  # seconds
        'notification_topic': None,  # ntfy topic',
        'port': 5588,
        'host': '0.0.0.0',
        'api_key': None
    }
    
    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Load .env values before reading environment variables
    _load_dotenv_files(base_dir)

    # Load from config file if it exists (lower precedence than explicit env vars)
    config_file = os.path.join(base_dir, 'config.yaml')
    if os.path.exists(config_file):
        logger.info(f"Loading configuration from {config_file}")
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config and isinstance(file_config, dict):
                    config.update(file_config)
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
    
    # Override with environment variables
    env_mappings = {
        'GOOGLE_API_KEY': 'api_key',
        'SPREADSHEET_ID': 'spreadsheet_id',
        'RANGE_NAME': 'range_name',
        'POLLING_INTERVAL': 'polling_interval',
        'NOTIFICATION_TOPIC': 'notification_topic',
        'PORT': 'port',
        'HOST': 'host'
    }
    
    for env_var, config_key in env_mappings.items():
        if env_var in os.environ and os.environ.get(env_var) not in (None, ""):
            value = os.environ.get(env_var)
            # Convert numeric values
            if config_key in ['polling_interval', 'port']:
                try:
                    value = int(value)
                except ValueError:
                    logger.warning(f"Could not convert {env_var}={_mask(value)} to int. Using existing/default.")
                    continue
            config[config_key] = value
            log_value = _mask(value) if config_key in ['api_key'] else value
            logger.info(f"Applied env var {env_var} -> {config_key}={log_value}")
    
    # Final check for API key
    if not config.get('api_key'):
        logger.error("No API key found. Provide GOOGLE_API_KEY via .env, environment, or config.yaml")
        return None
    
    return config
