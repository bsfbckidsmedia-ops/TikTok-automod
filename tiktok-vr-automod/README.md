# TikTok VR Stream AutoMod (alert-only MVP)

A small Python bot for monitoring a TikTok LIVE chat. It can be switched on or
off with moderator-only chat commands and reports likely rule violations to
the terminal running the bot.

This is an unofficial, read-only chat integration. TikTok's public developer
API does not provide a supported LIVE chat moderation endpoint. This MVP does
not delete comments, mute users, ban users, or send replies into TikTok chat.

## Requirements

- Python 3.10 or later
- A public TikTok LIVE stream
- The TikTok handle used for the stream
- TikTok moderator handles authorized to operate the bot

## Quick setup

```sh
cd path/to/tiktok-vr-automod
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with the stream account and moderator handles. For Windows
PowerShell setup commands, configuration details, troubleshooting, and the
full walkthrough, see the [setup guide](./SETUP_GUIDE.md).

Alerts include severity labels (blocked terms: HIGH, links: MEDIUM, repeated
messages: LOW). Repeated alerts for the same user and matched rules are
suppressed for 60 seconds by default. Moderators and usernames in
`AUTOMOD_TRUSTED_USERNAMES` are exempt from content alerts. Tune the rules and
thresholds in `.env`.

Start the listener:

```sh
python main.py
```

AutoMod starts disabled. A configured moderator can enter these in LIVE chat:

- `!automod on` — enable local violation alerts
- `!automod off` — disable alerts
- `!automod status` — report whether alerts are enabled

Commands and alerts appear in the bot's terminal; the bot does not post a
response in TikTok chat. The stream must be live for the listener to connect.

## Safety and limitations

- The TikTok LIVE listener is unofficial and may break when TikTok changes its
  service. Use it only if you accept that reliability and account-policy risk.
- The bot does not need TikTok passwords, session cookies, or access tokens.
  Never add those credentials to `.env`.
- Alerts are advisory. A human moderator must take any action in TikTok.
- Blocked-term rules are configurable and can produce false positives; review
  alerts before acting.
- The third-party APIs reviewed for this MVP document LIVE chat reading and
  sending, but no supported delete-comment or mute-user action. See
  [TikTool's API docs](https://tik.tools/docs) and the
  [TikTokLive client](https://github.com/isaackogan/TikTokLive).

## Tests

```sh
python -m unittest
```
