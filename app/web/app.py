"""
Flask application creation and configuration for the Google Spreadsheet Monitor
"""
import logging
import os
from flask import Flask

from app.web.routes import register_routes

logger = logging.getLogger(__name__)

def create_app(config, monitoring_service):
    """
    Create and configure the Flask application
    
    Args:
        config (dict): Configuration dictionary
        monitoring_service: The monitoring service instance
        
    Returns:
        Flask: Configured Flask application
    """
    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Create Flask app with paths to static and template folders
    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, 'static'),
        template_folder=os.path.join(base_dir, 'templates')
    )
    
    # Configure Flask
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SECRET_KEY'] = config.get('secret_key', os.urandom(24).hex())
    
    # Register routes with the app
    register_routes(app, monitoring_service)
    
    return app
