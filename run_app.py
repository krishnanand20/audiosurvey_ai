import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser


def _fetch_ngrok_https_url() -> str:
    try:
        with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=1.5) as res:
            data = json.loads(res.read().decode("utf-8"))
    except Exception:
        return ""

    for tunnel in data.get("tunnels", []):
        public_url = (tunnel or {}).get("public_url", "")
        if public_url.startswith("https://"):
            return public_url.rstrip("/")
    return ""


def _start_ngrok(workdir: str, port: int) -> subprocess.Popen:
    ngrok_bin = shutil.which("ngrok")
    if not ngrok_bin:
        raise RuntimeError("ngrok not found in PATH")

    return subprocess.Popen(
        [ngrok_bin, "http", str(port)],
        cwd=workdir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _ensure_public_base_url(env: dict, workdir: str, port: int = 5050):
    current = (env.get("PUBLIC_BASE_URL") or "").rstrip("/")

    # Reuse an already running ngrok tunnel if present.
    existing = _fetch_ngrok_https_url()
    if existing:
        env["PUBLIC_BASE_URL"] = existing
        return existing, None

    ngrok_proc = _start_ngrok(workdir=workdir, port=port)
    for _ in range(40):
        if ngrok_proc.poll() is not None:
            break
        tunnel_url = _fetch_ngrok_https_url()
        if tunnel_url:
            env["PUBLIC_BASE_URL"] = tunnel_url
            return tunnel_url, ngrok_proc
        time.sleep(0.5)

    if ngrok_proc.poll() is None:
        ngrok_proc.terminate()

    if current:
        return current, None

    raise RuntimeError("Could not create ngrok tunnel and PUBLIC_BASE_URL is not set")


def _default_open_url(env: dict, base_url: str, port: int = 5050) -> str:
    explicit = (env.get("APP_OPEN_URL") or "").strip()
    if explicit:
        return explicit

    open_public = (env.get("OPEN_PUBLIC_URL") or "0").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if base_url and not open_public and "ngrok" in base_url.lower():
        return f"http://127.0.0.1:{port}/admin"

    return base_url if base_url else f"http://127.0.0.1:{port}/admin"


def main() -> None:
    workdir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()

    auto_ngrok = (env.get("AUTO_START_NGROK") or "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }

    ngrok_proc = None
    base_url = (env.get("PUBLIC_BASE_URL") or "").rstrip("/")

    if auto_ngrok:
        try:
            base_url, ngrok_proc = _ensure_public_base_url(env=env, workdir=workdir, port=5050)
            print(f"Using PUBLIC_BASE_URL={base_url}")
        except Exception as exc:
            print(f"Failed to initialize ngrok: {exc}")
            sys.exit(1)

    app_proc = subprocess.Popen(
        [sys.executable, "-m", "app.twilio_handler", "serve"],
        cwd=workdir,
        env=env,
    )

    open_url = _default_open_url(env=env, base_url=base_url, port=5050)

    if base_url and "ngrok" in base_url.lower() and open_url.startswith("http://127.0.0.1"):
        print("Opening local admin URL to avoid ngrok browser warning page. Set OPEN_PUBLIC_URL=1 to open ngrok URL.")

    time.sleep(1.5)
    webbrowser.open(open_url)

    try:
        app_proc.wait()
    finally:
        if app_proc.poll() is None:
            app_proc.terminate()
        if ngrok_proc and ngrok_proc.poll() is None:
            ngrok_proc.terminate()


if __name__ == "__main__":
    main()
