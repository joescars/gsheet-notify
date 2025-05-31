"""
Configuration management for the Google Spreadsheet Monitor
Handles loading configuration from environment variables, config files, and API keys.
"""
import os
import sys
import yaml
import logging

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

def load_config():
    """
    Load configuration from config.yaml file and environment variables
    Environment variables take precedence over config file values
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
    
    # Load from config file if it exists
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
        if os.environ.get(env_var):
            value = os.environ.get(env_var)
            # Convert numeric values
            if config_key in ['polling_interval', 'port']:
                try:
                    value = int(value)
                except ValueError:
                    logger.warning(f"Could not convert {env_var}={value} to int. Using default.")
                    continue
            config[config_key] = value
    
    # Check for API key in api_key.txt if not set
    if config['api_key'] is None:
        api_key_file = os.path.join(base_dir, 'api_key.txt')
        if os.path.exists(api_key_file):
            logger.info(f"Loading API key from {api_key_file}")
            try:
                with open(api_key_file, 'r') as f:
                    config['api_key'] = f.read().strip()
            except Exception as e:
                logger.error(f"Error loading API key file: {str(e)}")
    
    # Final check for API key
    if config['api_key'] is None:
        logger.error("No API key found. Please set GOOGLE_API_KEY environment variable or create an api_key.txt file")
        return None
    
    return config
