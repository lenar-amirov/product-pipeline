#!/bin/bash
# Deploys the PM pipeline Telegram bot as a systemd service.
# Run once on the server as root: bash ~/pipeline/tools/scripts/setup-bot.sh

SCRIPT="/home/lenar/pipeline/tools/scripts/bot.py"
CONFIG="/home/lenar/pipeline/config/telegram.json"
LOG_DIR="/home/lenar/pipeline/logs"
SERVICE="pm-bot"

# Check config exists
if [ ! -f "$CONFIG" ]; then
  echo "⚠️  Config not found: $CONFIG"
  exit 1
fi

mkdir -p "$LOG_DIR"

# Write systemd unit
cat > /etc/systemd/system/${SERVICE}.service << EOF
[Unit]
Description=PM Pipeline Telegram Bot
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $SCRIPT
Restart=on-failure
RestartSec=10
StandardOutput=append:$LOG_DIR/bot.log
StandardError=append:$LOG_DIR/bot.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $SERVICE
systemctl restart $SERVICE

echo "✓ Bot deployed"
echo ""
systemctl status $SERVICE --no-pager
