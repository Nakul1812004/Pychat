# shared/config.py
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def load_settings():
    """Load settings.json or create default."""
    if not os.path.exists(SETTINGS_FILE):
        default = {
            "server_ip": "127.0.0.1",
            "server_port": 8000
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default, f, indent=4)
        return default

    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


def get_base_url():
    """
    Return correct base URL:

    ✔ http://127.0.0.1:8000
    ✔ https://xxxx.ngrok-free.app
    ✔ https://mycustomdomain.com
    ✔ http://192.168.1.10:8000
    ✔ https://my-ip.ngrok.io
    """
    cfg = load_settings()
    server_ip = cfg.get("server_ip", "127.0.0.1")
    port = cfg.get("server_port", 8000)

    server_ip = server_ip.rstrip("/")

    # --------------------------------------
    # 1. Already a full URL → return as is
    # --------------------------------------
    if server_ip.startswith(("http://", "https://")):
        return server_ip

    # --------------------------------------
    # 2. ngrok domains automatically HTTPS
    # --------------------------------------
    if "ngrok" in server_ip or "ngrok-free" in server_ip:
        return f"https://{server_ip}"

    # --------------------------------------
    # 3. Public domain (no port) → assume HTTPS
    # --------------------------------------
    if "." in server_ip and port in (80, 443):
        proto = "https" if port == 443 else "http"
        return f"{proto}://{server_ip}"

    # --------------------------------------
    # 4. Localhost or LAN IP with port
    # --------------------------------------
    return f"http://{server_ip}:{port}"


def http_to_ws(url: str) -> str:
    """
    Convert HTTP base URL → WS URL.
    
    Examples:
        http://127.0.0.1:8000 -> ws://127.0.0.1:8000
        https://xxxx.ngrok-free.app -> wss://xxxx.ngrok-free.app
    """
    url = url.rstrip("/")

    if url.startswith("https://"):
        return "wss://" + url[8:]

    if url.startswith("http://"):
        return "ws://" + url[7:]

    return url
