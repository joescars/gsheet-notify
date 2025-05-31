"""
Notification systems for the Google Spreadsheet Monitor
Handles sending notifications through various channels.
"""
import logging
import requests

logger = logging.getLogger(__name__)

class BaseNotifier:
    """Base class for notification providers"""
    
    def __init__(self, config=None):
        """Initialize the notifier with configuration"""
        self.config = config or {}
    
    def send(self, message, **kwargs):
        """
        Send a notification
        
        Args:
            message (str): The message to send
            **kwargs: Additional parameters specific to the notification channel
            
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send()")

class NtfyNotifier(BaseNotifier):
    """Notification provider using ntfy.sh service"""
    
    def send(self, message, **kwargs):
        """
        Send a notification using ntfy.sh
        
        Args:
            message (str): The message to send
            **kwargs: Additional parameters including:
                - title (str): Notification title
                - priority (str): Priority level (high, default, low)
                - tags (str): Comma-separated tags
                - url (str): URL to open when clicking the notification
                
        Returns:
            bool: True if the notification was sent successfully, False otherwise
        """
        try:
            topic = kwargs.get('topic') or self.config.get('notification_topic', 'joetest333')
            
            headers = {
                'Title': kwargs.get('title', 'Bus Status Alert'),
                'Priority': kwargs.get('priority', 'high'),
                'Tags': kwargs.get('tags', 'bus,alert')
            }
            
            # Add Click URL if provided
            url = kwargs.get('url') or 'https://login.herecomesthebus.com/Map.aspx'
            if url:
                headers['Click'] = url
            
            response = requests.post(
                f'https://ntfy.sh/{topic}',
                data=message.encode('utf-8'),
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Notification sent successfully to ntfy.sh/{topic}")
                return True
            else:
                logger.error(f"Failed to send notification. Status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False

class LogNotifier(BaseNotifier):
    """A simple notifier that only logs messages"""
    
    def send(self, message, **kwargs):
        """
        Log the notification message
        
        Args:
            message (str): The message to log
            **kwargs: Additional parameters (ignored)
            
        Returns:
            bool: Always returns True
        """
        logger.info(f"NOTIFICATION: {message}")
        return True

class NotificationManager:
    """Manages multiple notification providers"""
    
    def __init__(self, config=None):
        """Initialize the notification manager"""
        self.config = config or {}
        self.notifiers = []
        
        # Set up default notifier
        if self.config.get('notification_topic'):
            self.add_notifier(NtfyNotifier(self.config))
        
        # Always add log notifier as a fallback
        self.add_notifier(LogNotifier())
    
    def add_notifier(self, notifier):
        """Add a notification provider"""
        if isinstance(notifier, BaseNotifier):
            self.notifiers.append(notifier)
            return True
        return False
    
    def send_notification(self, message, **kwargs):
        """
        Send notification through all registered providers
        
        Args:
            message (str): The message to send
            **kwargs: Additional parameters for the notification
            
        Returns:
            bool: True if at least one notification was sent successfully
        """
        if not self.notifiers:
            logger.warning("No notification providers configured")
            return False
        
        success = False
        for notifier in self.notifiers:
            if notifier.send(message, **kwargs):
                success = True
        
        return success
