# TikTok VR AutoMod Setup Guide

This guide walks through installing and running the alert-only TikTok LIVE
AutoMod.

## Before you start

You will need:

- A computer that can stay on while the stream is live.
- Python 3.10 or later installed.
- This project folder on that computer.
- The TikTok username of the account whose LIVE chat you want to watch.
- The TikTok usernames of the moderators allowed to switch alerts on and off.

The bot connects to a public LIVE using an unofficial, read-only integration.
It does not need your TikTok password, session cookie, or access token. It
cannot delete comments, mute or ban users, or post messages to chat. Alerts are
printed only in the terminal running the bot.

## 1. Open a terminal in the project folder

Open Terminal (macOS/Linux) or PowerShell (Windows), then change to the folder
containing `main.py`, `automod.py`, and `requirements.txt`.

For example, on macOS:

```sh
cd ~/CascadeProjects/tiktok-vr-automod
```

Use the actual location of the project if it is somewhere else. If you received
the project as a ZIP file, extract it first, then open a terminal in the
extracted `tiktok-vr-automod` folder.

## 2. Create a virtual environment

A virtual environment keeps this bot's Python packages separate from other
projects.

**macOS/Linux**

```sh
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell says script execution is disabled, use Command Prompt and run:

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

When the environment is active, the terminal prompt usually starts with
`(.venv)`. If `python3` or `py -3` is not found, install Python 3.10 or later
and try again.

## 3. Install the dependencies

With the virtual environment active, run:

```sh
python -m pip install -r requirements.txt
```

Wait for the command to finish before continuing.

## 4. Create and edit your settings

Copy the example settings file:

**macOS/Linux**

```sh
cp .env.example .env
```

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

Open `.env` in a text editor and replace the example values:

```dotenv
TIKTOK_LIVE_USERNAME=your_live_account
TIKTOK_MODERATOR_USERNAMES=your_mod_handle,another_mod
AUTOMOD_TRUSTED_USERNAMES=trusted_regular,another_trusted_user

AUTOMOD_BLOCKED_TERMS=
AUTOMOD_DETECT_LINKS=true
AUTOMOD_DETECT_REPEATED_MESSAGES=true
AUTOMOD_SPAM_LIMIT=3
AUTOMOD_SPAM_WINDOW_SECONDS=30
AUTOMOD_ALERT_DEDUPE_SECONDS=60
```

Configure the values as follows:

- `TIKTOK_LIVE_USERNAME`: the handle of the account that will be live. Do not
  include the `@`.
- `TIKTOK_MODERATOR_USERNAMES`: comma-separated TikTok handles permitted to
  use the `!automod` commands. Do not include `@`. Use each moderator's
  username/handle, not their display name.
- `AUTOMOD_TRUSTED_USERNAMES`: optional comma-separated handles exempt from
  content alerts. Configured moderators are exempt automatically. Do not
  include `@`.
- `AUTOMOD_BLOCKED_TERMS`: optional comma-separated words or phrases to flag.
  Leave empty to disable this rule. Terms are matched without regard to
  capitalization and as whole words/phrases.
- `AUTOMOD_DETECT_LINKS`: set to `true` to flag messages containing `http://`,
  `https://`, or `www.`; set to `false` to turn this rule off.
- `AUTOMOD_DETECT_REPEATED_MESSAGES`: set to `true` to flag the same user
  posting the same message repeatedly; set to `false` to turn this rule off.
- `AUTOMOD_SPAM_LIMIT`: how many matching messages from one user trigger an
  alert. The default is `3`.
- `AUTOMOD_SPAM_WINDOW_SECONDS`: the time period in which those messages count.
  The default is `30` seconds.
- `AUTOMOD_ALERT_DEDUPE_SECONDS`: suppress repeat alerts for the same user and
  matched rules during this many seconds. The default is `60`. When another
  alert is eventually emitted, it reports how many matching alerts were
  suppressed in the previous window.

Alerts have a severity label to help moderators prioritize review:

- **HIGH** — configured blocked term matched.
- **MEDIUM** — a link matched.
- **LOW** — repeated identical message matched.

If multiple rules match, the alert shows the highest matching severity. These
labels are prioritization hints, not judgments; review the message before
taking action.

Do not add TikTok passwords, cookies, or tokens to `.env`. Keep `.env` private;
it is excluded from version control by the project's `.gitignore`.

## 5. Start the bot

Make sure the virtual environment is active, then run:

```sh
python main.py
```

Leave this terminal open. The bot must be running on a computer with an
internet connection while the stream is live. It listens to the configured
account's LIVE; it does not start or broadcast a stream for you.

## 6. Turn AutoMod alerts on from LIVE chat

Alerts start **off** each time the program starts. Once the bot is running and
connected to the LIVE chat, one of the configured moderators can enter one of
these commands in TikTok chat:

- `!automod on` — enable alert checks.
- `!automod off` — disable alert checks.
- `!automod status` — check whether alert checks are enabled.

The command sender must match a handle in `TIKTOK_MODERATOR_USERNAMES`. The bot
does not reply in TikTok chat. Look at the terminal where you started it:
commands and alerts are logged there. Press `Ctrl+C` in that terminal to stop
the bot.

An alert identifies the account, severity, matched rules, and a shortened copy
of the message, and tells you to review it in TikTok. Repeat alerts for the
same user and rule set are deduplicated for the configured interval. Alerts
are advisory; manually delete or mute only if appropriate.

## Troubleshooting

### “Set TIKTOK_LIVE_USERNAME…” or “Set TIKTOK_MODERATOR_USERNAMES…”

Check that `.env` exists in the same folder as `main.py`, and that the
username settings are filled in. Restart the bot after changing `.env`.

### “Dependencies are missing” or `No module named ...`

Activate the virtual environment in the terminal, then run:

```sh
python -m pip install -r requirements.txt
```

### The bot starts but no chat is received

- Confirm the configured account is currently broadcasting a public TikTok
  LIVE.
- Check that `TIKTOK_LIVE_USERNAME` is the stream host's handle, not a
  moderator's handle.
- Check the terminal for connection errors and confirm the computer has
  internet access.
- The unofficial LIVE connection may be unavailable or may stop working when
  TikTok changes its service. This bot does not use an official TikTok LIVE
  chat API.

### The chat command does not enable alerts

- Confirm the command is being sent in the configured account's LIVE chat.
- Make sure the sender's TikTok handle is included in
  `TIKTOK_MODERATOR_USERNAMES`; display names are not used for authorization.
- Check the terminal for a `COMMAND` log message. The bot does not send a
  confirmation back into chat.

### A message did not trigger an alert

Check that alerts are on with `!automod status`. Also check that the relevant
rule is enabled in `.env`, then restart the bot to load changed settings.
Blocked phrases are optional and comma-separated; links are detected by
`http://`, `https://`, or `www.`.

If alerts from a specific account are being ignored, check whether its handle
is listed in `AUTOMOD_TRUSTED_USERNAMES` or `TIKTOK_MODERATOR_USERNAMES`.

## Important limitations

- This is an unofficial integration and may break without notice. Use it only
  if you accept that reliability and account-policy risk.
- It only prints local alerts. It does not automatically remove content or
  punish users.
- The third-party APIs reviewed for this MVP document LIVE chat reading and
  sending, but no supported delete-comment or mute-user action. See
  [TikTool's API docs](https://tik.tools/docs) and the
  [TikTokLive client](https://github.com/isaackogan/TikTokLive).
- Phrase and spam rules can produce false positives or miss harmful content.
  Human review is required.
- Alert enablement is temporary and resets to off whenever the bot restarts.
