"""
Run this ON YOUR PC.

Usage:
    pip install telethon
    python generate_telegram_session.py

It asks for:
- Telegram API ID
- Telegram API Hash
- Your phone number
- Telegram login code
- 2-step verification password, if enabled

It prints TELEGRAM_SESSION. Keep it private.
"""

from getpass import getpass
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("Telegram API ID: ").strip())
api_hash = getpass("Telegram API Hash: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nTELEGRAM_SESSION:\n")
    print(client.session.save())
    print("\nKeep this secret. Do not paste it into README or source code.")
