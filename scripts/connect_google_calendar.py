"""Run locally to grant this application access; never prints credentials."""
import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import time
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser
import requests


def main():
    parser = argparse.ArgumentParser(description="Connect your personal Google Calendar.")
    parser.add_argument("client_json", type=Path, help="Downloaded Desktop OAuth client JSON")
    parser.add_argument("--readonly", action="store_true")
    parser.add_argument("--calendar-id", default="primary")
    parser.add_argument("--output", type=Path, default=Path(".streamlit/google-calendar.secrets.toml"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists. Choose a new --output path to preserve your existing credentials.")
    config = json.loads(args.client_json.read_text(encoding="utf-8"))
    if "installed" not in config:
        parser.error("Create a Desktop app OAuth client, then download its JSON.")
    client = config["installed"]
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    received = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args): pass

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path != "/callback" or query.get("state", [""])[0] != state:
                self.send_error(400, "Invalid OAuth callback")
                return
            received.update({key: values[0] for key, values in query.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("授权响应已收到。请回到终端查看结果，可以关闭此页。".encode())

    with HTTPServer(("127.0.0.1", 0), Callback) as server:
        server.timeout = 1
        redirect = f"http://127.0.0.1:{server.server_port}/callback"
        scope = "https://www.googleapis.com/auth/calendar.events" + (".readonly" if args.readonly else "")
        params = {"client_id": client["client_id"], "redirect_uri": redirect, "response_type": "code",
                  "scope": scope, "state": state, "access_type": "offline", "prompt": "consent",
                  "code_challenge": challenge, "code_challenge_method": "S256"}
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        print("Opening your browser for Google authorization. No calendar events will be created.")
        if not webbrowser.open(url):
            print("Open this authorization URL in a browser on this computer:", url)
        deadline = time.monotonic() + 300
        while not received and time.monotonic() < deadline:
            server.handle_request()
    if not received.get("code"):
        raise SystemExit("Authorization was declined or timed out. No credentials were saved.")
    response = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client["client_id"], "client_secret": client["client_secret"], "code": received["code"],
        "redirect_uri": redirect, "code_verifier": verifier, "grant_type": "authorization_code"}, timeout=30)
    if response.status_code != 200:
        raise SystemExit("Could not exchange authorization. Check your OAuth client and try again.")
    token = response.json()
    if not token.get("refresh_token"):
        raise SystemExit("Google did not return an offline token. Revoke this app's grant and reconnect.")
    values = {"client_id": client["client_id"], "client_secret": client["client_secret"],
              "refresh_token": token["refresh_token"], "calendar_id": args.calendar_id}
    output = "[google_calendar]\n" + "\n".join(f"{key} = {json.dumps(value)}" for key, value in values.items())
    output += f"\nreadonly = {'true' if args.readonly else 'false'}\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as file:
        file.write(output)
    args.output.chmod(0o600)
    print(f"Saved private configuration to {args.output}. Copy its section into Streamlit Secrets; do not commit it.")


if __name__ == "__main__":
    main()
