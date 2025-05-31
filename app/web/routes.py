"""
Flask routes for the Google Spreadsheet Monitor web interface
"""
import logging
from flask import render_template, jsonify, redirect, url_for, request

logger = logging.getLogger(__name__)

def register_routes(app, monitoring_service):
    """
    Register all routes for the Flask application
    
    Args:
        app: Flask application instance
        monitoring_service: The monitoring service instance
    """
    
    @app.route('/')
    def index():
        """Main page with user interface"""
        status = monitoring_service.get_status()
        return render_template(
            'index.html', 
            is_active=status['is_active'],
            result=status['last_result'],
            check_time=status['last_check_time'],
            history=status['history']
        )
    
    @app.route('/start', methods=['GET', 'POST'])
    def start_polling_endpoint():
        """Endpoint to start polling the spreadsheet"""
        if monitoring_service.is_active:
            message = "Monitoring is already active"
            logger.info(message)
            
            if request.method == 'POST':
                return redirect(url_for('index'))
            else:
                return jsonify({"status": "already_running", "message": message})
        
        # Start the monitoring service
        success = monitoring_service.start()
        message = "Started monitoring spreadsheet" if success else "Failed to start monitoring"
        logger.info(message)
        
        if request.method == 'POST':
            return redirect(url_for('index'))
        else:
            return jsonify({
                "status": "started" if success else "error",
                "message": message
            })
    
    @app.route('/stop', methods=['GET', 'POST'])
    def stop_polling_endpoint():
        """Endpoint to stop polling the spreadsheet"""
        if not monitoring_service.is_active:
            message = "Monitoring is not active"
            logger.info(message)
            
            if request.method == 'POST':
                return redirect(url_for('index'))
            else:
                return jsonify({"status": "not_running", "message": message})
        
        # Stop the monitoring service
        success = monitoring_service.stop()
        message = "Stopped monitoring spreadsheet" if success else "Failed to stop monitoring"
        logger.info(message)
        
        if request.method == 'POST':
            return redirect(url_for('index'))
        else:
            return jsonify({
                "status": "stopped" if success else "error",
                "message": message
            })
    
    @app.route('/status', methods=['GET'])
    def status_endpoint():
        """Endpoint to check the status of the polling"""
        status = monitoring_service.get_status()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "status": "active" if status['is_active'] else "inactive",
                "message": f"Monitoring is currently {'active' if status['is_active'] else 'inactive'}",
                "last_result": status['last_result'],
                "last_check_time": status['last_check_time'],
                "history": status['history']
            })
        else:
            return redirect(url_for('index'))
    
    @app.route('/check_now', methods=['POST'])
    def check_now():
        """Endpoint to manually trigger a check"""
        monitoring_service.check_now()
        return redirect(url_for('index'))
    
    @app.route('/history', methods=['GET'])
    def history():
        """Endpoint to view the history of checks"""
        status = monitoring_service.get_status()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "history": status['history']
            })
        else:
            return render_template(
                'history.html',
                history=status['history'],
                is_active=status['is_active']
            )
