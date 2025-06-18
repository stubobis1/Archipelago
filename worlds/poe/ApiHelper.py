import http.server
import socketserver
import urllib.parse
import webbrowser
import base64
import hashlib
import os
import requests

# === CONFIG ===
CLIENT_ID = "archipelagopoe"
REDIRECT_URI = "http://127.0.0.1:8234/oauth-callback"
SCOPES = "account:profile account:characters account:stashes account:leagues"
PORT = 8234

# === Step 1: Generate PKCE pair ===
code_verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b'=').decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()

# === Step 2: Build Auth URL ===
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
    "state": "mystate",
    "code_challenge": code_challenge,
    "code_challenge_method": "S256",
}
auth_url = f"https://www.pathofexile.com/oauth/authorize?{urllib.parse.urlencode(params)}"

# === Step 3: Start local callback server ===
class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
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
                print(f"\n🔑 code_verifier = {code_verifier}")
                print(f"\n✅ code = {code}")

                print("\n📋 Paste this curl command to exchange your code for a token:\n")
                print(f"""
                curl -X POST https://www.pathofexile.com/oauth/token \\
                  -H \"Content-Type: application/x-www-form-urlencoded\" \\
                  -d \"grant_type=authorization_code\" \\
                  -d \"code={code}\" \\
                  -d \"client_id={CLIENT_ID}\" \\
                  -d \"redirect_uri={REDIRECT_URI}\" \\
                  -d \"code_verifier={code_verifier}\" 
                """)


                # Step 4: Exchange code for token
                token_response = requests.post(
                    "https://www.pathofexile.com/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": REDIRECT_URI,
                        "client_id": CLIENT_ID,
                        "code_verifier": code_verifier,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if token_response.ok:
                    tokens = token_response.json()
                    print("\n✅ Access Token:", tokens["access_token"])
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

# === Step 5: Launch browser and serve ===
print(f"🌐 Opening browser to log in...")
webbrowser.open(auth_url)

print(f"🔊 Listening for callback on {REDIRECT_URI} ...")
with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
    httpd.serve_forever()