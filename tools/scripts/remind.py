#!/usr/bin/env python3
"""
Telegram reminder script for PM pipeline.
Reads output/status.json from all initiatives, sends reminders when needed.
Run via cron: 0 10,16 * * * python3 ~/pipeline/tools/scripts/remind.py
"""

import json
import os
import glob
from datetime import date
import urllib.request
import urllib.error

BASE_DIR = os.path.expanduser("~/pipeline")
CONFIG_FILE = f"{BASE_DIR}/config/telegram.json"
LOG_FILE = f"{BASE_DIR}/logs/remind.log"

STAGES = {
    "jira_needed": {
        "emoji": "📋",
        "title": "Создай задачи в Jira",
        "body": "Тикеты готовы в <code>output/jira-tickets.md</code>. Создай их в Jira.",
        "hint": "Когда создашь → открой Claude Code и напиши <b>/confirm-jira</b>",
        "remind_after_days": 1,
        "repeat_every_days": 1,
    },
    "grooming_needed": {
        "emoji": "🗓",
        "title": "Запишись на грумминг к аналитикам",
        "body": "Задачи в Jira есть — пора разобрать их с аналитиком.",
        "hint": "Когда грумминг пройдёт → открой Claude Code и напиши <b>/confirm-grooming</b>",
        "remind_after_days": 2,
        "repeat_every_days": 2,
    },
    "results_needed": {
        "emoji": "📊",
        "title": "Внеси результаты грумминга",
        "body": "Грумминг прошёл, но результаты ещё не зафиксированы.",
        "hint": "Открой Claude Code и напиши <b>/confirm-grooming</b>",
        "remind_after_days": 1,
        "repeat_every_days": 1,
    },
}


def send_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except urllib.error.URLError as e:
        print(f"  Telegram error: {e}")
        return False


def log(msg: str):
    timestamp = date.today().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def main():
    if not os.path.exists(CONFIG_FILE):
        log(f"Config not found: {CONFIG_FILE}")
        return

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    bot_token = config.get("bot_token", "")
    pms = config.get("pms", {})

    if not bot_token or bot_token == "YOUR_BOT_TOKEN_FROM_BOTFATHER":
        log("Bot token not configured")
        return

    today = date.today()
    sent = 0

    for status_file in glob.glob(f"{BASE_DIR}/*/*/output/status.json"):
        try:
            with open(status_file) as f:
                status = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        stage = status.get("stage", "in_progress")
        if stage not in STAGES:
            continue

        pm = status.get("pm", "")
        initiative = status.get("initiative", os.path.basename(
            os.path.dirname(os.path.dirname(status_file))
        ))
        updated_str = status.get("updated", str(today))

        try:
            updated = date.fromisoformat(updated_str)
        except ValueError:
            updated = today

        days_in_stage = (today - updated).days
        stage_info = STAGES[stage]

        if days_in_stage < stage_info["remind_after_days"]:
            continue

        # Repeat every N days after initial reminder
        excess = days_in_stage - stage_info["remind_after_days"]
        if excess > 0 and excess % stage_info["repeat_every_days"] != 0:
            continue

        chat_id = pms.get(pm)
        if not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID":
            log(f"  No chat_id for PM '{pm}', skipping {initiative}")
            continue

        text = (
            f"{stage_info['emoji']} <b>{initiative}</b>\n\n"
            f"<b>{stage_info['title']}</b>\n"
            f"{stage_info['body']}\n\n"
            f"💡 {stage_info['hint']}"
        )

        if send_telegram(bot_token, chat_id, text):
            log(f"Sent to {pm}: {initiative} ({stage}, day {days_in_stage})")
            sent += 1

    log(f"Done. Sent {sent} reminder(s).")


if __name__ == "__main__":
    main()
