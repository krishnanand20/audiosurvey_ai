# app/dashboard.py
from flask import Blueprint, request, redirect
import csv
import os
from app.utils import schedule_participant

from app.state import (
    load_participants, save_participants, upsert_participant,
    mask_phone, set_paused, is_paused
)
from app.utils import schedule_participant

dashboard_bp = Blueprint("dashboard", __name__)

def require_admin(req) -> bool:
    token = os.getenv("ADMIN_TOKEN", "").strip()
    if not token:
        return True
    return (req.args.get("token") == token) or (req.form.get("token") == token)

def token_qs() -> str:
    token = os.getenv("ADMIN_TOKEN", "").strip()
    return f"?token={token}" if token else ""

@dashboard_bp.route("/admin", methods=["GET"])
def admin_home():
    if not require_admin(request):
        return ("Unauthorized", 401)

    state = load_participants()
    paused = is_paused()
    token = os.getenv("ADMIN_TOKEN", "").strip()
    qs = token_qs()

    rows = []
    for pid, p in sorted(state.items(), key=lambda x: x[0]):
        rows.append(f"""
        <tr>
          <td>{pid}</td>
          <td>{mask_phone(p.get("phone_e164"))}</td>
          <td>{p.get("status")}</td>
          <td>{p.get("attempts")}</td>
          <td>{p.get("scheduled_time_local") or ""}</td>
          <td>
            <form method="POST" action="/admin/schedule{qs}" style="display:flex;gap:8px;">
              <input type="hidden" name="token" value="{token}">
              <input type="hidden" name="participant_id" value="{pid}">
              <input name="local_time" placeholder="YYYY-MM-DD HH:MM" style="width:170px;">
              <button type="submit">Schedule</button>
            </form>
          </td>
        </tr>
        """)

    html = f"""
    <html><body style="font-family:Arial;padding:18px;">
      <h2>AudioSurvey Admin</h2>
      <p>Status: <b>{"PAUSED" if paused else "RUNNING"}</b></p>

      <div style="display:flex;gap:10px;">
        <form method="POST" action="/admin/pause{qs}">
          <input type="hidden" name="token" value="{token}">
          <button>Pause</button>
        </form>
        <form method="POST" action="/admin/resume{qs}">
          <input type="hidden" name="token" value="{token}">
          <button>Resume</button>
        </form>
        <form method="POST" action="/admin/dial_now{qs}">
          <input type="hidden" name="token" value="{token}">
          <button>Dial Now</button>
        </form>
      </div>

      <hr>

      <h3>Upload Contacts CSV</h3>
      <p>CSV headers must be: <code>participant_id,phone_e164</code></p>
      <form method="POST" action="/admin/upload_contacts{qs}" enctype="multipart/form-data">
        <input type="hidden" name="token" value="{token}">
        <input type="file" name="file" accept=".csv">
        <button type="submit">Upload</button>
      </form>

      <hr>

      <h3>Participants</h3>
      <table border="1" cellpadding="6" cellspacing="0">
        <tr>
          <th>ID</th><th>Phone</th><th>Status</th><th>Attempts</th><th>Scheduled</th><th>Action</th>
        </tr>
        {''.join(rows) if rows else '<tr><td colspan="6">No participants loaded. Upload contacts CSV.</td></tr>'}
      </table>
    </body></html>
    """
    return html

@dashboard_bp.route("/admin/upload_contacts", methods=["POST"])
def admin_upload_contacts():
    if not require_admin(request):
        return ("Unauthorized", 401)

    f = request.files.get("file")
    if not f:
        return redirect("/admin" + token_qs())

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
        count += 1

    save_participants(state)
    return redirect("/admin" + token_qs())

@dashboard_bp.route("/admin/schedule", methods=["POST"])
def admin_schedule():
    if not require_admin(request):
        return ("Unauthorized", 401)

    pid = (request.form.get("participant_id") or "").strip()
    local_time = (request.form.get("local_time") or "").strip()

    if not local_time:
        # Don’t crash with 500
        return redirect("/admin" + token_qs())

    try:
        schedule_participant(pid, local_time)
    except Exception:
        # keep it simple for now; later we can show error message in UI
        pass

    return redirect("/admin" + token_qs())

@dashboard_bp.route("/admin/pause", methods=["POST"])
def admin_pause():
    if not require_admin(request):
        return ("Unauthorized", 401)
    set_paused(True)
    return redirect("/admin" + token_qs())

@dashboard_bp.route("/admin/resume", methods=["POST"])
def admin_resume():
    if not require_admin(request):
        return ("Unauthorized", 401)
    set_paused(False)
    return redirect("/admin" + token_qs())

@dashboard_bp.route("/admin/dial_now", methods=["POST"])
def admin_dial_now():
    if not require_admin(request):
        return ("Unauthorized", 401)
    # this endpoint is handled by twilio_handler via calling scheduler once
    return redirect("/admin" + token_qs())