# Telegram Drive Uploader

Uploads NEW videos from one Telegram channel to Google Drive automatically using GitHub Actions.

## Routing

Default routing is based on file size:

- **Below 150 MB** -> `Serials`
- **150 MB or larger** -> `Shows`

You can override the destination in a Telegram caption:

- `#serial` or `#serials` -> Serials
- `#show` or `#shows` -> Shows

This matches the intended use case where serials are around 40-50 MB and shows are around 500-800 MB.

## Required GitHub Repository Secrets

Repository -> Settings -> Secrets and variables -> Actions -> New repository secret.

Create these secrets:

### Telegram

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION`
- `TELEGRAM_CHANNEL`

`TELEGRAM_CHANNEL` can be:
- `@your_channel_username` for a public channel, OR
- a numeric channel id such as `-1001234567890`

### Google Drive

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `SERIALS_FOLDER_ID`
- `SHOWS_FOLDER_ID`

## Generate Telegram session

On your PC:

```bash
pip install telethon
python tools/generate_telegram_session.py
```

Never share the session string.

## Generate Google refresh token

Put your downloaded Google OAuth Desktop App JSON beside the helper script and rename it:

```text
tools/client_secret.json
```

Then:

```bash
pip install google-auth-oauthlib
cd tools
python generate_google_refresh_token.py
```

If Google Cloud OAuth is in Testing mode, add your own Google account under **OAuth consent screen -> Audience -> Test users** first.

## First run

The first run intentionally does NOT upload old channel history.

Go to:

**GitHub -> Actions -> Telegram to Google Drive -> Run workflow**

The workflow records the latest current Telegram message.

After that first run finishes, forward a NEW video into the channel.

The scheduled workflow checks automatically every 5 minutes. GitHub scheduled jobs can sometimes start later than the exact 5-minute mark.

## Important

- The normal BotFather bot token is **not used** by this version.
- This project uses your Telegram user session via Telethon so it can handle files larger than the Bot API's normal download limit.
- GitHub runners are temporary. Videos are downloaded only during the workflow and then removed.
- `state.json` is automatically updated and committed so the same video is not uploaded again.
- Keep the repository free of credentials. Put secrets only in GitHub Actions Secrets.
