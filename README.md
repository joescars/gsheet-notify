# Google Spreadsheet Cell Monitor

This application monitors a specific cell (D19) in a Google Spreadsheet for the word "Departed" and can send notifications when detected. It provides a web interface to start/stop monitoring and check status.

## Prerequisites

- Raspberry Pi (any model with network connectivity)
- Raspberry Pi OS installed and configured
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

If needed, edit `monitor.py` to:
- Change the `SPREADSHEET_ID` to your Google spreadsheet's ID
- Modify `RANGE_NAME` if you want to monitor a different cell
- Update the port (default is 5588) if needed

## Running the Application

### Manual Start

To start the application manually:

```bash
cd ~/gsheet-notifier-copilot
source venv/bin/activate
python monitor.py
```

The web interface will be available at `http://<raspberry_pi_ip>:5588/`

### Setting Up as a Service (for automatic startup)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/gsheet-monitor.service
```

Add the following content (adjust paths as needed):

```
[Unit]
Description=Google Spreadsheet Monitor Service
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/gsheet-notifier-copilot
ExecStart=/home/pi/gsheet-notifier-copilot/venv/bin/python /home/pi/gsheet-notifier-copilot/monitor.py
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

## Usage

1. Access the web interface by navigating to `http://<raspberry_pi_ip>:5588/` in your browser
2. Use the interface to:
   - Start monitoring
   - Stop monitoring
   - Check current status
   - Manually trigger a check

## API Endpoints

- `http://<raspberry_pi_ip>:5588/start` - Begin polling
- `http://<raspberry_pi_ip>:5588/stop` - Stop polling
- `http://<raspberry_pi_ip>:5588/status` - Check polling status
- `http://<raspberry_pi_ip>:5588/check_now` - Manually trigger a check

## Customizing Notifications

To implement notifications when "Departed" is detected, edit the `send_notification()` function in `monitor.py`. You could add:

- Email notifications
- SMS alerts
- Push notifications
- Sounds/visual alerts on the Pi
- Integration with other services like IFTTT

## Troubleshooting

1. **Cannot access web interface:**
   - Ensure the service is running: `sudo systemctl status gsheet-monitor.service`
   - Check that you're using the correct IP address and port
   - Verify no firewall is blocking port 5588

2. **API key errors:**
   - Verify your API key is correctly stored in `api_key.txt`
   - Check that the Google Sheets API is enabled for your project
   - Ensure the API key has access to the Google Sheets API

3. **Application crashes:**
   - Check the logs: `sudo journalctl -u gsheet-monitor.service`
   - Ensure all required Python packages are installed

## License

[Your license information here]
