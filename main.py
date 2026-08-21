import json
import os
import sys
import tempfile
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


STATE_FILE = Path("state.json")
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".mpeg", ".mpg", ".ts"}


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"initialized": False, "last_message_id": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"initialized": False, "last_message_id": 0}


def save_state(last_message_id: int) -> None:
    STATE_FILE.write_text(
        json.dumps(
            {"initialized": True, "last_message_id": int(last_message_id)},
            indent=2
        ) + "\n",
        encoding="utf-8",
    )


def get_drive_service():
    creds = Credentials(
        token=None,
        refresh_token=require_env("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=require_env("GOOGLE_CLIENT_ID"),
        client_secret=require_env("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def is_video(message) -> bool:
    if not message.file:
        return False

    mime = (getattr(message.file, "mime_type", "") or "").lower()
    if mime.startswith("video/"):
        return True

    name = (getattr(message.file, "name", "") or "").lower()
    return Path(name).suffix.lower() in VIDEO_EXTENSIONS


def choose_folder(message) -> tuple[str, str]:
    serials_folder = require_env("SERIALS_FOLDER_ID")
    shows_folder = require_env("SHOWS_FOLDER_ID")

    threshold_mb = float(os.getenv("SHOW_SIZE_THRESHOLD_MB", "150"))
    threshold_bytes = int(threshold_mb * 1024 * 1024)

    size = int(getattr(message.file, "size", 0) or 0)
    caption = (message.message or "").lower()

    # Optional explicit override in Telegram caption.
    if "#serial" in caption or "#serials" in caption:
        return serials_folder, "Serials"
    if "#show" in caption or "#shows" in caption:
        return shows_folder, "Shows"

    # Your current pattern:
    # serials ~40-50 MB, shows ~500-800 MB.
    if size >= threshold_bytes:
        return shows_folder, "Shows"
    return serials_folder, "Serials"


def safe_filename(message) -> str:
    original = getattr(message.file, "name", None)
    if original:
        return Path(original).name

    ext = getattr(message.file, "ext", None) or ".mp4"
    return f"telegram_{message.id}{ext}"


def upload_to_drive(service, local_path: str, filename: str, folder_id: str):
    metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaFileUpload(local_path, resumable=True, chunksize=8 * 1024 * 1024)

    request = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,size,webViewLink",
        supportsAllDrives=True,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"Google Drive upload: {pct}%")

    return response


async def main():
    api_id = int(require_env("TELEGRAM_API_ID"))
    api_hash = require_env("TELEGRAM_API_HASH")
    session = require_env("TELEGRAM_SESSION")
    channel_value = require_env("TELEGRAM_CHANNEL")

    # Accept either @username or numeric channel id such as -1001234567890
    try:
        channel = int(channel_value)
    except ValueError:
        channel = channel_value

    state = load_state()

    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        raise RuntimeError("Telegram session is not authorized. Generate a new TELEGRAM_SESSION.")

    entity = await client.get_entity(channel)

    # First run only initializes at the newest existing message.
    # This prevents accidentally uploading the entire historical channel.
    if not state.get("initialized", False):
        latest_id = 0
        async for msg in client.iter_messages(entity, limit=1):
            latest_id = msg.id
        save_state(latest_id)
        print(f"Initialized. Existing messages skipped through ID {latest_id}.")
        print("Now forward a NEW video to the channel; the next run will upload it.")
        await client.disconnect()
        return

    last_id = int(state.get("last_message_id", 0))
    messages = []

    async for msg in client.iter_messages(entity, min_id=last_id, reverse=True):
        messages.append(msg)

    if not messages:
        print("No new Telegram messages.")
        await client.disconnect()
        return

    drive = get_drive_service()
    highest_seen = last_id

    for msg in messages:
        highest_seen = max(highest_seen, msg.id)

        if not is_video(msg):
            print(f"Skipping message {msg.id}: not a video.")
            save_state(highest_seen)
            continue

        filename = safe_filename(msg)
        folder_id, folder_name = choose_folder(msg)
        size_mb = (int(getattr(msg.file, "size", 0) or 0) / 1024 / 1024)

        print(f"Processing message {msg.id}: {filename} ({size_mb:.1f} MB) -> {folder_name}")

        with tempfile.TemporaryDirectory() as tmp:
            target = str(Path(tmp) / filename)
            downloaded = await client.download_media(msg, file=target)
            if not downloaded:
                raise RuntimeError(f"Telegram download failed for message {msg.id}")

            print(f"Downloaded: {downloaded}")
            result = upload_to_drive(drive, downloaded, filename, folder_id)
            print(f"Uploaded to Drive: {result.get('name')} | ID: {result.get('id')}")

        # Save after each successful item so a later failure doesn't re-upload earlier items.
        save_state(highest_seen)

    await client.disconnect()
    print("Done.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
