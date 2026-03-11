#!/usr/bin/env python3
"""PM Pipeline Web Dashboard — Flask app on port 5000."""

import json
import os
import subprocess
from datetime import date, datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)

PENDING_LABELS = {
    "analytics_brief":   ("📊", "Передай бриф аналитику"),
    "survey_brief":      ("📝", "Передай бриф на опрос"),
    "audience_brief":    ("👥", "Передай бриф на выгрузку аудитории"),
    "analytics_results": ("📈", "Запроси результаты у аналитика"),
    "survey_results":    ("📋", "Запроси результаты опроса"),
    "design_brief":      ("🎨", "Передай бриф дизайнеру"),
    "gate1_challenge":   ("🎯", "Иди на Challenge Gate 1"),
    "gate2_challenge":   ("🏁", "Иди на Challenge Gate 2"),
}

PIPELINE_FILES = [
    ("Анализ CJM",          "output/hypotheses.md"),
    ("Синтетика",           "research/synthetic-interviews.md"),
    ("Конкуренты",          "research/competitive-analysis.md"),
    ("Брифы аналитику",     "research/analytics-brief.md"),
    ("Аудитория",           "research/survey-audience-brief.md"),
    ("Валидация гипотез",   "output/validated-hypotheses.md"),
    ("Гипотезы решений",    "output/solution-hypotheses.md"),
    ("Образ решения",       "output/solution-sketch.md"),
    ("Презентация Gate 1",  "output/presentation.md"),
    ("Бриф дизайнеру",      "output/design-brief.md"),
    ("Оценка разработки",   "output/dev-estimate.md"),
    ("AB-тест",             "output/ab-test-design.md"),
    ("Презентация Gate 2",  "output/gate2-presentation.md"),
]

USERS = ["lenar", "slava", "olya", "zhanna", "sergey"]


def get_pm(req):
    """Read PM name from X-PM-User header (set by nginx)."""
    return req.headers.get("X-PM-User", "")


def days_pending(date_str):
    """Return number of days since date_str (YYYY-MM-DD). 0 if future or today."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        delta = (date.today() - d).days
        return max(delta, 0)
    except (ValueError, TypeError):
        return 0


def get_initiative_data(pm, base_path):
    """
    Read status.json from base_path, compute pending items with days,
    compute steps_done count.

    Returns dict:
        {
            "name": str,
            "pm": str,
            "pending": [{"key": str, "emoji": str, "label": str, "days": int}],
            "steps_done": int,
            "steps": [{"label": str, "done": bool}],
            "path": str,
        }
    or None if unreadable.
    """
    status_path = os.path.join(base_path, "output", "status.json")
    try:
        with open(status_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    initiative_name = os.path.basename(base_path)
    raw_pending = data.get("pending", {})

    pending_items = []
    for key, value in raw_pending.items():
        if value is not None and key in PENDING_LABELS:
            emoji, label = PENDING_LABELS[key]
            pending_items.append({
                "key": key,
                "emoji": emoji,
                "label": label,
                "days": days_pending(value),
            })

    steps = []
    steps_done = 0
    for label, rel_path in PIPELINE_FILES:
        full_path = os.path.join(base_path, rel_path)
        done = os.path.isfile(full_path) and os.path.getsize(full_path) > 0
        if done:
            steps_done += 1
        steps.append({"label": label, "done": done})

    return {
        "name": initiative_name,
        "pm": pm,
        "pending": pending_items,
        "steps_done": steps_done,
        "steps": steps,
        "path": base_path,
    }


def list_initiatives(pm):
    """Return list of initiative data dicts for the given pm."""
    pipeline_dir = f"/home/{pm}/pipeline"
    initiatives = []
    try:
        entries = sorted(os.listdir(pipeline_dir))
    except FileNotFoundError:
        return []

    for entry in entries:
        full = os.path.join(pipeline_dir, entry)
        status_json = os.path.join(full, "output", "status.json")
        if os.path.isdir(full) and os.path.isfile(status_json):
            data = get_initiative_data(pm, full)
            if data:
                initiatives.append(data)
    return initiatives


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/<pm>/")
def dashboard(pm):
    if get_pm(request) != pm:
        abort(403)
    initiatives = list_initiatives(pm)
    return render_template("dashboard.html", pm=pm, initiatives=initiatives,
                           total_steps=len(PIPELINE_FILES))


@app.route("/<pm>/initiative/<name>")
def initiative_detail(pm, name):
    if get_pm(request) != pm:
        abort(403)
    base_path = f"/home/{pm}/pipeline/{name}"
    if not os.path.isdir(base_path):
        abort(404)
    data = get_initiative_data(pm, base_path)
    return render_template("initiative.html", pm=pm, initiative=data,
                           total_steps=len(PIPELINE_FILES))


@app.route("/<pm>/open/<name>", methods=["POST"])
def open_initiative(pm, name):
    if get_pm(request) != pm:
        abort(403)
    initiative_path = f"/home/{pm}/pipeline/{name}"
    state_file = f"/tmp/pm-session-{pm}"
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            f.write(initiative_path)
    except OSError as e:
        return {"ok": False, "error": str(e)}, 500
    return {"ok": True}


@app.route("/<pm>/new", methods=["GET"])
def new_initiative_form(pm):
    if get_pm(request) != pm:
        abort(403)
    return render_template("new.html", pm=pm, error=None)


@app.route("/<pm>/new", methods=["POST"])
def new_initiative_submit(pm):
    if get_pm(request) != pm:
        abort(403)

    name = request.form.get("name", "").strip()

    # Basic validation
    import re
    if not name:
        return render_template("new.html", pm=pm, error="Введите название инициативы.")
    if not re.match(r'^[a-z0-9-]+$', name):
        return render_template("new.html", pm=pm,
                               error="Только строчные латинские буквы и дефисы.")

    script = f"/home/{pm}/pipeline/tools/scripts/new-initiative.sh"
    cmd = f'su - {pm} -c "bash {script} {pm} {name}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            err = result.stderr.strip() or result.stdout.strip() or "Неизвестная ошибка"
            return render_template("new.html", pm=pm, error=err)
    except subprocess.TimeoutExpired:
        return render_template("new.html", pm=pm, error="Скрипт завис (timeout 30s).")

    # Write state file so terminal opens in the new initiative
    state_file = f"/tmp/pm-session-{pm}"
    initiative_path = f"/home/{pm}/pipeline/{name}"
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            f.write(initiative_path)
    except OSError:
        pass  # non-fatal

    return redirect(url_for("initiative_detail", pm=pm, name=name))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
