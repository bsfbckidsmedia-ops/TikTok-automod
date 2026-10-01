import unittest

from automod import AutoModConfig, AutoModerator


class AutoModeratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 100.0
        config = AutoModConfig(
            moderator_usernames=frozenset({"trusted_mod"}),
            trusted_usernames=frozenset({"regular"}),
            blocked_terms=("bad phrase",),
            spam_limit=3,
            spam_window_seconds=10,
            alert_dedupe_seconds=5,
        )
        self.bot = AutoModerator(config, clock=lambda: self.now)

    def test_starts_disabled(self) -> None:
        self.assertIsNone(self.bot.process_message("https://example.com", "viewer"))

    def test_only_configured_moderators_can_toggle(self) -> None:
        ignored = self.bot.process_message("!automod on", "viewer")
        self.assertIn("moderator-only", ignored)
        self.assertFalse(self.bot.enabled)

        enabled = self.bot.process_message("!automod on", "@TRUSTED_MOD")
        self.assertEqual(enabled, "COMMAND: AutoMod alerts enabled.")
        self.assertTrue(self.bot.enabled)

    def test_status_and_off_commands(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        self.assertEqual(
            self.bot.process_message("!automod status", "trusted_mod"),
            "COMMAND: AutoMod alerts are on.",
        )
        self.bot.process_message("!automod off", "trusted_mod")
        self.assertFalse(self.bot.enabled)

    def test_detects_links_and_blocked_phrases_case_insensitively(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        result = self.bot.process_message(
            "BAD phrase! visit https://example.com", "viewer"
        )
        self.assertIn("ACTION NEEDED", result)
        self.assertIn("HIGH SEVERITY", result)
        self.assertIn("User: @viewer", result)
        self.assertIn("link", result)
        self.assertIn("blocked term", result)
        self.assertIn("manually delete or mute", result)

    def test_links_have_medium_severity(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        result = self.bot.process_message("visit https://example.com", "viewer")
        self.assertIn("MEDIUM SEVERITY", result)

    def test_detects_repeated_messages_within_window(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        self.assertIsNone(self.bot.process_message("join our group", "viewer"))
        self.now += 1
        self.assertIsNone(self.bot.process_message("JOIN OUR GROUP", "viewer"))
        self.now += 1
        result = self.bot.process_message("join our group", "viewer")
        self.assertIn("repeated message", result)
        self.assertIn("LOW SEVERITY", result)

    def test_suppresses_repeated_alerts_and_reports_suppressed_count(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        self.assertIsNone(self.bot.process_message("same message", "viewer"))
        self.assertIsNone(self.bot.process_message("same message", "viewer"))
        first_alert = self.bot.process_message("same message", "viewer")
        self.assertIn("LOW SEVERITY", first_alert)

        self.now += 1
        self.assertIsNone(self.bot.process_message("same message", "viewer"))
        self.now = 106
        next_alert = self.bot.process_message("same message", "viewer")
        self.assertIn("Additional matching messages since the previous alert: 1", next_alert)

    def test_spam_threshold_can_be_tuned(self) -> None:
        tuned_bot = AutoModerator(
            AutoModConfig(
                moderator_usernames=frozenset({"trusted_mod"}),
                spam_limit=2,
            ),
            clock=lambda: self.now,
        )
        tuned_bot.process_message("!automod on", "trusted_mod")
        self.assertIsNone(tuned_bot.process_message("same", "viewer"))
        alert = tuned_bot.process_message("same", "viewer")
        self.assertIn("LOW SEVERITY", alert)

    def test_trusted_user_and_moderators_are_exempt_from_alerts(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        for trusted_user in ("regular", "@TRUSTED_MOD"):
            self.assertIsNone(
                self.bot.process_message("https://example.com bad phrase", trusted_user)
            )

    def test_old_repetitions_expire(self) -> None:
        self.bot.process_message("!automod on", "trusted_mod")
        self.bot.process_message("same", "viewer")
        self.now += 11
        self.bot.process_message("same", "viewer")
        self.now += 1
        self.assertIsNone(self.bot.process_message("same", "viewer"))


if __name__ == "__main__":
    unittest.main()
