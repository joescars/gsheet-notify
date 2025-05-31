#!/usr/bin/env python3
"""
Google Spreadsheet Cell Monitor - Main Entry Point
This script starts the monitoring service and web interface.
"""
import sys
import logging
from app.config import load_config, setup_logging
from app.monitor import MonitoringService
from app.web.app import create_app

def main():
    """Main entry point for the application"""
    # Set up logging
    logger = setup_logging()
    
    # Load configuration
    logger.info("Loading configuration...")
    config = load_config()
    
    if not config:
        logger.error("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Create monitoring service
    logger.info("Initializing monitoring service...")
    monitoring_service = MonitoringService(config)
    
    # Create Flask app
    logger.info("Creating Flask application...")
    app = create_app(config, monitoring_service)
    
    # Log startup information
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 5588)
    
    logger.info("Starting Google Spreadsheet Monitor server...")
    logger.info(f"Access the web interface at http://<host>:{port}/")
    logger.info("API Endpoints:")
    logger.info(f"  - http://<host>:{port}/start - Begin monitoring")
    logger.info(f"  - http://<host>:{port}/stop - Stop monitoring")
    logger.info(f"  - http://<host>:{port}/status - Check monitoring status")
    logger.info(f"  - http://<host>:{port}/check_now - Manually trigger a check")
    logger.info(f"  - http://<host>:{port}/history - View check history")
    
    # Run the Flask application
    app.run(
        host=host,
        port=port,
        debug=config.get('debug', False),
        threaded=True
    )

if __name__ == "__main__":
    main()
