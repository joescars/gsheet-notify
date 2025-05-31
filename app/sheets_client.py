"""
Google Sheets API client for the Google Spreadsheet Monitor
Handles interactions with the Google Sheets API.
"""
import logging
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class SheetsClient:
    """Client for interacting with Google Sheets API"""
    
    def __init__(self, config):
        """
        Initialize the Google Sheets client.
        
        Args:
            config (dict): Configuration dictionary containing api_key, spreadsheet_id, and range_name
        """
        self.config = config
        self.service = None
        self.last_cell_value = None
    
    def get_service(self):
        """Get and return the Google Sheets API service using API key."""
        if not self.service:
            try:
                self.service = build('sheets', 'v4', developerKey=self.config['api_key'])
                logger.info("Successfully connected to Google Sheets API")
            except Exception as e:
                logger.error(f"Failed to build Google Sheets service: {str(e)}")
                raise
        return self.service
    
    def get_cell_value(self):
        """
        Fetch the value of the specified cell from the Google Sheet.
        
        Returns:
            dict: A dictionary containing:
                - value: The value of the cell (str)
                - is_new: Whether the value is different from the last check (bool)
                - timestamp: When the check was performed (str)
        """
        try:
            service = self.get_service()
            sheet = service.spreadsheets()
            
            # Call the Sheets API to get the cell value
            result = sheet.values().get(
                spreadsheetId=self.config['spreadsheet_id'],
                range=self.config['range_name']
            ).execute()
            
            values = result.get('values', [])
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            if not values:
                return {
                    'value': '',
                    'is_new': False,
                    'timestamp': timestamp,
                    'error': 'No data found in cell'
                }

            # Extract the cell value
            cell_value = values[0][0] if values and values[0] else ''
            cell_value = str(cell_value).upper()  # Convert to string and uppercase for comparison
            
            # Check if the cell value has changed since the last check
            is_new = self.last_cell_value != cell_value
            
            # Store the current value for future reference
            self.last_cell_value = cell_value
            
            return {
                'value': cell_value,
                'is_new': is_new,
                'timestamp': timestamp
            }
            
        except HttpError as error:
            logger.error(f"HTTP error while fetching cell value: {error}")
            return {
                'value': '',
                'is_new': False,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                'error': f"HTTP error: {str(error)}"
            }
        except Exception as error:
            logger.error(f"Error fetching cell value: {error}")
            return {
                'value': '',
                'is_new': False,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                'error': f"Error: {str(error)}"
            }

    def get_cell_value_with_retry(self, max_retries=3, retry_delay=5):
        """
        Fetch cell value with retry logic for handling temporary failures.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
            
        Returns:
            dict: Cell value information (see get_cell_value)
        """
        retries = 0
        while retries < max_retries:
            try:
                return self.get_cell_value()
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    logger.warning(f"Retry {retries}/{max_retries} after error: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed after {max_retries} retries: {str(e)}")
                    return {
                        'value': '',
                        'is_new': False,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                        'error': f"Failed after {max_retries} retries: {str(e)}"
                    }
