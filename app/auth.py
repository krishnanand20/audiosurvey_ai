# app/auth.py
from __future__ import annotations

import os
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from functools import wraps
from flask import request, session, redirect

from werkzeug.security import check_password_hash

NY_TZ = ZoneInfo("America/New_York")

AUTH_STATE_PATH = os.getenv("AUTH_STATE_PATH", "data/auth_state.json")
AUTH_LOG_PATH = os.getenv("AUTH_LOG_PATH", "data/auth_log.jsonl")

MAX_FAILS = int(os.getenv("AUTH_MAX_FAILS", "7"))          # lock after 7 fails
LOCK_SECONDS = int(os.getenv("AUTH_LOCK_SECONDS", "900"))  # 15 minutes lock
WINDOW_SECONDS = int(os.getenv("AUTH_WINDOW_SECONDS", "600"))  # track fails in 10 mins


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ny_now_str() -> str:
    return datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _load_auth_state() -> dict:
    if not os.path.exists(AUTH_STATE_PATH):
        return {"fails": {}, "locks": {}}
    try:
        with open(AUTH_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {"fails": {}, "locks": {}}
    except Exception:
        return {"fails": {}, "locks": {}}


def _save_auth_state(st: dict) -> None:
    _ensure_parent(AUTH_STATE_PATH)
    with open(AUTH_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


def _log_event(event: dict) -> None:
    _ensure_parent(AUTH_LOG_PATH)
    line = json.dumps(event, ensure_ascii=False)
    with open(AUTH_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _client_ip() -> str:
    # If behind ngrok/reverse proxy, X-Forwarded-For can exist
    xff = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return xff or (request.remote_addr or "unknown")


def _key(username: str) -> str:
    return f"{username.lower()}|{_client_ip()}"


def is_locked(username: str) -> tuple[bool, int]:
    st = _load_auth_state()
    k = _key(username)
    until = int(st.get("locks", {}).get(k, 0))
    now = int(time.time())
    if until > now:
        return True, until - now
    return False, 0


def record_fail(username: str) -> None:
    st = _load_auth_state()
    k = _key(username)
    now = int(time.time())

    fails = st.setdefault("fails", {}).setdefault(k, [])
    # keep only recent fails
    fails = [t for t in fails if now - int(t) <= WINDOW_SECONDS]
    fails.append(now)
    st["fails"][k] = fails

    if len(fails) >= MAX_FAILS:
        st.setdefault("locks", {})[k] = now + LOCK_SECONDS

    _save_auth_state(st)


def clear_fails(username: str) -> None:
    st = _load_auth_state()
    k = _key(username)
    st.get("fails", {}).pop(k, None)
    st.get("locks", {}).pop(k, None)
    _save_auth_state(st)


def start_session(username: str) -> None:
    session["user"] = username
    session["login_utc"] = _utc_now_iso()
    session["login_ts"] = int(time.time())
    session["ip"] = _client_ip()

    _log_event({
        "event": "login",
        "user": username,
        "ip": session["ip"],
        "login_utc": session["login_utc"],
        "login_local": _ny_now_str(),
        "user_agent": request.headers.get("User-Agent", ""),
    })


def end_session() -> None:
    user = session.get("user")
    if not user:
        session.clear()
        return

    login_ts = int(session.get("login_ts") or 0)
    now = int(time.time())
    duration_sec = max(0, now - login_ts)

    _log_event({
        "event": "logout",
        "user": user,
        "ip": session.get("ip", ""),
        "logout_utc": _utc_now_iso(),
        "logout_local": _ny_now_str(),
        "session_duration_sec": duration_sec,
    })

    session.clear()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("user"):
            return fn(*args, **kwargs)
        return redirect("/login")
    return wrapper


def verify_credentials(users: dict, username: str, password: str) -> bool:
    """
    users format:
    {
      "krishnanand": {"password_hash": "..."},
      "professor": {"password_hash": "..."}
    }
    """
    u = users.get(username.lower())
    if not u:
        return False
    return check_password_hash(u.get("password_hash", ""), password)