"""
Run this ON YOUR PC, not on GitHub.

1. Put the OAuth Desktop App JSON you downloaded from Google Cloud
   in this folder and rename it to: client_secret.json
2. Run:
       pip install google-auth-oauthlib
       python generate_google_refresh_token.py
3. A Google sign-in page will open.
4. Sign in to the Google account that owns the destination Drive folders.
5. The script will print:
       GOOGLE_CLIENT_ID
       GOOGLE_CLIENT_SECRET
       GOOGLE_REFRESH_TOKEN
6. Put those values in GitHub Repository Secrets.
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_FILE = Path("client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]

if not CLIENT_FILE.exists():
    raise SystemExit("client_secret.json not found. Put it beside this script.")

data = json.loads(CLIENT_FILE.read_text(encoding="utf-8"))
section = data.get("installed") or data.get("web")
if not section:
    raise SystemExit("This does not look like a Google OAuth client JSON file.")

flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\nSAVE THESE AS GITHUB SECRETS:\n")
print("GOOGLE_CLIENT_ID=" + section["client_id"])
print("GOOGLE_CLIENT_SECRET=" + section["client_secret"])
print("GOOGLE_REFRESH_TOKEN=" + str(creds.refresh_token))
print("\nDo not post these values publicly.")
