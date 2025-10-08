#!/usr/bin/env bash
# Install or update the gsheet-monitor systemd service
# This script encapsulates the steps from the README.
# Usage:
#   ./scripts/install_service.sh [-u USER] [-d APP_DIR] [-p PYTHON] [-s SERVICE_NAME]
# Defaults:
#   USER: current user
#   APP_DIR: $HOME/gsheet-notifier-copilot
#   PYTHON: python3
#   SERVICE_NAME: gsheet-monitor
#
# The script will:
# 1. Create the application directory (if not existing)
# 2. Set up a Python virtual environment
# 3. Install requirements
# 4. Create/overwrite the systemd service file
# 5. Reload systemd and enable + (re)start the service
#
# Requires: systemd, bash, python3-venv
set -euo pipefail

USER_NAME="$(whoami)"
APP_DIR="$HOME/services/gsheet-notify"
PYTHON_BIN="python3"
SERVICE_NAME="gsheet-monitor"
FORCE=0

while getopts ":u:d:p:s:f" opt; do
  case $opt in
    u) USER_NAME="$OPTARG" ;;
    d) APP_DIR="$OPTARG" ;;
    p) PYTHON_BIN="$OPTARG" ;;
    s) SERVICE_NAME="$OPTARG" ;;
    f) FORCE=1 ;;
    :) echo "Option -$OPTARG requires an argument" >&2; exit 1 ;;
    \?) echo "Unknown option: -$OPTARG" >&2; exit 1 ;;
  esac
done

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="$APP_DIR/venv"
RUN_FILE="$APP_DIR/run.py"

# if [[ ! -f "$RUN_FILE" ]]; then
#   echo "[INFO] run.py not found in $APP_DIR. Copying project files..." >&2
#   mkdir -p "$APP_DIR"
#   # If script is run from inside repo, copy everything (except common junk)
#   SRC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
#   rsync -av --exclude '.git' --exclude '__pycache__' --exclude 'logs/*' "$SRC_ROOT/" "$APP_DIR/"
# fi

# if [[ ! -d "$VENV_DIR" ]]; then
#   echo "[INFO] Creating virtual environment at $VENV_DIR"
#   "$PYTHON_BIN" -m venv "$VENV_DIR"
# fi

# # shellcheck source=/dev/null
# source "$VENV_DIR/bin/activate"

# if [[ -f "$APP_DIR/requirements.txt" ]]; then
#   echo "[INFO] Installing dependencies"
#   pip install --upgrade pip
#   pip install -r "$APP_DIR/requirements.txt"
# else
#   echo "[WARN] requirements.txt not found at $APP_DIR" >&2
# fi

echo "[INFO] Writing systemd service file: $SERVICE_FILE"
SERVICE_CONTENT="[Unit]\nDescription=Google Spreadsheet Monitor Service\nAfter=network.target\n\n[Service]\nUser=${USER_NAME}\nWorkingDirectory=${APP_DIR}\nExecStart=${VENV_DIR}/bin/python ${RUN_FILE}\nRestart=on-failure\nRestartSec=5\nEnvironment=PYTHONUNBUFFERED=1\n\n[Install]\nWantedBy=multi-user.target\n"

TMP_SERVICE_FILE="/tmp/${SERVICE_NAME}.service.$$"
echo -e "$SERVICE_CONTENT" > "$TMP_SERVICE_FILE"

mv "$TMP_SERVICE_FILE" "$SERVICE_FILE"

if [[ $EUID -ne 0 ]]; then
  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}.service"
  sudo systemctl restart "${SERVICE_NAME}.service"
  sudo systemctl status --no-pager "${SERVICE_NAME}.service" || true
else
  systemctl daemon-reload
  systemctl enable "${SERVICE_NAME}.service"
  systemctl restart "${SERVICE_NAME}.service"
  systemctl status --no-pager "${SERVICE_NAME}.service" || true
fi

echo "[SUCCESS] Service ${SERVICE_NAME} installed and started."
