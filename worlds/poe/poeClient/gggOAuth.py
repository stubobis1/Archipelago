import os
import sys
vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
from worlds.poe.poeClient import fileHelper
fileHelper.load_vendor_modules()
import http.server
import socketserver
import urllib.parse
import webbrowser
import base64
import hashlib
import requests
import asyncio
import httpx
import time

# === CONFIG ===
CLIENT_ID = "archipelagopoe"
REDIRECT_URI = "http://127.0.0.1:8234/oauth-callback"
SCOPES = "account:profile account:characters account:stashes account:leagues"
PORT = 8234


# === Step 1: Generate PKCE pair ===
_code_verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b'=').decode()
_code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(_code_verifier.encode()).digest()
).rstrip(b'=').decode()

# === Step 2: Build Auth URL ===
_params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
    "state": "mystate",
    "code_challenge": _code_challenge,
    "code_challenge_method": "S256",
}
_auth_url = f"https://www.pathofexile.com/oauth/authorize?{urllib.parse.urlencode(_params)}"
access_token = ""
token_expire_time = None
# === Step 3: Start local callback server ===
class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global access_token
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/oauth-callback":

            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if code:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h1>Authorization successful! You can close this tab.</h1>")
                print("\n✅ Authorization code received.")
                print("🔄 Exchanging for access token...")
                print(f"\n🔑 code_verifier = {_code_verifier}")
                print(f"\n✅ code = {code}")

                # Step 4: Exchange code for token
                token_response = requests.post(
                    "https://www.pathofexile.com/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": REDIRECT_URI,
                        "client_id": CLIENT_ID,
                        "code_verifier": _code_verifier,
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Archipelago-PoE",
                    },
                )

                if token_response.ok:
                    tokens = token_response.json()
                    print("\n✅ Access Token:", tokens["access_token"])
                    access_token = tokens["access_token"]
                    token_expire_time = tokens["expires_in"] + time.time()
                    print("⏳ Token expires at:", token_expire_time, "seconds since epoch, or"
                          , token_expire_time - time.time(), "seconds from now")
                    print("🔁 Refresh Token:", tokens.get("refresh_token"))
                else:
                    print("\n❌ Token exchange failed:")
                    print(token_response.text)

                # Shut down server after response
                def shutdown_server(server):
                    server.shutdown()

                import threading
                threading.Thread(target=shutdown_server, args=(self.server,), daemon=True).start()
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"<h1>Error: Missing authorization code</h1>")

async def async_oauth_login() -> dict:
    """
    Async version of oauth_login. Returns a new access_token.
    """
    code_future = asyncio.get_event_loop().create_future()

    class AsyncOAuthHandler(http.server.SimpleHTTPRequestHandler):
        global access_token, token_expire_time

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/oauth-callback":
                params = urllib.parse.parse_qs(parsed.query)
                code = params.get("code", [None])[0]
                if code:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<h1>Authorization successful! You can close this tab.</h1>")
                    if not code_future.done():
                        code_future.set_result(code)
                    def shutdown_server(server):
                        server.shutdown()
                    import threading
                    threading.Thread(target=shutdown_server, args=(self.server,), daemon=True).start()
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"<h1>Error: Missing authorization code</h1>")

    webbrowser.open(_auth_url)
    print(f"🔊 Listening for callback on {REDIRECT_URI} ...")
    server = socketserver.TCPServer(("", PORT), AsyncOAuthHandler)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, server.serve_forever)
    code = await code_future

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.pathofexile.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "code_verifier": _code_verifier,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Archipelago-PoE",
            },
        )
        resp.raise_for_status()
        tokens = resp.json()
        token_expire_time = tokens["expires_in"] + time.time()
        access_token = tokens["access_token"]
        print("\n✅ Access Token:", tokens["access_token"])
        print("⏳ Token expires at:", token_expire_time, "seconds since epoch, or"
              , token_expire_time - time.time(), "seconds from now")

        # return a dict with expire time and access token
        return {
            "access_token": access_token,
            "expires_at": token_expire_time
        }




if __name__ == '__main__':
    # Run the async OAuth login
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(async_oauth_login())
    print("OAuth login result:", result)


## === Step 5: Launch browser and serve ===
#def oauth_login():
#
#    print(f"🌐 Opening browser to log in...")
#    webbrowser.open(_auth_url)
#
#    print(f"🔊 Listening for callback on {REDIRECT_URI} ...")
#    with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
#        httpd.serve_forever()
#
#
#if __name__ == '__main__':
#    oauth_login()