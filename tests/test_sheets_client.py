"""
Tests for the Google Sheets client module
"""
import unittest
from unittest.mock import patch, MagicMock
from app.sheets_client import SheetsClient

class TestSheetsClient(unittest.TestCase):
    """Test suite for SheetsClient class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api_key': 'test_api_key',
            'spreadsheet_id': 'test_spreadsheet_id',
            'range_name': 'test_range'
        }
        self.client = SheetsClient(self.config)
    
    @patch('app.sheets_client.build')
    def test_get_service(self, mock_build):
        """Test that get_service returns a service object"""
        # Configure the mock
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call the method
        service = self.client.get_service()
        
        # Verify the results
        self.assertEqual(service, mock_service)
        mock_build.assert_called_once_with(
            'sheets', 'v4', developerKey=self.config['api_key']
        )
    
    @patch('app.sheets_client.SheetsClient.get_service')
    def test_get_cell_value(self, mock_get_service):
        """Test get_cell_value method"""
        # Configure the mock
        mock_service = MagicMock()
        mock_sheets = MagicMock()
        mock_values = MagicMock()
        mock_get = MagicMock()
        
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets.return_value = mock_sheets
        mock_sheets.values.return_value = mock_values
        mock_values.get.return_value = mock_get
        
        # Configure mock response
        mock_get.execute.return_value = {
            'values': [['DEPARTED']]
        }
        
        # Call the method
        result = self.client.get_cell_value()
        
        # Verify the results
        self.assertIn('value', result)
        self.assertIn('is_new', result)
        self.assertIn('timestamp', result)
        self.assertEqual(result['value'], 'DEPARTED')
        self.assertTrue(result['is_new'])
        
        # Check that subsequent calls with same value are marked as not new
        mock_get.execute.return_value = {
            'values': [['DEPARTED']]
        }
        result = self.client.get_cell_value()
        self.assertEqual(result['value'], 'DEPARTED')
        self.assertFalse(result['is_new'])
    
    @patch('app.sheets_client.SheetsClient.get_service')
    def test_get_cell_value_error(self, mock_get_service):
        """Test error handling in get_cell_value"""
        # Configure the mock to raise an exception
        mock_get_service.side_effect = Exception("Test error")
        
        # Call the method
        result = self.client.get_cell_value()
        
        # Verify the results
        self.assertIn('error', result)
        self.assertEqual(result['value'], '')
        self.assertFalse(result['is_new'])

if __name__ == '__main__':
    unittest.main()
