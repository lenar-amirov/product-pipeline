#!/bin/bash
# Sets up Telegram reminders cron job for PM pipeline
# Run once per user on the server: bash ~/pipeline/tools/scripts/remind-setup.sh

SCRIPT="$HOME/pipeline/tools/scripts/remind.py"
LOG_DIR="$HOME/pipeline/logs"
CONFIG="$HOME/pipeline/config/telegram.json"

mkdir -p "$LOG_DIR"

# Check config exists
if [ ! -f "$CONFIG" ]; then
  echo "⚠️  Config not found: $CONFIG"
  echo "   Copy the sample and fill in your values:"
  echo "   cp ~/pipeline/config/telegram-sample.json ~/pipeline/config/telegram.json"
  echo "   nano ~/pipeline/config/telegram.json"
  exit 1
fi

# Add cron: run at 10:00 and 16:00 every day
CRON_LINE="0 10,16 * * * /usr/bin/python3 $SCRIPT >> $LOG_DIR/remind.log 2>&1"

# Remove old entry if exists, then add fresh
(crontab -l 2>/dev/null | grep -v "remind.py"; echo "$CRON_LINE") | crontab -

echo "✓ Cron set up: reminders at 10:00 and 16:00 daily"
echo "  Log: $LOG_DIR/remind.log"
echo ""
echo "Test run:"
echo "  python3 $SCRIPT"
