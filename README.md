# Google Spreadsheet Cell Monitor

This application monitors a specific cell (D19) in a Google Spreadsheet for the word "Departed" and sends notifications when detected. It provides a web interface to start/stop monitoring, check status, and view the history of cell values.

## Features

- **Real-time Monitoring**: Checks a specific cell in a Google Spreadsheet at configurable intervals
- **Notifications**: Sends push notifications via ntfy.sh when "Departed" is detected
- **Web Interface**: User-friendly web UI to control monitoring and view status
- **History Tracking**: Maintains a log of all status changes
- **Configurable**: Settings can be changed via config file or environment variables
- **Modular Design**: Well-organized codebase for easy maintenance and extension

## Prerequisites

- Raspberry Pi (any model with network connectivity) or any computer with Python
- Raspberry Pi OS or other compatible OS installed and configured
- Internet connection
- Google Cloud Platform account with API key for Google Sheets API
- Python 3.6 or higher

## Installation Instructions

### 1. Set up your Raspberry Pi

Ensure your Raspberry Pi is set up with Raspberry Pi OS and connected to the internet. You can access it either directly with a monitor/keyboard or via SSH.

### 2. Install Required Software

SSH into your Raspberry Pi or open a terminal and run:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git
```

### 3. Clone or Copy the Application

Option 1: Clone from Git (if you have a repository):

```bash
git clone [your-repository-url]
cd gsheet-notifier-copilot
```

Option 2: Create a project directory and copy files manually:

```bash
mkdir -p ~/gsheet-notifier-copilot
cd ~/gsheet-notifier-copilot
# Now copy all project files to this directory
```

### 4. Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Get Google Sheets API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API for your project
4. Create an API key:
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API key"
5. Save your API key in a file named `api_key.txt` in the project directory:

   ```bash
   echo "YOUR_API_KEY" > api_key.txt
   ```

### 6. Configure the Application

Create or edit `config.yaml` to adjust settings:

```yaml
# Google Spreadsheet Monitor Configuration
spreadsheet_id: "YOUR_SPREADSHEET_ID"
range_name: "SHEET_NAME!CELL_RANGE"
polling_interval: 30
notification_topic: "your-ntfy-topic"
port: 5588
```

You can also use environment variables to override these settings:
- `GOOGLE_API_KEY`: Your Google Sheets API key
- `SPREADSHEET_ID`: ID of the spreadsheet to monitor
- `RANGE_NAME`: Cell range to check
- `POLLING_INTERVAL`: Check frequency in seconds
- `NOTIFICATION_TOPIC`: Topic name for ntfy.sh notifications
- `PORT`: Web interface port number

## Running the Application

### Manual Start

To start the application manually:

```bash
cd ~/gsheet-notifier-copilot
source venv/bin/activate
python run.py
```

The web interface will be available at `http://<raspberry_pi_ip>:5588/`

### Setting Up as a Service (for automatic startup)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/gsheet-monitor.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Google Spreadsheet Monitor Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/gsheet-notifier-copilot
ExecStart=/home/pi/gsheet-notifier-copilot/venv/bin/python /home/pi/gsheet-notifier-copilot/run.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gsheet-monitor.service
sudo systemctl start gsheet-monitor.service
```

Check the status:

```bash
sudo systemctl status gsheet-monitor.service
```

## Project Structure

The project follows a modular structure:

```
gsheet-notifier-copilot/
├── app/                   # Application package
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── sheets_client.py   # Google Sheets API interactions
│   ├── notifier.py        # Notification services
│   ├── monitor.py         # Core monitoring logic
│   └── web/               # Web interface
│       ├── __init__.py
│       ├── app.py         # Flask app creation
│       └── routes.py      # API endpoints
├── logs/                  # Log files
├── static/                # Static web assets
├── templates/             # HTML templates
│   ├── index.html         # Main interface
│   └── history.html       # History page
├── tests/                 # Unit tests
├── config.yaml            # Configuration file
├── run.py                 # Entry point
└── requirements.txt       # Dependencies
```

## Usage

1. Access the web interface by navigating to `http://<raspberry_pi_ip>:5588/` in your browser
2. Use the interface to:
   - Start monitoring
   - Stop monitoring
   - Check current status
   - Manually trigger a check
   - View status history

## API Endpoints

- `http://<raspberry_pi_ip>:5588/start` - Begin monitoring
- `http://<raspberry_pi_ip>:5588/stop` - Stop monitoring
- `http://<raspberry_pi_ip>:5588/status` - Check monitoring status
- `http://<raspberry_pi_ip>:5588/check_now` - Manually trigger a check
- `http://<raspberry_pi_ip>:5588/history` - View status history

## Extending the Application

### Adding New Notification Methods

To add a new notification method, extend the `BaseNotifier` class in `app/notifier.py`:

```python
class EmailNotifier(BaseNotifier):
    def send(self, message, **kwargs):
        # Email sending logic here
        return True  # Return success/failure
```

Then add your notifier to the `NotificationManager`:

```python
# In app/monitor.py
notification_manager = NotificationManager(config)
notification_manager.add_notifier(EmailNotifier(config))
```

### Running Tests

```bash
python -m pytest tests/
```

To generate a coverage report:

```bash
python -m pytest --cov=app tests/
```

## Troubleshooting

1. **Cannot access web interface:**
   - Ensure the service is running: `sudo systemctl status gsheet-monitor.service`
   - Check that you're using the correct IP address and port
   - Verify no firewall is blocking port 5588

2. **API key errors:**
   - Verify your API key is correctly stored in `api_key.txt` or set as an environment variable
   - Check that the Google Sheets API is enabled for your project
   - Ensure the API key has access to the Google Sheets API

3. **Application crashes:**
   - Check the logs in the `logs/` directory or using: `sudo journalctl -u gsheet-monitor.service`
   - Ensure all required Python packages are installed

## License

[Your license information here]
