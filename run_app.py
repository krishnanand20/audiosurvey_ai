import os
import time
import webbrowser
import subprocess
import sys

def main():
    # Start the flask app (your module)
    # Use python -m to match your current setup
    cmd = [sys.executable, "-m", "app.twilio_handler", "serve"]

    # Start in same folder so relative paths (data/...) work
    p = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    base_url = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")
    open_url = (os.getenv("APP_OPEN_URL") or "").strip()
    if not open_url:
        open_url = base_url if base_url else "http://127.0.0.1:5050/admin"

    # Give server a second to boot, then open the configured website
    time.sleep(1.5)
    webbrowser.open(open_url)

    # Wait for server process to exit
    p.wait()

if __name__ == "__main__":
    main()
