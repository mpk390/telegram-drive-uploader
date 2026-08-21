"""
Optional helper: find the numeric ID of your Telegram channel.

Set these environment variables first:
  TELEGRAM_API_ID
  TELEGRAM_API_HASH
  TELEGRAM_SESSION

Then run:
  python list_telegram_channels.py
"""

import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel

api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
session = os.environ["TELEGRAM_SESSION"]

with TelegramClient(StringSession(session), api_id, api_hash) as client:
    for dialog in client.iter_dialogs():
        ent = dialog.entity
        if isinstance(ent, Channel):
            print(f"{dialog.name} | ID: {ent.id} | GitHub secret value: -100{ent.id}")
