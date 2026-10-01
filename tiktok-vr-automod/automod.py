"""Chat command handling and alert-only moderation rules."""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional


LINK_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def normalize_username(username: str) -> str:
    return username.strip().removeprefix("@").casefold()


@dataclass(frozen=True)
class AutoModConfig:
    moderator_usernames: frozenset[str]
    trusted_usernames: frozenset[str] = frozenset()
    blocked_terms: tuple[str, ...] = ()
    detect_links: bool = True
    detect_repeated_messages: bool = True
    spam_limit: int = 3
    spam_window_seconds: float = 30.0
    alert_dedupe_seconds: float = 60.0


class AutoModerator:
    def __init__(
        self,
        config: AutoModConfig,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not config.moderator_usernames:
            raise ValueError("At least one moderator username must be configured.")
        if config.spam_limit < 2:
            raise ValueError("spam_limit must be at least 2.")
        if config.spam_window_seconds <= 0:
            raise ValueError("spam_window_seconds must be greater than 0.")
        if config.alert_dedupe_seconds <= 0:
            raise ValueError("alert_dedupe_seconds must be greater than 0.")

        self.config = config
        self._clock = clock
        self.enabled = False
        self._moderators = frozenset(
            normalize_username(name) for name in config.moderator_usernames
        )
        self._trusted_users = self._moderators | frozenset(
            normalize_username(name) for name in config.trusted_usernames
        )
        self._term_patterns = tuple(
            re.compile(
                r"(?<!\w)" + re.escape(term).replace(r"\ ", r"\s+") + r"(?!\w)",
                re.IGNORECASE,
            )
            for term in config.blocked_terms
            if term.strip()
        )
        self._recent_messages: dict[str, Deque[tuple[float, str]]] = defaultdict(deque)
        self._recent_alerts: dict[tuple[str, tuple[str, ...]], tuple[float, int]] = {}

    def process_message(self, message: str, sender_username: str) -> Optional[str]:
        text = message.strip()
        if not text:
            return None

        words = text.split()
        if words and words[0].casefold() == "!automod":
            return self._handle_command(words[1:], sender_username)

        if not self.enabled:
            return None

        sender = normalize_username(sender_username)
        if sender in self._trusted_users:
            return None

        reasons: list[str] = []
        if self.config.detect_links and LINK_PATTERN.search(text):
            reasons.append("link")
        if any(pattern.search(text) for pattern in self._term_patterns):
            reasons.append("blocked term")
        if self.config.detect_repeated_messages and self._is_repeated(
            text, sender_username
        ):
            reasons.append("repeated message")

        if not reasons:
            return None

        now = self._clock()
        alert_key = (sender, tuple(sorted(reasons)))
        previous_alert = self._recent_alerts.get(alert_key)
        suppressed_count = 0
        if (
            previous_alert
            and now - previous_alert[0] < self.config.alert_dedupe_seconds
        ):
            self._recent_alerts[alert_key] = (
                previous_alert[0],
                previous_alert[1] + 1,
            )
            return None

        if previous_alert:
            suppressed_count = previous_alert[1]
        self._recent_alerts[alert_key] = (now, 0)
        self._recent_alerts = {
            key: alert
            for key, alert in self._recent_alerts.items()
            if key == alert_key
            or now - alert[0] < self.config.alert_dedupe_seconds
        }

        display_name = sender_username.strip().lstrip("@") or "unknown"
        safe_text = " ".join(text.split())[:240]
        severity = self._severity_for(reasons)
        summary = (
            f"Additional matching messages since the previous alert: {suppressed_count}\n"
            if suppressed_count
            else None
        )
        return (
            f"AUTOMOD ALERT: ACTION NEEDED - {severity} SEVERITY\n"
            f"User: @{display_name}\n"
            f"Matched rules: {', '.join(reasons)}\n"
            f"Message: {safe_text!r}\n"
            f"{summary or ''}"
            "Next step: Review in TikTok LIVE and manually delete or mute "
            "if appropriate."
        )

    @staticmethod
    def _severity_for(reasons: list[str]) -> str:
        severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        rule_severity = {
            "repeated message": "LOW",
            "link": "MEDIUM",
            "blocked term": "HIGH",
        }
        return max(
            (rule_severity[reason] for reason in reasons),
            key=severity_rank.__getitem__,
        )

    def _handle_command(self, arguments: list[str], sender_username: str) -> str:
        sender = normalize_username(sender_username)
        if sender not in self._moderators:
            return "COMMAND IGNORED: !automod commands are moderator-only."

        command = arguments[0].casefold() if arguments else "help"
        if command == "on" and len(arguments) == 1:
            self.enabled = True
            return "COMMAND: AutoMod alerts enabled."
        if command == "off" and len(arguments) == 1:
            self.enabled = False
            return "COMMAND: AutoMod alerts disabled."
        if command == "status" and len(arguments) == 1:
            state = "on" if self.enabled else "off"
            return f"COMMAND: AutoMod alerts are {state}."
        return "COMMAND: Use !automod on, !automod off, or !automod status."

    def _is_repeated(self, message: str, sender_username: str) -> bool:
        now = self._clock()
        sender = normalize_username(sender_username)
        normalized_message = " ".join(message.casefold().split())
        history = self._recent_messages[sender]
        cutoff = now - self.config.spam_window_seconds

        while history and history[0][0] < cutoff:
            history.popleft()

        history.append((now, normalized_message))
        return (
            sum(previous == normalized_message for _, previous in history)
            >= self.config.spam_limit
        )
