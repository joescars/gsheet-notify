"""
Tests for the notification system
"""
import unittest
from unittest.mock import patch, MagicMock
from app.notifier import BaseNotifier, NtfyNotifier, LogNotifier, NotificationManager

class TestNotifiers(unittest.TestCase):
    """Test suite for notification classes"""
    
    def test_base_notifier(self):
        """Test that BaseNotifier raises NotImplementedError"""
        notifier = BaseNotifier()
        with self.assertRaises(NotImplementedError):
            notifier.send("Test message")
    
    @patch('app.notifier.requests.post')
    def test_ntfy_notifier(self, mock_post):
        """Test NtfyNotifier send method"""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create notifier and send message
        config = {'notification_topic': 'test-topic'}
        notifier = NtfyNotifier(config)
        result = notifier.send("Test message", title="Test Title")
        
        # Verify the results
        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], 'https://ntfy.sh/test-topic')
        self.assertEqual(kwargs['data'], b'Test message')
        self.assertEqual(kwargs['headers']['Title'], 'Test Title')
    
    @patch('app.notifier.requests.post')
    def test_ntfy_notifier_failure(self, mock_post):
        """Test NtfyNotifier error handling"""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response
        
        # Create notifier and send message
        notifier = NtfyNotifier({'notification_topic': 'test'})
        result = notifier.send("Test message")
        
        # Verify the results
        self.assertFalse(result)
    
    @patch('app.notifier.logger')
    def test_log_notifier(self, mock_logger):
        """Test LogNotifier send method"""
        # Create notifier and send message
        notifier = LogNotifier()
        result = notifier.send("Test message")
        
        # Verify the results
        self.assertTrue(result)
        mock_logger.info.assert_called_once()
    
    def test_notification_manager(self):
        """Test NotificationManager with multiple notifiers"""
        # Create mock notifiers
        mock_notifier1 = MagicMock(spec=BaseNotifier)
        mock_notifier1.send.return_value = True
        
        mock_notifier2 = MagicMock(spec=BaseNotifier)
        mock_notifier2.send.return_value = False
        
        # Create manager and add notifiers
        manager = NotificationManager()
        manager.notifiers = [mock_notifier1, mock_notifier2]
        
        # Send notification
        result = manager.send_notification("Test message", title="Test")
        
        # Verify the results
        self.assertTrue(result)  # True because at least one notifier succeeded
        mock_notifier1.send.assert_called_once()
        mock_notifier2.send.assert_called_once()
    
    def test_notification_manager_empty(self):
        """Test NotificationManager with no notifiers"""
        # Create manager with empty notifier list
        manager = NotificationManager()
        manager.notifiers = []
        
        # Send notification
        result = manager.send_notification("Test message")
        
        # Verify the results
        self.assertFalse(result)  # False because no notifiers to use

if __name__ == '__main__':
    unittest.main()
