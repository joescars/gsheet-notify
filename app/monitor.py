"""
Core monitoring logic for the Google Spreadsheet Cell Monitor
Handles checking the spreadsheet and triggering notifications.
"""
import logging
import time
import threading
from datetime import datetime

from app.sheets_client import SheetsClient
from app.notifier import NotificationManager

logger = logging.getLogger(__name__)

class SheetMonitor:
    """
    Main monitoring class that checks the spreadsheet cell for changes
    and triggers notifications based on the content.
    """
    
    def __init__(self, config):
        """
        Initialize the sheet monitor
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.sheets_client = SheetsClient(config)
        self.notification_manager = NotificationManager(config)
        self.last_check_result = "No check performed yet"
        self.last_check_time = ""
        self.status_history = []  # List of (timestamp, status, message) tuples
        self.max_history = 50  # Maximum number of history entries to keep
    
    def check_cell(self):
        """
        Check the cell in the spreadsheet and process its value.
        
        Returns:
            bool: True if a notification was triggered, False otherwise
        """
        try:
            # Get the cell value from the Google Sheets API
            result = self.sheets_client.get_cell_value_with_retry()
            cell_value = result.get('value', '')
            is_new = result.get('is_new', False)
            timestamp = result.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Update last check time
            self.last_check_time = f"Last Checked: {timestamp}"
            
            # Check for errors
            if 'error' in result:
                error_msg = f"Error checking spreadsheet: {result['error']}"
                logger.error(error_msg)
                self.last_check_result = error_msg
                self._add_history_entry('error', error_msg)
                return False
            
            # If value hasn't changed and it's not the first check, just return
            if not is_new and len(self.status_history) > 0:
                message = f"Current value: '{cell_value}'"
                logger.debug(message)
                self.last_check_result = message
                return False
            
            # Process the cell value
            if 'DEPARTED' in cell_value and 'NOT' not in cell_value:
                message = f"*** {cell_value} ***"
                logger.info(message)
                self.last_check_result = message
                
                # Add to history
                self._add_history_entry('departed', message)
                
                # Send notification
                self._send_notification(message)
                return True
            else:
                message = f"Current Status: '{cell_value}'"
                logger.info(message)
                self.last_check_result = message
                
                # Add to history
                self._add_history_entry('normal', message)
                return False
                
        except Exception as e:
            error_msg = f"Error checking spreadsheet: {str(e)}"
            logger.error(error_msg)
            self.last_check_result = error_msg
            self._add_history_entry('error', error_msg)
            return False
    
    def _add_history_entry(self, status, message):
        """
        Add an entry to the status history
        
        Args:
            status (str): Status type ('normal', 'departed', 'error')
            message (str): The status message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_history.append((timestamp, status, message))
        
        # Trim history if needed
        if len(self.status_history) > self.max_history:
            self.status_history = self.status_history[-self.max_history:]
    
    def _send_notification(self, message):
        """
        Send notification using the notification manager
        
        Args:
            message (str): The message to send
            
        Returns:
            bool: True if notification was sent successfully
        """
        return self.notification_manager.send_notification(message)
    
    def get_history(self, limit=10):
        """
        Get the recent status history
        
        Args:
            limit (int): Maximum number of entries to return
            
        Returns:
            list: List of recent (timestamp, status, message) tuples
        """
        return self.status_history[-limit:] if self.status_history else []


class MonitoringService:
    """
    Service that manages the monitoring thread and scheduling
    """
    
    def __init__(self, config):
        """
        Initialize the monitoring service
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.polling_interval = config.get('polling_interval', 30)
        self.monitor = SheetMonitor(config)
        self.stop_event = threading.Event()
        self.thread = None
        self.is_active = False
    
    def start(self):
        """
        Start the monitoring service if it's not already running
        
        Returns:
            bool: True if started successfully, False if already running
        """
        if self.is_active and self.thread and self.thread.is_alive():
            logger.warning("Monitoring service is already running")
            return False
        
        logger.info(f"Starting monitoring service with {self.polling_interval} second interval")
        self.stop_event.clear()
        self.is_active = True
        
        # Run an immediate check
        self.monitor.check_cell()
        
        # Start the monitoring thread
        self.thread = threading.Thread(target=self._monitoring_loop)
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def stop(self):
        """
        Stop the monitoring service if it's running
        
        Returns:
            bool: True if stopped successfully, False if not running
        """
        if not self.is_active:
            logger.warning("Monitoring service is not running")
            return False
        
        logger.info("Stopping monitoring service")
        self.stop_event.set()
        self.is_active = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            
        return True
    
    def _monitoring_loop(self):
        """
        Main monitoring loop that runs in a background thread
        """
        logger.info("Monitoring loop started")
        
        while not self.stop_event.is_set():
            try:
                # Wait for the specified interval or until stop is called
                if self.stop_event.wait(self.polling_interval):
                    break
                
                # Check the cell
                self.monitor.check_cell()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                # Continue the loop despite errors
        
        logger.info("Monitoring loop stopped")
    
    def check_now(self):
        """
        Perform an immediate check regardless of the monitoring schedule
        
        Returns:
            bool: Result from the check_cell method
        """
        logger.info("Performing immediate check")
        return self.monitor.check_cell()
    
    def get_status(self):
        """
        Get the current status of the monitoring service
        
        Returns:
            dict: Status information including:
                - is_active: Whether the service is running
                - last_result: The last check result
                - last_check_time: When the last check was performed
                - history: Recent status history
        """
        return {
            'is_active': self.is_active,
            'last_result': self.monitor.last_check_result,
            'last_check_time': self.monitor.last_check_time,
            'history': self.monitor.get_history(10)
        }
