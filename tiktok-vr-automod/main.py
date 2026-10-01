"""Entry point for the TikTok LIVE alert-only automod."""

import logging
import os
import sys

from automod import AutoModConfig, AutoModerator, normalize_username


def load_config() -> tuple[str, AutoModConfig]:
    live_username = os.getenv("TIKTOK_LIVE_USERNAME", "").strip().lstrip("@")
    if not live_username:
        raise ValueError("Set TIKTOK_LIVE_USERNAME in your .env file.")

    moderators = frozenset(
        normalize_username(name)
        for name in os.getenv("TIKTOK_MODERATOR_USERNAMES", "").split(",")
        if name.strip()
    )
    if not moderators:
        raise ValueError(
            "Set TIKTOK_MODERATOR_USERNAMES to one or more comma-separated handles."
        )

    trusted_users = frozenset(
        normalize_username(name)
        for name in os.getenv("AUTOMOD_TRUSTED_USERNAMES", "").split(",")
        if name.strip()
    )
    blocked_terms = tuple(
        term.strip()
        for term in os.getenv("AUTOMOD_BLOCKED_TERMS", "").split(",")
        if term.strip()
    )
    spam_limit = int(os.getenv("AUTOMOD_SPAM_LIMIT", "3"))
    spam_window = float(os.getenv("AUTOMOD_SPAM_WINDOW_SECONDS", "30"))
    alert_dedupe = float(os.getenv("AUTOMOD_ALERT_DEDUPE_SECONDS", "60"))

    return live_username, AutoModConfig(
        moderator_usernames=moderators,
        trusted_usernames=trusted_users,
        blocked_terms=blocked_terms,
        detect_links=os.getenv("AUTOMOD_DETECT_LINKS", "true").casefold()
        in {"1", "true", "yes", "on"},
        detect_repeated_messages=os.getenv(
            "AUTOMOD_DETECT_REPEATED_MESSAGES", "true"
        ).casefold()
        in {"1", "true", "yes", "on"},
        spam_limit=spam_limit,
        spam_window_seconds=spam_window,
        alert_dedupe_seconds=alert_dedupe,
    )


def main() -> None:
    try:
        from dotenv import load_dotenv
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import CommentEvent
    except ImportError as exc:
        raise RuntimeError(
            "Dependencies are missing. Install them with: "
            f"{sys.executable} -m pip install -r requirements.txt"
        ) from exc

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logger = logging.getLogger("tiktok_vr_automod")

    live_username, config = load_config()
    automod = AutoModerator(config)
    client = TikTokLiveClient(unique_id=f"@{live_username}")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent) -> None:
        username = getattr(event.user, "unique_id", None) or event.user.nickname
        result = automod.process_message(event.comment, username)
        if result:
            if result.startswith("AUTOMOD ALERT:"):
                logger.warning("%s", result)
            else:
                logger.info("%s (from @%s)", result, username)

    logger.info("Listening to TikTok LIVE for @%s.", live_username)
    logger.info(
        "Alerts start disabled. A configured moderator can enable them with !automod on."
    )
    logger.info("This MVP reports violations locally; it does not delete or mute users.")
    client.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down.")
