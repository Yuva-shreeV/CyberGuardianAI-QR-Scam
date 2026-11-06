import socket
import uvicorn
import sys
import os
import urllib.request

# Force UTF-8 output so emoji/unicode don't crash on Windows CP1252 terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def is_port_in_use(port):
    """Return True if something is already listening on the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def is_cyberguardian_running(port):
    """
    Return True if the process on the port is our own CyberGuardian server
    (it responds to GET /health with {"status": "healthy"}).
    """
    try:
        url = f"http://127.0.0.1:{port}/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            import json
            body = json.loads(resp.read())
            return body.get("status") == "healthy"
    except Exception:
        return False


if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000

    # ── Pre-flight: check if port 8000 is already in use ──────────────
    if is_port_in_use(port):
        if is_cyberguardian_running(port):
            print("=" * 60)
            print("  CyberGuardian AI is ALREADY RUNNING on port", port)
            print("=" * 60)
            print(f"  Local Access:    http://localhost:{port}/app/")
            print(f"  Network Access:  http://{local_ip}:{port}/app/")
            print("=" * 60)
            print("  The existing server is working. No need to start another.")
            print()
            print("  To STOP it and start fresh, run this command first:")
            print(f"    netstat -ano | findstr :{port}")
            print("  Then kill the PID shown:  taskkill /PID <PID> /F")
            print("=" * 60)
        else:
            print("=" * 60)
            print(f"  ERROR: Port {port} is already in use by another program.")
            print("=" * 60)
            print("  CyberGuardian AI cannot start because port", port, "is taken.")
            print()
            print("  To find what is using it, run:")
            print(f"    netstat -ano | findstr :{port}")
            print("  Then stop ONLY that program before running this again.")
            print("=" * 60)
        sys.exit(0)
    # ──────────────────────────────────────────────────────────────────

    print("=" * 60)
    print("  CyberGuardian AI - Server Starting")
    print("=" * 60)
    print(f"  Local Access:    http://localhost:{port}/app/")
    print(f"  Network Access:  http://{local_ip}:{port}/")
    print(f"  Web App URL:     http://{local_ip}:{port}/app/")
    print("=" * 60)
    print("  All devices on the same Wi-Fi can use the Web App URL.")
    print("=" * 60)
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=False)
