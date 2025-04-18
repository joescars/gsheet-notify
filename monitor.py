#!/usr/bin/env python3
"""
Google Spreadsheet Cell Monitor - Checks cell for keyword and sends notification
This script monitors a specific cell in a Google Spreadsheet for the word 'Departed'.
When the word is detected, it sends a push notification using ntfy.sh API.
Includes HTTP endpoints and web interface to start and stop polling
"""
import os
import sys
import time
import threading
import schedule
from flask import Flask, request, jsonify, render_template, render_template_string, redirect, url_for
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
# Removed unused imports for OAuth flow

# The ID of the spreadsheet
SPREADSHEET_ID = '1sKIxt7K583QofrB3yOiDo-7--CUp0wxAOg2vMIWZHwA' #school sheet
#SPREADSHEET_ID = '1p4LyleLPwSBTyKfNirlpo5F2bbe6kYI_VWkfFrWoFiw' #test sheet

# The range to check (D19)
RANGE_NAME = 'PM!D19:E19'

# Store API key in a variable
API_KEY = None  # Replace with your actual API key or set below

def get_service():
    """Get and return the Google Sheets API service using API key."""
    global API_KEY
    
    # If API_KEY is not set in code, check for environment variable
    if API_KEY is None:
        API_KEY = os.environ.get('GOOGLE_API_KEY')
        if API_KEY is None:
            # If not found in environment, prompt user to enter it
            if os.path.exists('api_key.txt'):
                with open('api_key.txt', 'r') as f:
                    API_KEY = f.read().strip()
            else:
                print("No API key found. Please set API_KEY in the script or create an api_key.txt file")
                sys.exit(1)
    
    # Build the service with the API key
    service = build('sheets', 'v4', developerKey=API_KEY)
    return service

def check_cell():
    """Check the cell D19 in the spreadsheet for the word 'Departed'."""
    global last_check_result
    global last_cell_value
    
    try:
        service = get_service()
        sheet = service.spreadsheets()
        
        # Call the Sheets API to get the cell value
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                   range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            message = 'No data found in cell D19.'
            print(message)
            last_check_result = message
            return False

        # Check if the cell contains 'Departed'
        cell_value = values[0][0] if values and values[0] else ''
        cell_value = str(cell_value).upper()  # Convert to string and uppercase for comparison
        
        # Check if the cell value has changed since the last check
        if 'last_cell_value' in globals() and last_cell_value == cell_value:
            message = f"No Change; Current value: '{cell_value}'"
            print(message)
            last_check_result = message
            return False

        last_cell_value = cell_value  # Store the last cell value for reference

        if 'DEPARTED' in cell_value and 'NOT' not in cell_value:
            current_time = time.strftime("%H:%M", time.localtime())
            message = f"*** {cell_value} at {current_time} ***"
            print(message)
            last_check_result = message
            send_notification()
            return True
        else:
            message = f"Current Status: '{cell_value}'"
            print(message)
            last_check_result = message
            return False
    except Exception as e:
        error_msg = f"Error checking spreadsheet: {str(e)}"
        print(error_msg)
        last_check_result = error_msg
        return False

def send_notification():
    """
    Sends a push notification using ntfy.sh API when cell D19 contains the word 'Departed'.
    """
    import requests

    try:
        # Get the notification message from the last check result
        message = last_check_result
        
        # Send notification to ntfy.sh
        response = requests.post(
            'https://ntfy.sh/joetest333',  # You can change this topic name
            data=message.encode('utf-8'),
            headers={
                'Title': 'Bus Status Alert',
                'Priority': 'high',
                'Tags': 'bus,alert'
            }
        )
        
        if response.status_code == 200:
            print(f"Notification sent successfully: {message}")
        else:
            print(f"Failed to send notification. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {str(e)}")

# Initialize Flask application
app = Flask(__name__)

# Global variable to track if polling is active
polling_active = False

# Thread to run the scheduler
scheduler_thread = None

# Variable to store the last check result
last_check_result = "No check performed yet"

def start_polling():
    """Start the scheduled polling of the spreadsheet."""
    global polling_active
    polling_active = True
    print("Starting polling every minute...")
    
    # Run check_cell once immediately when starting
    check_cell()
    
    # Schedule the check_cell function to run every minute
    schedule.every(10).seconds.do(check_cell)
    
    # Run the scheduler in a loop as long as polling is active
    while polling_active:
        schedule.run_pending()
        time.sleep(1)
    
    print("Polling stopped.")
    # Clear all scheduled jobs when polling stops
    schedule.clear()

@app.route('/')
def index():
    """Main page with user interface."""
    return render_template(
        'index.html', 
        is_active=polling_active,
        result=last_check_result
    )

@app.route('/start', methods=['GET', 'POST'])
def start_polling_endpoint():
    """Endpoint to start polling the spreadsheet."""
    global polling_active, scheduler_thread
    
    if polling_active:
        if request.method == 'POST':
            return redirect('/')
        else:
            return jsonify({"status": "already_running", "message": "Polling is already active"})
    
    # Start polling in a separate thread to not block the server
    scheduler_thread = threading.Thread(target=start_polling)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    if request.method == 'POST':
        return redirect('/')
    else:
        return jsonify({"status": "started", "message": "Started polling spreadsheet every minute"})

@app.route('/stop', methods=['GET', 'POST'])
def stop_polling_endpoint():
    """Endpoint to stop polling the spreadsheet."""
    global polling_active, scheduler_thread
    
    if not polling_active:
        if request.method == 'POST':
            return redirect('/')
        else:
            return jsonify({"status": "not_running", "message": "Polling is not active"})
    
    # Set polling_active to False to stop the polling loop
    polling_active = False
    
    # Wait for the thread to finish
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=5)
    
    if request.method == 'POST':
        return redirect('/')
    else:
        return jsonify({"status": "stopped", "message": "Stopped polling spreadsheet"})

@app.route('/status', methods=['GET'])
def status_endpoint():
    """Endpoint to check the status of the polling."""
    global polling_active
    
    if request.headers.get('Accept') == 'application/json':
        status = "active" if polling_active else "inactive"
        return jsonify({
            "status": status, 
            "message": f"Polling is currently {status}",
            "last_result": last_check_result
        })
    else:
        return redirect('/')

@app.route('/check_now', methods=['POST'])
def check_now():
    """Endpoint to manually trigger a check."""
    check_cell()
    return redirect('/')

def main():
    """Main function to run the HTTP server."""
    print("Starting Google Spreadsheet Monitor server...")
    print("Access the web interface at http://<raspberry_pi_ip>:5000/")
    print("API Endpoints:")
    print("  - http://<raspberry_pi_ip>:5000/start - Begin polling")
    print("  - http://<raspberry_pi_ip>:5000/stop - Stop polling")
    print("  - http://<raspberry_pi_ip>:5000/status - Check polling status")
    
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # Run the Flask application on all interfaces so it's accessible from the local network
    # Setting threaded=True improves handling of concurrent requests on the Raspberry Pi
    app.run(host='0.0.0.0', port=5588, debug=False, threaded=True)

if __name__ == "__main__":
    main()
