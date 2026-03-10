#!/usr/bin/env python3
"""
Product Pipeline Dashboard — Notion-style light theme
Запуск: python3 -m streamlit run dashboard.py --server.port 8501
"""

import re
from pathlib import Path
from datetime import datetime
import streamlit as st

BASE = Path(__file__).parent

# --- Конфиг шагов ---

STEPS = [
    (1,  "analyze-cjm",           "Phase 1", "Анализ CJM"),
    (2,  "synthetic-research",     "Phase 1", "Синт. интервью"),
    (3,  "competitor-research",    "Phase 1", "Конкуренты"),
    (4,  "generate-research",      "Phase 1", "Бриф аналитику"),
    (5,  "create-survey-audience", "Phase 1", "Выборка"),
    (6,  "validate-problems",      "Phase 1", "Валидация"),
    (7,  "solution-hypotheses",    "Phase 1", "Гипотезы решений"),
    (8,  "sketch-solution",        "Phase 1", "Образ решения"),
    (9,  "review-design",          "Phase 1", "Ревью дизайна"),
    (10, "create-presentation",    "Phase 1", "Gate 1"),
    (11, "create-design-brief",    "Phase 2", "Дизайн-бриф"),
    (12, "estimate-with-dev",      "Phase 2", "Оценка"),
    (13, "finalize-prd",           "Phase 2", "PRD"),
    (14, "design-ab-test",         "Phase 2", "AB-тест"),
    (15, "create-gate2-presentation", "Phase 2", "Gate 2"),
]

ARTIFACTS = {
    "hypotheses":      ("output/hypotheses.md",              "Гипотезы проблем"),
    "synthetic":       ("research/synthetic-interviews.md",  "Синтетические интервью"),
    "competitive":     ("research/competitive-analysis.md",  "Конкурентный анализ"),
    "analytics_brief": ("research/analytics-brief.md",       "Бриф аналитику"),
    "survey":          ("research/survey-questions.md",       "Опрос"),
    "validated":       ("output/validated-hypotheses.md",     "Валидированные гипотезы"),
    "solutions":       ("output/solution-hypotheses.md",      "Гипотезы решений"),
    "sketch":          ("output/solution-sketch.md",          "Образ решения"),
    "presentation":    ("output/presentation.md",             "Презентация Gate 1"),
    "pptx":            ("output/presentation.pptx",           "Gate 1 (.pptx)"),
    "design_brief":    ("output/design-brief.md",             "Дизайн-бриф"),
    "prd":             ("output/PRD.md",                      "PRD"),
    "ab_test":         ("output/ab-test-design.md",           "Дизайн AB-теста"),
    "gate2":           ("output/gate2-presentation.md",       "Презентация Gate 2"),
}

# Маппинг шаг → артефакты (ключи из ARTIFACTS)
STEP_ARTIFACTS = {
    1:  ["hypotheses"],
    2:  ["synthetic"],
    3:  ["competitive"],
    4:  ["analytics_brief", "survey"],
    5:  [],
    6:  ["validated"],
    7:  ["solutions"],
    8:  ["sketch"],
    9:  [],
    10: ["presentation", "pptx"],
    11: ["design_brief"],
    12: [],
    13: ["prd"],
    14: ["ab_test"],
    15: ["gate2"],
}


# --- CSS: Notion-style light theme ---

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ─── Global ─── */
    #MainMenu, header, footer {visibility: hidden;}

    .stApp {
        background-color: #ffffff !important;
        font-family: 'Inter', ui-sans-serif, -apple-system, BlinkMacSystemFont, sans-serif;
        color: #37352f;
    }
    .block-container {
        padding: 2rem 4rem 2rem 4rem;
        max-width: 960px;
    }

    /* ─── Page title ─── */
    .page-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #37352f;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .page-subtitle {
        font-size: 0.82rem;
        color: #9b9a97;
        margin-bottom: 1.8rem;
    }

    /* ─── Summary counters ─── */
    .summary-row {
        display: flex;
        gap: 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid #e3e3e0;
        padding-bottom: 16px;
    }
    .summary-item {
        flex: 1;
        text-align: left;
        padding: 0 16px;
        border-right: 1px solid #e3e3e0;
    }
    .summary-item:first-child {padding-left: 0;}
    .summary-item:last-child {border-right: none;}
    .summary-num {
        font-size: 1.6rem;
        font-weight: 700;
        color: #37352f;
        line-height: 1.2;
    }
    .summary-label {
        font-size: 0.72rem;
        color: #9b9a97;
        margin-top: 2px;
    }
    .sn-blue {color: #2f80ed !important;}
    .sn-violet {color: #9065e0 !important;}
    .sn-orange {color: #d9730d !important;}
    .sn-green {color: #0f7b6c !important;}

    /* ─── PM group ─── */
    .pm-header {
        font-size: 0.72rem;
        font-weight: 600;
        color: #9b9a97;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 24px 0 8px 0;
    }

    /* ─── Initiative row ─── */
    .init-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        margin: 0 -12px;
        border-radius: 4px;
        cursor: default;
        transition: background 0.1s;
    }
    .init-row:hover {background: #f7f7f5;}
    .init-row.attention {background: #fdf4e7;}
    .init-row.attention:hover {background: #fcecd3;}

    .init-icon {
        width: 26px;
        height: 26px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .init-icon-p1 {background: #d3e5ef; color: #2f80ed;}
    .init-icon-p2 {background: #e8deee; color: #9065e0;}
    .init-icon-done {background: #dbeddb; color: #0f7b6c;}
    .init-icon-paused {background: #fadec9; color: #d9730d;}

    .init-body {flex: 1; min-width: 0;}
    .init-name {
        font-size: 0.88rem;
        font-weight: 600;
        color: #37352f;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .init-sub {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 2px;
    }
    .init-step-text {
        font-size: 0.75rem;
        color: #9b9a97;
    }

    /* ─── Notion-style tag ─── */
    .n-tag {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 0.68rem;
        font-weight: 500;
        white-space: nowrap;
    }
    .n-tag-blue {background: #d3e5ef; color: #2472a4;}
    .n-tag-violet {background: #e8deee; color: #6940a5;}
    .n-tag-green {background: #dbeddb; color: #0f7b6c;}
    .n-tag-orange {background: #fadec9; color: #cf7d2e;}

    /* ─── Mini step dots ─── */
    .mini-steps {
        display: flex;
        gap: 2px;
        align-items: center;
        flex-shrink: 0;
    }
    .mini-dot {
        width: 18px;
        height: 18px;
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.55rem;
        font-weight: 600;
    }
    .mini-dot.done   {background: #dbeddb; color: #0f7b6c;}
    .mini-dot.active {background: #d3e5ef; color: #2f80ed;}
    .mini-dot.paused {background: #fadec9; color: #d9730d;}
    .mini-dot.todo   {background: #f1f1ef; color: #c4c4c0;}
    .mini-divider {
        width: 1px;
        height: 14px;
        background: #e3e3e0;
        margin: 0 2px;
    }

    .init-date {
        font-size: 0.72rem;
        color: #c4c4c0;
        flex-shrink: 0;
        min-width: 70px;
        text-align: right;
    }

    /* ─── Overview: metric cards ─── */
    .ov-metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1px;
        background: #e3e3e0;
        border: 1px solid #e3e3e0;
        border-radius: 6px;
        overflow: hidden;
        margin: 1.2rem 0;
    }
    .ov-metric {
        background: #ffffff;
        padding: 14px 16px;
    }
    .ov-metric-label {
        font-size: 0.68rem;
        color: #9b9a97;
        margin-bottom: 4px;
    }
    .ov-metric-value {
        font-size: 0.92rem;
        font-weight: 600;
        color: #37352f;
        line-height: 1.3;
    }

    /* ─── Current step callout ─── */
    .callout {
        background: #f1f1ef;
        border-radius: 4px;
        padding: 14px 16px;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .callout-icon {
        font-size: 1.3rem;
        font-weight: 800;
        color: #2f80ed;
        flex-shrink: 0;
        width: 32px;
        text-align: center;
    }
    .callout-text {
        font-size: 0.88rem;
        color: #37352f;
    }
    .callout-sub {
        font-size: 0.75rem;
        color: #9b9a97;
        margin-top: 2px;
    }

    /* ─── Phase section ─── */
    .phase-section {margin: 1.2rem 0 0.4rem 0;}
    .phase-title {
        font-size: 0.72rem;
        font-weight: 600;
        color: #9b9a97;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }

    /* ─── Progress bar ─── */
    .progress-bar {
        background: #e3e3e0;
        border-radius: 3px;
        height: 4px;
        width: 100%;
        margin: 10px 0 4px 0;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 3px;
        background: #2f80ed;
    }
    .progress-text {
        font-size: 0.72rem;
        color: #9b9a97;
    }

    /* ─── Section divider ─── */
    .section-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #37352f;
        margin: 2rem 0 0.6rem 0;
        padding-bottom: 6px;
        border-bottom: 1px solid #e3e3e0;
    }

    /* ─── Decisions ─── */
    .dec-item {
        padding: 8px 0;
        border-bottom: 1px solid #f1f1ef;
    }
    .dec-item:last-child {border-bottom: none;}
    .dec-head {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.72rem;
        color: #9b9a97;
        margin-bottom: 2px;
    }
    .dec-body {
        font-size: 0.82rem;
        color: #37352f;
    }
    .dec-reason {
        font-size: 0.75rem;
        color: #9b9a97;
        margin-top: 2px;
    }

    /* ─── Step detail panel ─── */
    .step-detail {
        background: #f7f7f5;
        border: 1px solid #e3e3e0;
        border-radius: 6px;
        padding: 16px 18px;
        margin: 0.75rem 0;
    }
    .step-detail-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #37352f;
        margin-bottom: 4px;
    }
    .step-detail-cmd {
        font-size: 0.75rem;
        color: #9b9a97;
        font-family: 'SFMono-Regular', Consolas, monospace;
        margin-bottom: 8px;
    }
    .step-detail-status {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 0.68rem;
        font-weight: 500;
    }

    /* ─── Step button grid ─── */
    .phase-btn-row .stButton > button {
        padding: 8px 4px !important;
        min-height: 0 !important;
        font-size: 0.68rem !important;
        font-weight: 500 !important;
        line-height: 1.3 !important;
        width: 100% !important;
        white-space: normal !important;
        border-radius: 6px !important;
        height: auto !important;
    }
    .phase-btn-row .stButton > button[data-done="true"] {
        background: #dbeddb !important;
        border-color: #c3dcc3 !important;
        color: #0f7b6c !important;
    }

    /* ─── Chevron button (init list) ─── */
    .chevron-col .stButton > button {
        border: none !important;
        background: transparent !important;
        color: #c4c4c0 !important;
        font-size: 1.2rem !important;
        padding: 0 !important;
        min-height: 0 !important;
        line-height: 1 !important;
    }
    .chevron-col .stButton > button:hover {
        color: #37352f !important;
        background: transparent !important;
    }

    /* ─── Row button (invisible overlay for click) ─── */
    .row-btn-col .stButton > button {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10;
    }
    .row-btn-col {
        position: relative;
    }

    /* ─── Clickable init row ─── */
    .init-row {
        cursor: pointer;
    }

    /* ─── Streamlit widget overrides ─── */
    .stSelectbox > div > div {
        background: #ffffff !important;
        border-color: #e3e3e0 !important;
        color: #37352f !important;
        font-size: 0.82rem !important;
    }
    .stSelectbox label {color: #9b9a97 !important;}

    div[data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #e3e3e0;
        border-radius: 4px;
    }
    div[data-testid="stExpander"] summary {
        font-size: 0.82rem;
        color: #37352f;
    }

    .stButton > button {
        background: #ffffff !important;
        color: #37352f !important;
        border: 1px solid #e3e3e0 !important;
        border-radius: 4px !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        padding: 4px 12px !important;
        transition: background 0.1s !important;
    }
    .stButton > button:hover {
        background: #f7f7f5 !important;
        border-color: #d3d3d0 !important;
    }

    .stDownloadButton > button {
        background: #f7f7f5 !important;
        color: #37352f !important;
        border: 1px solid #e3e3e0 !important;
        border-radius: 4px !important;
    }

    .stAlert {
        background: #f1f1ef !important;
        border: none !important;
        border-radius: 4px !important;
        color: #37352f !important;
    }
</style>
"""


# --- Парсинг ---

def parse_context(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    info = {}

    def extract(pattern):
        m = re.search(pattern, text, re.MULTILINE)
        return m.group(1).strip() if m else "—"

    info["name"] = extract(r"^# Инициатива:\s*(.+)$")
    info["pm"] = extract(r"\*\*Продакт\*\*:\s*(.+?)$")
    info["metric"] = extract(r"\*\*Метрика, которую улучшаем\*\*:\s*(.+?)$")
    info["segment"] = extract(r"\*\*Сегмент\*\*:\s*(.+?)$")
    info["baseline"] = extract(r"\*\*Текущий baseline\*\*:\s*(.+?)$")
    info["target"] = extract(r"\*\*Целевой результат\*\*:\s*(.+?)$")

    steps_status = {}
    for line in text.split("\n"):
        m = re.match(r"\|\s*(\d+)\s*\|.*?\|\s*([✅⏸🔄⬜])\s*\|", line)
        if m:
            steps_status[int(m.group(1))] = m.group(2)
    info["steps"] = steps_status

    dates = re.findall(r"\|\s*\d+\s*\|.*?\|\s*[✅⏸🔄]\s*\|\s*([\d-]+)\s*\|", text)
    info["last_date"] = max(dates) if dates else "—"

    return info


def parse_decisions(path: Path, limit: int = 5) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    rows = []
    for line in text.split("\n"):
        m = re.match(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if m and not m.group(1).startswith(("-", "Дата")):
            date, step, decision, reason = m.groups()
            if date.strip():
                rows.append({"date": date.strip(), "step": step.strip(),
                             "decision": decision.strip(), "reason": reason.strip()})
    return rows[-limit:]


def get_current_step(steps: dict) -> tuple[int, str, str, str]:
    for num, cmd, phase, label in STEPS:
        status = steps.get(num, "⬜")
        if status in ("⬜", "⏸", "🔄"):
            return num, cmd, status, label
    return 15, "done", "✅", "Готово"


def count_done(steps: dict) -> int:
    return sum(1 for s in steps.values() if s == "✅")


def needs_attention(info: dict) -> bool:
    step_num, _, step_status, _ = get_current_step(info["steps"])
    if step_status == "⏸":
        return True
    if info["last_date"] != "—":
        try:
            last = datetime.strptime(info["last_date"], "%Y-%m-%d")
            if (datetime.now() - last).days > 14:
                return True
        except ValueError:
            pass
    return False


def scan_artifacts(path: Path) -> dict[str, bool]:
    result = {}
    for key, (rel_path, _) in ARTIFACTS.items():
        fpath = path / rel_path
        if fpath.exists():
            if fpath.suffix == ".pptx":
                result[key] = True
            else:
                content = fpath.read_text(encoding="utf-8")
                result[key] = "заполнит после" not in content.lower() and len(content.strip()) > 100
        else:
            result[key] = False
    return result


def scan_all() -> list[dict]:
    initiatives = []
    seen_paths = set()

    for pm_dir in sorted(BASE.iterdir()):
        if not pm_dir.is_dir() or pm_dir.name.startswith(("_", ".")):
            continue
        for init_dir in sorted(pm_dir.iterdir()):
            if not init_dir.is_dir():
                continue
            ctx = init_dir / "CONTEXT.md"
            if ctx.exists():
                info = parse_context(ctx)
                info["path"] = init_dir
                info["pm_folder"] = pm_dir.name
                info["folder"] = init_dir.name
                info["artifacts"] = scan_artifacts(init_dir)
                initiatives.append(info)
                seen_paths.add(init_dir)

    for init_dir in sorted(BASE.iterdir()):
        if not init_dir.is_dir() or init_dir.name.startswith(("_", ".")):
            continue
        if init_dir in seen_paths:
            continue
        ctx = init_dir / "CONTEXT.md"
        if ctx.exists():
            info = parse_context(ctx)
            info["path"] = init_dir
            info["pm_folder"] = ""
            info["folder"] = init_dir.name
            info["artifacts"] = scan_artifacts(init_dir)
            initiatives.append(info)

    return initiatives


def get_step_status_cls(num: int, steps: dict, current_num: int, current_status: str) -> str:
    """Возвращает CSS-класс статуса шага."""
    s = steps.get(num, "⬜")
    if s == "✅":
        return "done"
    if num == current_num and current_status == "⏸":
        return "paused"
    if num == current_num:
        return "active"
    return "todo"


# --- UI: Все инициативы ---

def render_all(initiatives: list[dict]):
    st.markdown('<div class="page-title">Product Pipeline</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{len(initiatives)} инициатив</div>', unsafe_allow_html=True)

    # Фильтры
    c1, c2, _ = st.columns([2, 2, 6])
    pms = sorted(set(i["pm"] for i in initiatives))
    with c1:
        pm_filter = st.selectbox("Продакт", ["Все"] + pms, label_visibility="collapsed")
    with c2:
        status_filter = st.selectbox("Статус", ["Все", "В работе", "Ждут данные", "Завершены"], label_visibility="collapsed")

    filtered = initiatives
    if pm_filter != "Все":
        filtered = [i for i in filtered if i["pm"] == pm_filter]

    # Summary
    total = len(filtered)
    phase1 = sum(1 for i in filtered if get_current_step(i["steps"])[2] != "✅"
                 and any(s[2] == "Phase 1" for s in STEPS if s[0] == get_current_step(i["steps"])[0]))
    phase2 = sum(1 for i in filtered if get_current_step(i["steps"])[2] != "✅"
                 and any(s[2] == "Phase 2" for s in STEPS if s[0] == get_current_step(i["steps"])[0]))
    paused = sum(1 for i in filtered if get_current_step(i["steps"])[2] == "⏸")
    done_count = sum(1 for i in filtered if count_done(i["steps"]) >= 15)

    st.markdown(f"""<div class="summary-row">
        <div class="summary-item">
            <div class="summary-num">{total}</div>
            <div class="summary-label">Всего</div>
        </div>
        <div class="summary-item">
            <div class="summary-num sn-blue">{phase1}</div>
            <div class="summary-label">Phase 1</div>
        </div>
        <div class="summary-item">
            <div class="summary-num sn-violet">{phase2}</div>
            <div class="summary-label">Phase 2</div>
        </div>
        <div class="summary-item">
            <div class="summary-num sn-orange">{paused}</div>
            <div class="summary-label">Ждут данные</div>
        </div>
        <div class="summary-item">
            <div class="summary-num sn-green">{done_count}</div>
            <div class="summary-label">Завершены</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Группировка по PM
    from collections import defaultdict
    by_pm = defaultdict(list)
    for i in filtered:
        pm_key = i["pm"] if i["pm"] != "—" else i.get("pm_folder", "—")
        by_pm[pm_key].append(i)

    for pm_name in sorted(by_pm.keys()):
        pm_inits = by_pm[pm_name]
        st.markdown(f'<div class="pm-header">{pm_name}</div>', unsafe_allow_html=True)

        for i in pm_inits:
            step_num, step_cmd, step_status, step_label = get_current_step(i["steps"])
            done = count_done(i["steps"])
            phase = next((s[2] for s in STEPS if s[0] == step_num), "—")

            if status_filter == "В работе" and step_status in ("⏸", "✅"):
                continue
            if status_filter == "Ждут данные" and step_status != "⏸":
                continue
            if status_filter == "Завершены" and done < 15:
                continue

            # Icon
            if done >= 15:
                icon_cls = "init-icon-done"
            elif step_status == "⏸":
                icon_cls = "init-icon-paused"
            elif phase == "Phase 1":
                icon_cls = "init-icon-p1"
            else:
                icon_cls = "init-icon-p2"

            # Tag
            if done >= 15:
                tag = '<span class="n-tag n-tag-green">Готово</span>'
            elif step_status == "⏸":
                tag = f'<span class="n-tag n-tag-orange">{step_label}</span>'
            elif phase == "Phase 1":
                tag = '<span class="n-tag n-tag-blue">Phase 1</span>'
            else:
                tag = '<span class="n-tag n-tag-violet">Phase 2</span>'

            # Mini step dots
            dots = ""
            prev_ph = None
            for num, _, ph, lbl in STEPS:
                if prev_ph and prev_ph != ph:
                    dots += '<div class="mini-divider"></div>'
                prev_ph = ph
                cls = get_step_status_cls(num, i["steps"], step_num, step_status)
                dots += f'<div class="mini-dot {cls}">{num}</div>'

            attention_cls = " attention" if needs_attention(i) else ""

            row_html = f"""<div class="init-row{attention_cls}">
                <div class="init-icon {icon_cls}">{step_num}</div>
                <div class="init-body">
                    <div class="init-name">{i['name']}</div>
                    <div class="init-sub">
                        {tag}
                        <span class="init-step-text">Шаг {step_num}: {step_label}</span>
                        <span class="init-step-text">{done}/15</span>
                    </div>
                </div>
                <div class="mini-steps">{dots}</div>
                <div class="init-date">{i['last_date']}</div>
                <div style="color:#c4c4c0; font-size:1.2rem; flex-shrink:0; padding-left:4px;">&#8250;</div>
            </div>"""

            btn_key = f"btn_{i['folder']}_{i.get('pm_folder', '')}"
            st.markdown('<div class="row-btn-col">', unsafe_allow_html=True)
            st.markdown(row_html, unsafe_allow_html=True)
            if st.button(i['name'], key=f"row_{btn_key}", use_container_width=True):
                st.session_state["selected_path"] = str(i["path"])
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# --- UI: Овервью инициативы ---

def render_phase_buttons(phase_name: str, i: dict, step_num: int, step_status: str):
    """Рендерит кликабельные кнопки-шаги для фазы."""
    phase_steps = [(n, c, l) for n, c, ph, l in STEPS if ph == phase_name]
    cols = st.columns(len(phase_steps))

    for col, (num, cmd, lbl) in zip(cols, phase_steps):
        cls = get_step_status_cls(num, i["steps"], step_num, step_status)

        # Иконка статуса + название шага
        if cls == "done":
            label = f"✓ {lbl}"
        elif cls == "active":
            label = f"→ {lbl}"
        elif cls == "paused":
            label = f"⏸ {lbl}"
        else:
            label = lbl

        with col:
            if st.button(label, key=f"step_{num}", help=f"/{cmd}", use_container_width=True):
                st.session_state["selected_step"] = num


def render_step_detail(num: int, i: dict, step_num: int, step_status: str):
    """Рендерит панель деталей выбранного шага с артефактами."""
    step_info = next((s for s in STEPS if s[0] == num), None)
    if not step_info:
        return

    _, cmd, phase, label = step_info
    cls = get_step_status_cls(num, i["steps"], step_num, step_status)
    status_labels = {"done": "Готово", "active": "В работе", "paused": "Ожидание данных", "todo": "Не начат"}
    status_colors = {"done": "#dbeddb; color: #0f7b6c", "active": "#d3e5ef; color: #2472a4",
                     "paused": "#fadec9; color: #cf7d2e", "todo": "#e3e3e0; color: #787774"}

    st.markdown(f"""<div class="step-detail">
        <div class="step-detail-title">{num}. {label}</div>
        <div class="step-detail-cmd">/{cmd}</div>
        <span class="step-detail-status" style="background:{status_colors.get(cls, '#e3e3e0; color: #787774')}">{status_labels.get(cls, '—')}</span>
    </div>""", unsafe_allow_html=True)

    # Артефакты этого шага
    art_keys = STEP_ARTIFACTS.get(num, [])
    if art_keys:
        for key in art_keys:
            if key not in ARTIFACTS:
                continue
            rel_path, art_label = ARTIFACTS[key]
            file_path = i["path"] / rel_path
            has_content = i["artifacts"].get(key, False)

            if has_content and file_path.exists():
                if file_path.suffix == ".pptx":
                    with st.expander(f"✓ {art_label}", expanded=False):
                        with open(file_path, "rb") as f:
                            st.download_button("Скачать .pptx", f, file_name=file_path.name,
                                               key=f"dl_{num}_{key}")
                else:
                    with st.expander(f"✓ {art_label}", expanded=False):
                        st.markdown(file_path.read_text(encoding="utf-8"))
            else:
                st.markdown(f'<span style="color:#c4c4c0; font-size:0.82rem">· {art_label} — не заполнен</span>',
                            unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#c4c4c0; font-size:0.82rem">Нет связанных артефактов</span>',
                    unsafe_allow_html=True)


def render_initiative(i: dict):
    if st.button("← Назад"):
        st.session_state.pop("selected_path", None)
        st.session_state.pop("selected_step", None)
        st.rerun()

    step_num, step_cmd, step_status, step_label = get_current_step(i["steps"])
    done = count_done(i["steps"])
    pct = round(done / 15 * 100)

    st.markdown(f'<div class="page-title">{i["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{i["pm"]}</div>', unsafe_allow_html=True)

    # Метрики
    st.markdown(f"""<div class="ov-metrics">
        <div class="ov-metric">
            <div class="ov-metric-label">Метрика</div>
            <div class="ov-metric-value">{i['metric']}</div>
        </div>
        <div class="ov-metric">
            <div class="ov-metric-label">Baseline</div>
            <div class="ov-metric-value">{i['baseline']}</div>
        </div>
        <div class="ov-metric">
            <div class="ov-metric-label">Target</div>
            <div class="ov-metric-value">{i['target']}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Текущий шаг — callout
    status_map = {"⬜": "Не начат", "⏸": "Ожидание данных", "🔄": "Повтор", "✅": "Завершено"}
    st.markdown(f"""<div class="callout">
        <div class="callout-icon">{step_num}</div>
        <div>
            <div class="callout-text">{step_label}</div>
            <div class="callout-sub">{status_map.get(step_status, step_status)}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Phase 1 — кликабельные шаги
    st.markdown("""<div class="phase-section">
        <div class="phase-title">Phase 1 — Исследование проблемы + Образ решения → Gate 1</div>
    </div>""", unsafe_allow_html=True)
    render_phase_buttons("Phase 1", i, step_num, step_status)

    # Phase 2 — кликабельные шаги
    st.markdown("""<div class="phase-section">
        <div class="phase-title">Phase 2 — Проработка решения → Gate 2</div>
    </div>""", unsafe_allow_html=True)
    render_phase_buttons("Phase 2", i, step_num, step_status)

    # Progress
    st.markdown(f"""<div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
        <span class="progress-text">{done}/15 шагов</span>""", unsafe_allow_html=True)

    # Детали выбранного шага
    selected_step = st.session_state.get("selected_step")
    if selected_step:
        render_step_detail(selected_step, i, step_num, step_status)

    # Сегмент
    st.markdown(f"""<div class="ov-metrics" style="grid-template-columns:1fr;">
        <div class="ov-metric">
            <div class="ov-metric-label">Сегмент</div>
            <div class="ov-metric-value" style="font-size:0.85rem">{i['segment']}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Все артефакты — схлопнутые
    st.markdown('<div class="section-title">Все артефакты</div>', unsafe_allow_html=True)
    arts = i["artifacts"]
    for key, (rel_path, label) in ARTIFACTS.items():
        file_path = i["path"] / rel_path
        has_content = arts.get(key, False)

        if has_content and file_path.exists():
            if file_path.suffix == ".pptx":
                with st.expander(f"✓ {label}", expanded=False):
                    with open(file_path, "rb") as f:
                        st.download_button("Скачать .pptx", f, file_name=file_path.name,
                                           key=f"all_dl_{key}")
            else:
                with st.expander(f"✓ {label}", expanded=False):
                    st.markdown(file_path.read_text(encoding="utf-8"))
        else:
            st.markdown(f'<span style="color:#c4c4c0; font-size:0.82rem; display:block; padding:4px 0;">· {label}</span>',
                        unsafe_allow_html=True)

    # Решения
    st.markdown('<div class="section-title">Решения</div>', unsafe_allow_html=True)
    decisions = parse_decisions(i["path"] / "output" / "decisions.md")
    if decisions:
        for d in reversed(decisions):
            st.markdown(f"""<div class="dec-item">
                <div class="dec-head"><span>{d['date']}</span><span>·</span><span>{d['step']}</span></div>
                <div class="dec-body">{d['decision']}</div>
                <div class="dec-reason">{d['reason']}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#c4c4c0; font-size:0.82rem">Решений пока нет</span>', unsafe_allow_html=True)


# --- Main ---

def main():
    st.set_page_config(page_title="Product Pipeline", page_icon="◇", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    initiatives = scan_all()

    if not initiatives:
        st.markdown('<div class="page-title">Product Pipeline</div>', unsafe_allow_html=True)
        st.warning("Инициативы не найдены. Создай первую: `./new-initiative.sh имя-продакта название-инициативы`")
        return

    if "selected_path" in st.session_state:
        sel_path = Path(st.session_state["selected_path"])
        current = next((i for i in initiatives if i["path"] == sel_path), None)
        if current:
            render_initiative(current)
        else:
            del st.session_state["selected_path"]
            st.rerun()
    else:
        render_all(initiatives)


if __name__ == "__main__":
    main()
