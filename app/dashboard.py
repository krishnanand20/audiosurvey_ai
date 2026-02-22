# app/dashboard.py
from __future__ import annotations

import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from app.logger import logger
from flask import Blueprint, request, redirect, session, jsonify


from app.state import (
    load_participants,
    save_participants,
    upsert_participant,
    mask_phone,
    set_paused,
    is_paused,
    reset_state,
)
from app.utils import schedule_participant
from app.scheduler import run_once

dashboard_bp = Blueprint("dashboard", __name__)
NY_TZ = ZoneInfo("America/New_York")


# ----------------------------
# UI helpers
# ----------------------------
def pill(status: str) -> str:
    s = (status or "").lower().strip()
    cls = "pill"
    if s == "completed":
        cls += " pill-ok"
    elif s in {"failed"}:
        cls += " pill-bad"
    elif s in {"in_progress", "in-progress"}:
        cls += " pill-warn"
    else:
        cls += " pill-neutral"
    return f'<span class="{cls}">{(status or "pending")}</span>'


def fmt_dt(s: str | None) -> str:
    if not s:
        return ""
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return s


def fmt_dt_input(s: str | None) -> str:
    if not s:
        return ""
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%dT%H:%M")
    except Exception:
        t = str(s).strip().replace(" ", "T")
        return t[:16]


def _read_questions_text() -> str:
    path = "data/questions.txt"
    try:
        import yaml
        if os.path.exists("config.yaml"):
            with open("config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            path = (cfg.get("ivr", {}) or {}).get("questions_file", path)
    except Exception:
        pass

    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _safe_q(s: str) -> str:
    return (s or "").replace(" ", "+").replace("&", "and").replace("%", "")


def _whoami() -> str:
    # twilio_handler.py sets session["user"]
    return (session.get("user") or "").strip()


def engaged_badge(engaged: bool) -> str:
    cls = "eng-badge eng-yes" if engaged else "eng-badge eng-no"
    label = "Engaged" if engaged else "Not engaged"
    return f'<span class="{cls}"><span class="eng-dot"></span>{label}</span>'


def _dashboard_snapshot(state: dict) -> tuple[int, dict, list[dict]]:
    total = len(state)
    counts = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
    participants = []

    for pid, p in sorted(state.items(), key=lambda x: str(x[0])):
        st = (p.get("status") or "pending").lower().strip()
        if st in counts:
            counts[st] += 1
        else:
            counts["pending"] += 1

        participants.append(
            {
                "participant_id": str(pid),
                "phone_masked": mask_phone(p.get("phone_e164")),
                "status": p.get("status") or "pending",
                "attempts": int(p.get("attempts", 0) or 0),
                "engaged": bool(p.get("engaged", False)),
                "scheduled_local": fmt_dt(p.get("scheduled_time_local")),
                "scheduled_input": fmt_dt_input(p.get("scheduled_time_local")).replace("T", " "),
            }
        )

    return total, counts, participants


def _participants_rows_html(participants: list[dict]) -> str:
    rows_html = []
    for p in participants:
        rows_html.append(
            f"""
          <tr>
            <td class="mono">{p["participant_id"]}</td>
            <td class="mono">{p["phone_masked"]}</td>
            <td>{pill(p["status"])}</td>
            <td class="mono">{p["attempts"]}</td>
            <td>{engaged_badge(p["engaged"])}</td>
            <td class="mono">{p["scheduled_local"]}</td>
            <td>
              <form class="inline schedule-form" method="POST" action="/admin/schedule">
                <input type="hidden" name="participant_id" value="{p["participant_id"]}">
                <input type="hidden" name="local_time" value="">
                <input class="input input-sm schedule-datetime" type="text" name="local_time_ui" value="{p["scheduled_input"]}" placeholder="YYYY-MM-DD HH:MM" autocomplete="off" />
                <button class="btn btn-sm btn-primary" type="submit">Set</button>
              </form>
            </td>
          </tr>
        """
        )
    return "\n".join(rows_html)


# ----------------------------
# Routes
# ----------------------------
@dashboard_bp.route("/admin", methods=["GET"])
def admin_home():
    # Auth is enforced in twilio_handler.py @app.before_request.
    # If someone hits this directly without login, they'll be redirected to /login by the main app.
    state = load_participants()
    paused = is_paused()

    msg = (request.args.get("msg") or "").strip()
    err = (request.args.get("err") or "").strip()

    total, counts, participants = _dashboard_snapshot(state)

    rows = _participants_rows_html(participants) if participants else """
      <tr><td colspan="7" class="muted">No participants loaded yet. Upload a contacts CSV.</td></tr>
    """

    initial_clock = datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    user = _whoami()

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>AudioSurvey Admin</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/themes/dark.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/confirmDate/confirmDate.css">
  <style>
    :root {{
      --bg: #0b1020;
      --card: #121a33;
      --muted: #9aa4c3;
      --text: #e8ecff;
      --line: rgba(255,255,255,.08);
      --accent: #7c5cff;
      --good: #20c997;
      --warn: #f59f00;
      --bad: #ff6b6b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      background: radial-gradient(1200px 800px at 20% 10%, rgba(124,92,255,.22), transparent 60%),
                  radial-gradient(900px 600px at 80% 20%, rgba(32,201,151,.12), transparent 55%),
                  var(--bg);
      color: var(--text);
    }}
    .wrap {{ max-width: 1100px; margin: 28px auto; padding: 0 18px; }}
    .top {{
      display: flex; align-items: center; justify-content: space-between;
      gap: 16px; margin-bottom: 16px;
    }}
    .title h1 {{ margin: 0; font-size: 22px; letter-spacing: .2px; }}
    .title p {{ margin: 6px 0 0; color: var(--muted); font-size: 13px; }}
    .card {{
      background: rgba(18,26,51,.78);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,.25);
      backdrop-filter: blur(8px);
    }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .row {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}

    .btn {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,.06);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 16px;
      cursor: pointer;
      font-weight: 700;
      transition: transform .05s ease, background .15s ease, border-color .15s ease;
    }}
    .btn:hover {{ background: rgba(255,255,255,.10); }}
    .btn:active {{ transform: translateY(1px); }}
    .btn-primary {{ background: rgba(124,92,255,.22); border-color: rgba(124,92,255,.35); }}
    .btn-good {{ background: rgba(32,201,151,.16); border-color: rgba(32,201,151,.28); }}
    .btn-bad {{ background: rgba(255,107,107,.14); border-color: rgba(255,107,107,.28); }}
    .btn-sm {{ padding: 7px 10px; border-radius: 12px; font-size: 12px; }}

    .input {{
      border: 1px solid var(--line);
      background: rgba(0,0,0,.18);
      color: var(--text);
      padding: 10px 10px;
      border-radius: 12px;
      outline: none;
      width: 100%;
    }}
    .input-sm {{ padding: 7px 9px; border-radius: 10px; width: 170px; }}

    .muted {{ color: var(--muted); font-size: 13px; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12.5px; }}
    .sep {{ height: 1px; background: var(--line); margin: 14px 0; }}

    .pill {{
      display: inline-flex; align-items: center; justify-content: center;
      padding: 5px 9px; border-radius: 999px;
      border: 1px solid var(--line);
      font-size: 12px; font-weight: 800;
      letter-spacing: .2px;
    }}
    .pill-ok {{ border-color: rgba(32,201,151,.35); background: rgba(32,201,151,.14); }}
    .pill-warn {{ border-color: rgba(245,159,0,.35); background: rgba(245,159,0,.12); }}
    .pill-bad {{ border-color: rgba(255,107,107,.35); background: rgba(255,107,107,.12); }}
    .pill-neutral {{ border-color: rgba(154,164,195,.35); background: rgba(154,164,195,.10); }}
    .eng-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .2px;
    }}
    .eng-dot {{
      width: 8px;
      height: 8px;
      border-radius: 999px;
      display: inline-block;
    }}
    .eng-yes {{
      border-color: rgba(32,201,151,.35);
      background: rgba(32,201,151,.10);
      color: #c8f5e8;
    }}
    .eng-yes .eng-dot {{ background: #20c997; }}
    .eng-no {{
      border-color: rgba(154,164,195,.30);
      background: rgba(154,164,195,.10);
      color: #d0d6ea;
    }}
    .eng-no .eng-dot {{ background: #9aa4c3; }}

    .banner {{
      border-radius: 14px; padding: 10px 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.06);
      margin-bottom: 12px;
      font-size: 13px;
    }}
    .banner.err {{ border-color: rgba(255,107,107,.35); background: rgba(255,107,107,.10); }}
    .banner.ok {{ border-color: rgba(32,201,151,.35); background: rgba(32,201,151,.10); }}

    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      overflow: visible;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.12);
    }}
    th, td {{
      padding: 10px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: middle;
      font-size: 13px;
    }}
    th {{
      text-align: left;
      color: var(--muted);
      font-weight: 800;
      background: rgba(255,255,255,.04);
    }}
    tr:hover td {{ background: rgba(255,255,255,.03); }}
    .inline {{ display: inline-flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
    .schedule-form {{
      width: 100%;
      align-items: center;
      justify-content: flex-start;
      flex-wrap: nowrap;
      gap: 10px;
    }}
    .schedule-form .btn {{ flex-shrink: 0; }}
    .schedule-datetime {{
      min-width: 240px;
      flex: 1;
      max-width: 360px;
    }}
    @media (max-width: 820px) {{
      .schedule-form {{ flex-wrap: wrap; }}
      .schedule-datetime {{ max-width: 100%; }}
    }}
    .flatpickr-calendar {{
      background: #0d1830;
      border: 1px solid rgba(255,255,255,.22);
      box-shadow: 0 14px 30px rgba(0,0,0,.45);
      border-radius: 12px;
      overflow: hidden;
    }}
    .flatpickr-months,
    .flatpickr-weekdays {{
      background: #12234a;
    }}
    .flatpickr-months .flatpickr-month,
    .flatpickr-current-month .flatpickr-monthDropdown-months,
    .flatpickr-current-month input.cur-year,
    .flatpickr-weekday,
    .flatpickr-day {{
      color: #e8ecff;
    }}
    .flatpickr-monthDropdown-months,
    .flatpickr-current-month input.cur-year {{
      background: rgba(255,255,255,.08);
      border-radius: 8px;
    }}
    .flatpickr-months .flatpickr-prev-month,
    .flatpickr-months .flatpickr-next-month {{
      color: #e8ecff;
      fill: #e8ecff;
      border-radius: 8px;
      width: 34px;
      height: 34px;
      top: 4px;
      padding: 6px;
    }}
    .flatpickr-months .flatpickr-prev-month:hover,
    .flatpickr-months .flatpickr-next-month:hover {{
      background: rgba(255,255,255,.12);
    }}
    .flatpickr-day.selected,
    .flatpickr-day.selected:hover,
    .flatpickr-day.startRange,
    .flatpickr-day.endRange {{
      background: rgba(124,92,255,.95);
      border-color: rgba(124,92,255,.95);
    }}
    .flatpickr-day.today {{
      border-color: rgba(32,201,151,.9);
    }}
    .flatpickr-day.prevMonthDay,
    .flatpickr-day.nextMonthDay {{
      color: rgba(232,236,255,.45);
    }}
    .flatpickr-day:hover {{
      background: rgba(255,255,255,.16);
    }}
    .flatpickr-time {{
      border-top: 1px solid rgba(255,255,255,.14);
    }}
    .flatpickr-time input,
    .flatpickr-time .flatpickr-am-pm {{
      color: #e8ecff;
      font-weight: 700;
    }}
    .flatpickr-time input:hover,
    .flatpickr-time .flatpickr-am-pm:hover {{
      background: rgba(255,255,255,.14);
    }}
    .flatpickr-confirm {{
      background: rgba(124,92,255,.25);
      border-top: 1px solid rgba(255,255,255,.14);
      color: #e8ecff;
      font-weight: 800;
      letter-spacing: .2px;
    }}
    .flatpickr-confirm:hover {{
      background: rgba(124,92,255,.38);
    }}

    .kpi {{
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 10px; margin-top: 10px;
    }}
    @media (max-width: 700px) {{ .kpi {{ grid-template-columns: repeat(2, 1fr); }} }}
    .k {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 10px;
      background: rgba(255,255,255,.04);
    }}
    .k .n {{ font-size: 20px; font-weight: 900; }}
    .k .l {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}

    .file-wrap {{
      display:flex; gap:10px; align-items:center; flex-wrap:wrap;
      width: 100%;
    }}
    input[type="file"].file-hidden {{
      position: absolute;
      left: -9999px;
      width: 1px;
      height: 1px;
      overflow: hidden;
    }}
    .file-name {{
      color: var(--muted);
      font-size: 13px;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px dashed rgba(255,255,255,.14);
      background: rgba(0,0,0,.14);
      flex: 1;
      min-width: 220px;
    }}
  </style>
</head>

<body>
  <div class="wrap">
    <div class="top">
      <div class="title">
        <h1>AudioSurvey AI — Admin</h1>
        <p>
          NYC time: <span id="nycClock" class="mono">{initial_clock}</span>
          <span class="muted" style="margin-left:10px;">Logged in as:</span>
          <span class="mono">{user or "unknown"}</span>
        </p>
      </div>

      <div class="row">
        <span class="muted">System:</span>
        <span class="{ 'pill pill-bad' if paused else 'pill pill-ok' }">{'STOPPED' if paused else 'RUNNING'}</span>

        <form method="POST" action="/logout" style="margin-left:10px;">
          <button class="btn btn-sm btn-bad" type="submit">Sign out</button>
        </form>
      </div>
    </div>

    {f'<div class="banner ok">{msg}</div>' if msg else ''}
    {f'<div class="banner err">{err}</div>' if err else ''}

    <div class="card">
      <div class="row">
        <form method="POST" action="/admin/dial_now">
          <button class="btn btn-primary" type="submit">Dial Now</button>
        </form>

        <form method="POST" action="/admin/resume">
          <button class="btn btn-good" type="submit">Start</button>
        </form>

        <form method="POST" action="/admin/pause">
          <button class="btn btn-bad" type="submit">Stop</button>
        </form>

        <form method="POST" action="/admin/reset_state" onsubmit="return confirm('This will reset participants and call log (with backup files). Continue?');">
          <button class="btn btn-bad" type="submit">State Refresh</button>
        </form>

        <span class="muted">Calls go out only when participants are eligible.</span>
      </div>

      <div class="kpi">
        <div class="k"><div id="kpiTotal" class="n mono">{total}</div><div class="l">Total</div></div>
        <div class="k"><div id="kpiPending" class="n mono">{counts["pending"]}</div><div class="l">Pending</div></div>
        <div class="k"><div id="kpiInProgress" class="n mono">{counts["in_progress"]}</div><div class="l">In progress</div></div>
        <div class="k"><div id="kpiCompleted" class="n mono">{counts["completed"]}</div><div class="l">Completed</div></div>
      </div>
    </div>

    <div class="sep"></div>

    <div class="grid">
      <div class="card">
        <h3 style="margin:0 0 8px 0;">Upload contacts</h3>
        <p class="muted" style="margin:0 0 12px 0;">
          CSV headers: <span class="mono">participant_id,phone_e164</span>
        </p>

        <form method="POST" action="/admin/upload_contacts" enctype="multipart/form-data">
          <div class="file-wrap">
            <input id="contactsFile" class="file-hidden" type="file" name="file" accept=".csv" />
            <label for="contactsFile" class="btn btn-primary">Choose CSV</label>
            <div id="fileName" class="file-name">No file selected</div>
            <button class="btn btn-primary" type="submit">Upload</button>
          </div>
        </form>
      </div>

      <div class="card">
        <h3 style="margin:0 0 8px 0;">Questions</h3>
        <p class="muted" style="margin:0 0 12px 0;">One question per line.</p>
        <form method="POST" action="/admin/save_questions">
          <textarea class="input" name="questions" rows="8" style="resize:vertical;">{_read_questions_text()}</textarea>
          <div style="height:10px;"></div>
          <button class="btn btn-primary" type="submit">Save questions</button>
        </form>
      </div>
    </div>

    <div class="sep"></div>

    <!-- NEW: Conference call -->
    <div class="card">
      <h3 style="margin:0 0 8px 0;">Conference call</h3>
      <p class="muted" style="margin:0 0 12px 0;">
        Enter two phone numbers in international format (example: <span class="mono">+1716XXXXXXX</span>). Both will join the same call.
      </p>

      <form class="inline" method="POST" action="/admin/conference_call">
        <input class="input input-sm" name="number_1" placeholder="+1..." required />
        <input class="input input-sm" name="number_2" placeholder="+1..." required />
        <button class="btn btn-primary" type="submit">Start call</button>
      </form>
    </div>

    <div class="sep"></div>

    <div class="card">
      <h3 style="margin:0 0 10px 0;">Participants</h3>
      <div class="muted" style="margin-bottom:10px;">
        Tip: click schedule field, choose date/time, press <span class="mono">✓</span> in calendar, then press <span class="mono">Set</span>.
      </div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Attempts</th>
            <th>Engaged</th>
            <th>Scheduled (NYC)</th>
            <th>Schedule</th>
          </tr>
        </thead>
        <tbody id="participantsTbody">
          {rows}
        </tbody>
      </table>
    </div>

    <div style="height:24px;"></div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
  <script src="https://cdn.jsdelivr.net/npm/flatpickr/dist/plugins/confirmDate/confirmDate.js"></script>
  <script>
    // Live NYC clock
    const clockEl = document.getElementById("nycClock");
    const fmt = new Intl.DateTimeFormat("en-US", {{
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
      timeZoneName: "short"
    }});

    function tickClock() {{
      const parts = fmt.formatToParts(new Date());
      const get = (t) => parts.find(p => p.type === t)?.value || "";
      const y = get("year");
      const mo = get("month");
      const d = get("day");
      const h = get("hour");
      const mi = get("minute");
      const s = get("second");
      const tz = get("timeZoneName");
      clockEl.textContent = `${{y}}-${{mo}}-${{d}} ${{h}}:${{mi}}:${{s}} ${{tz}}`;
    }}
    tickClock();
    setInterval(tickClock, 1000);

    // File picker label
    const fileInput = document.getElementById("contactsFile");
    const fileName = document.getElementById("fileName");
    if (fileInput) {{
      fileInput.addEventListener("change", () => {{
        const f = fileInput.files && fileInput.files[0];
        fileName.textContent = f ? f.name : "No file selected";
      }});
    }}

    // Live dashboard table + KPI refresh (no full page reload)
    const kpiTotal = document.getElementById("kpiTotal");
    const kpiPending = document.getElementById("kpiPending");
    const kpiInProgress = document.getElementById("kpiInProgress");
    const kpiCompleted = document.getElementById("kpiCompleted");
    const participantsTbody = document.getElementById("participantsTbody");
    let pollInFlight = false;

    const esc = (v) => String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

    function statusPill(statusRaw) {{
      const status = String(statusRaw || "pending");
      const s = status.toLowerCase().trim();
      let cls = "pill pill-neutral";
      if (s === "completed") cls = "pill pill-ok";
      else if (s === "failed") cls = "pill pill-bad";
      else if (s === "in_progress" || s === "in-progress") cls = "pill pill-warn";
      return `<span class="${{cls}}">${{esc(status)}}</span>`;
    }}

    function engagedBadge(engaged) {{
      if (engaged) {{
        return '<span class="eng-badge eng-yes"><span class="eng-dot"></span>Engaged</span>';
      }}
      return '<span class="eng-badge eng-no"><span class="eng-dot"></span>Not engaged</span>';
    }}

    function participantRow(p) {{
      const pid = esc(p.participant_id);
      const phone = esc(p.phone_masked || "");
      const status = statusPill(p.status);
      const attempts = esc(p.attempts ?? 0);
      const engaged = engagedBadge(!!p.engaged);
      const sched = esc(p.scheduled_local || "");
      const schedInput = esc(p.scheduled_input || "");

      return `
        <tr>
          <td class="mono">${{pid}}</td>
          <td class="mono">${{phone}}</td>
          <td>${{status}}</td>
          <td class="mono">${{attempts}}</td>
          <td>${{engaged}}</td>
          <td class="mono">${{sched}}</td>
          <td>
            <form class="inline schedule-form" method="POST" action="/admin/schedule">
              <input type="hidden" name="participant_id" value="${{pid}}">
              <input type="hidden" name="local_time" value="">
              <input class="input input-sm schedule-datetime" type="text" name="local_time_ui" value="${{schedInput}}" placeholder="YYYY-MM-DD HH:MM" autocomplete="off" />
              <button class="btn btn-sm btn-primary" type="submit">Set</button>
            </form>
          </td>
        </tr>
      `;
    }}

    function normalizeScheduleInputToServer(value) {{
      return String(value || "").trim().replace("T", " ").replace(/\s+/g, " ");
    }}

    function initSchedulePickers(root = document) {{
      if (typeof flatpickr !== "function") return;
      const inputs = root.querySelectorAll("input.schedule-datetime[name='local_time_ui']");
      inputs.forEach((input) => {{
        if (input._flatpickr) return;
        const fpPlugins = [];
        if (typeof confirmDatePlugin === "function") {{
          fpPlugins.push(new confirmDatePlugin({{
            confirmIcon: "✓",
            confirmText: " OK",
            showAlways: false,
            theme: "dark"
          }}));
        }}
        flatpickr(input, {{
          enableTime: true,
          time_24hr: true,
          minuteIncrement: 1,
          dateFormat: "Y-m-d H:i",
          allowInput: true,
          disableMobile: true,
          appendTo: document.body,
          position: "auto center",
          plugins: fpPlugins,
        }});
      }});
    }}

    document.addEventListener("submit", (e) => {{
      const form = e.target.closest("form.schedule-form");
      if (!form) return;

      const ui = form.querySelector("input.schedule-datetime[name='local_time_ui']");
      const hidden = form.querySelector("input[type='hidden'][name='local_time']");
      if (!ui || !hidden) return;

      const uiVal = String(ui.value || "").trim();
      if (!uiVal) {{
        e.preventDefault();
        ui.focus();
        return;
      }}

      hidden.value = normalizeScheduleInputToServer(uiVal);
    }});

    async function refreshDashboard() {{
      if (pollInFlight) return;
      pollInFlight = true;
      try {{
        // Do not re-render while any date-time picker popup is open.
        const pickerOpen = !!document.querySelector(".flatpickr-calendar.open");
        if (pickerOpen) return;

        const res = await fetch("/admin/live_state", {{
          method: "GET",
          headers: {{ "Accept": "application/json" }},
          cache: "no-store"
        }});
        if (!res.ok) return;
        const data = await res.json();

        if (kpiTotal) kpiTotal.textContent = String(data.total ?? 0);
        if (kpiPending) kpiPending.textContent = String(data.counts?.pending ?? 0);
        if (kpiInProgress) kpiInProgress.textContent = String(data.counts?.in_progress ?? 0);
        if (kpiCompleted) kpiCompleted.textContent = String(data.counts?.completed ?? 0);

        if (participantsTbody) {{
          const active = document.activeElement;
          const editingSchedule = !!(
            active &&
            participantsTbody.contains(active) &&
            active.classList &&
            active.classList.contains("schedule-datetime")
          );
          if (editingSchedule) {{
            return;
          }}

          const ps = Array.isArray(data.participants) ? data.participants : [];
          if (!ps.length) {{
            participantsTbody.innerHTML = '<tr><td colspan="7" class="muted">No participants loaded yet. Upload a contacts CSV.</td></tr>';
          }} else {{
            participantsTbody.innerHTML = ps.map(participantRow).join("");
            initSchedulePickers(participantsTbody);
          }}
        }}
      }} catch (_e) {{
        // no-op: keep UI stable if one poll fails
      }} finally {{
        pollInFlight = false;
      }}
    }}

    initSchedulePickers(document);
    refreshDashboard();
    setInterval(refreshDashboard, 1000);
  </script>
</body>
</html>
"""
    return html


@dashboard_bp.route("/admin/live_state", methods=["GET"])
def admin_live_state():
    state = load_participants()
    total, counts, participants = _dashboard_snapshot(state)
    return jsonify(
        {
            "total": total,
            "counts": counts,
            "participants": participants,
        }
    )


@dashboard_bp.route("/admin/upload_contacts", methods=["POST"])
def admin_upload_contacts():
    f = request.files.get("file")
    if not f:
        return redirect("/admin?err=No+file+selected")

    content = f.read().decode("utf-8", errors="ignore").splitlines()
    reader = csv.DictReader(content)

    state = load_participants()
    count = 0

    for row in reader:
        pid = (row.get("participant_id") or "").strip()
        phone = (row.get("phone_e164") or "").strip()
        if not pid or not phone:
            continue

        upsert_participant(state, pid, phone)

        # 🔒 VERY IMPORTANT → uploaded participants must NOT be callable yet
        state[pid]["status"] = "idle"
        state[pid]["scheduled_time_local"] = None
        state[pid]["scheduled_time_utc"] = None
        state[pid]["last_call_time"] = None
        state[pid]["attempts"] = 0
        state[pid]["engaged"] = False
        state[pid]["last_call_sid"] = None
        state[pid]["last_call_status"] = None

        count += 1

    save_participants(state)
    return redirect(f"/admin?msg=Uploaded+{count}+contacts")


@dashboard_bp.route("/admin/save_questions", methods=["POST"])
def admin_save_questions():
    path = "data/questions.txt"
    try:
        import yaml
        if os.path.exists("config.yaml"):
            with open("config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            path = (cfg.get("ivr", {}) or {}).get("questions_file", path)
    except Exception:
        pass

    text = (request.form.get("questions") or "").strip()
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + ("\n" if text and not text.endswith("\n") else ""))

    return redirect("/admin?msg=Questions+saved")


@dashboard_bp.route("/admin/schedule", methods=["POST"])
def admin_schedule():
    pid = (request.form.get("participant_id") or "").strip()
    local_time = (request.form.get("local_time") or "").strip().replace("T", " ")

    if not pid:
        return redirect("/admin?err=Missing+participant_id")

    if not local_time:
        return redirect("/admin?err=Please+enter+time+as+YYYY-MM-DD+HH:MM")

    try:
        schedule_participant(pid, local_time)
    except Exception as e:
        return redirect("/admin?err=" + _safe_q(str(e)))

    return redirect(f"/admin?msg=Scheduled+{pid}+at+{_safe_q(local_time)}")


@dashboard_bp.route("/admin/pause", methods=["POST"])
def admin_pause():
    set_paused(True)
    return redirect("/admin?msg=Stopped")


@dashboard_bp.route("/admin/resume", methods=["POST"])
def admin_resume():
    set_paused(False)
    return redirect("/admin?msg=Started")

@dashboard_bp.route("/admin/dial_now", methods=["POST"])
def admin_dial_now():
    run_once(force=True)
    return redirect("/admin?msg=Dial+Now+triggered")


@dashboard_bp.route("/admin/reset_state", methods=["POST"])
def admin_reset_state():
    try:
        reset_state(reset_call_log=True, backup=True)
    except Exception as e:
        return redirect("/admin?err=" + _safe_q(str(e)))
    return redirect("/admin?msg=State+reset+complete")
