"""
Tests for the monitor module
"""
import unittest
from unittest.mock import patch, MagicMock
from app.monitor import SheetMonitor, MonitoringService

class TestSheetMonitor(unittest.TestCase):
    """Test suite for SheetMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Patch the SheetsClient and NotificationManager
        self.sheets_client_patcher = patch('app.monitor.SheetsClient')
        self.notif_manager_patcher = patch('app.monitor.NotificationManager')
        
        self.mock_sheets_client = self.sheets_client_patcher.start()
        self.mock_notif_manager = self.notif_manager_patcher.start()
        
        # Create instance with mock dependencies
        self.config = {'polling_interval': 30}
        self.monitor = SheetMonitor(self.config)
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.sheets_client_patcher.stop()
        self.notif_manager_patcher.stop()
    
    def test_check_cell_normal(self):
        """Test check_cell with normal status"""
        # Configure mock
        mock_client_instance = self.monitor.sheets_client
        mock_client_instance.get_cell_value_with_retry.return_value = {
            'value': 'NORMAL STATUS',
            'is_new': True,
            'timestamp': '2023-01-01 12:00:00'
        }
        
        # Call the method
        result = self.monitor.check_cell()
        
        # Verify results
        self.assertFalse(result)
        self.assertEqual(self.monitor.last_check_result, "Current Status: 'NORMAL STATUS'")
        self.assertEqual(len(self.monitor.status_history), 1)
        self.assertEqual(self.monitor.status_history[0][1], 'normal')
    
    def test_check_cell_departed(self):
        """Test check_cell with departed status"""
        # Configure mock
        mock_client_instance = self.monitor.sheets_client
        mock_client_instance.get_cell_value_with_retry.return_value = {
            'value': 'BUS DEPARTED',
            'is_new': True,
            'timestamp': '2023-01-01 12:00:00'
        }
        
        # Configure notification manager
        mock_notif_instance = self.monitor.notification_manager
        mock_notif_instance.send_notification.return_value = True
        
        # Call the method
        result = self.monitor.check_cell()
        
        # Verify results
        self.assertTrue(result)
        self.assertIn('*** BUS DEPARTED ***', self.monitor.last_check_result)
        mock_notif_instance.send_notification.assert_called_once()
        self.assertEqual(len(self.monitor.status_history), 1)
        self.assertEqual(self.monitor.status_history[0][1], 'departed')
    
    def test_check_cell_error(self):
        """Test check_cell handling errors"""
        # Configure mock to raise an exception
        mock_client_instance = self.monitor.sheets_client
        mock_client_instance.get_cell_value_with_retry.return_value = {
            'value': '',
            'is_new': False,
            'timestamp': '2023-01-01 12:00:00',
            'error': 'Test error'
        }
        
        # Call the method
        result = self.monitor.check_cell()
        
        # Verify results
        self.assertFalse(result)
        self.assertIn('Error checking spreadsheet', self.monitor.last_check_result)
        self.assertEqual(len(self.monitor.status_history), 1)
        self.assertEqual(self.monitor.status_history[0][1], 'error')

class TestMonitoringService(unittest.TestCase):
    """Test suite for MonitoringService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Patch SheetMonitor
        self.monitor_patcher = patch('app.monitor.SheetMonitor')
        self.mock_monitor_class = self.monitor_patcher.start()
        
        # Configure mock
        self.mock_monitor = MagicMock()
        self.mock_monitor_class.return_value = self.mock_monitor
        
        # Create instance
        self.config = {'polling_interval': 0.1}  # Short interval for testing
        self.service = MonitoringService(self.config)
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.monitor_patcher.stop()
        if self.service.is_active:
            self.service.stop()
    
    def test_start_stop(self):
        """Test starting and stopping the service"""
        # Start the service
        self.service.start()
        self.assertTrue(self.service.is_active)
        self.assertIsNotNone(self.service.thread)
        self.assertTrue(self.service.thread.is_alive())
        
        # Try to start again
        result = self.service.start()
        self.assertFalse(result)  # Should return False as already running
        
        # Stop the service
        self.service.stop()
        self.assertFalse(self.service.is_active)
        
        # Try to stop again
        result = self.service.stop()
        self.assertFalse(result)  # Should return False as already stopped
    
    def test_check_now(self):
        """Test immediate check"""
        # Configure mock
        self.mock_monitor.check_cell.return_value = True
        
        # Call method
        result = self.service.check_now()
        
        # Verify results
        self.assertTrue(result)
        self.mock_monitor.check_cell.assert_called_once()
    
    def test_get_status(self):
        """Test status retrieval"""
        # Configure mock
        self.mock_monitor.last_check_result = "Test result"
        self.mock_monitor.last_check_time = "Test time"
        self.mock_monitor.get_history.return_value = [("time", "status", "msg")]
        
        # Call method
        status = self.service.get_status()
        
        # Verify results
        self.assertIn('is_active', status)
        self.assertIn('last_result', status)
        self.assertIn('last_check_time', status)
        self.assertIn('history', status)
        self.assertEqual(status['last_result'], "Test result")

if __name__ == '__main__':
    unittest.main()
