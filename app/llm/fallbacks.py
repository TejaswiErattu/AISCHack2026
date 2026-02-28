"""Template fallbacks used when the LLM is unavailable or returns an error.

Every public method returns a pre-formatted string that can be sent directly
to the user through Telegram without any LLM involvement.
"""

from app.models.schemas import OnboardingStep


class FallbackTemplates:
    """Static methods that produce deterministic user-facing messages."""

    @staticmethod
    def rate_alert(
        recipient_amount: float,
        personal_baseline_amount: float,
        pct_change: float,
        currency: str,
    ) -> str:
        """Full rate-alert message with baseline comparison.

        Sent as the first alert when a favorable window is detected.
        """
        change_amount = recipient_amount - personal_baseline_amount
        direction = "more" if change_amount >= 0 else "less"
        return (
            f"Good news! Now is a good time to send money.\n\n"
            f"Recipient gets: {recipient_amount:,.2f} {currency}\n"
            f"vs your 14-day average: {change_amount:+,.2f} {currency} "
            f"({pct_change:+.1f}%) -- {abs(change_amount):,.2f} {currency} "
            f"{direction} than usual.\n\n"
            f"Reply CONFIRM to send, WAIT to keep monitoring, "
            f"or 'details' for a full breakdown."
        )

    @staticmethod
    def short_followup(
        recipient_amount: float,
        pct_change: float,
        currency: str,
    ) -> str:
        """Short follow-up alert for subsequent notifications in the same window."""
        return (
            f"Still a good time to send.\n"
            f"Recipient amount: {recipient_amount:,.2f} {currency} "
            f"({pct_change:+.1f}%)\n"
            f"Reply 'details' for full breakdown."
        )

    @staticmethod
    def onboarding_question(step: str | OnboardingStep) -> str:
        """Return the default question for the given onboarding step.

        Accepts either a string value or an ``OnboardingStep`` enum member.
        """
        if isinstance(step, OnboardingStep):
            step = step.value

        questions = {
            "language": (
                "Welcome to RemitAgent! I help you send money internationally "
                "at the best possible rate.\n\n"
                "What language would you like me to use?\n"
                "(e.g. English, Spanish, Hindi, French, Tagalog)"
            ),
            "literacy": (
                "How much do you know about exchange rates and "
                "international transfers?\n\n"
                "1. Beginner -- just tell me the simple version\n"
                "2. Intermediate -- I understand rates and fees\n"
                "3. Advanced -- give me all the technical details"
            ),
            "sender_country": (
                "Which country will you be sending money FROM?\n"
                "(e.g. United States, United Kingdom, UAE)"
            ),
            "recipient_country": (
                "Which country will your recipient be in?\n"
                "(e.g. India, Philippines, Mexico)"
            ),
            "amount": (
                "How much do you typically send each time? "
                "Please include the currency.\n"
                "(e.g. $500, 300 GBP)"
            ),
            "confirm": (
                "Here is your profile summary. "
                "Does everything look correct?\n"
                "Reply YES to confirm or tell me what to change."
            ),
            "complete": (
                "You're all set! I'm now monitoring exchange rates for "
                "your corridor.\n"
                "I'll notify you when conditions are favorable to send."
            ),
        }

        return questions.get(
            step,
            "Could you provide a bit more information so I can continue?",
        )

    @staticmethod
    def transfer_confirmation(
        transfer_id: str,
        amount: float,
        currency: str,
        status: str,
    ) -> str:
        """Transfer status message shown after execution or status check."""
        status_display = status.replace("_", " ").title()
        return (
            f"Transfer update:\n\n"
            f"Transfer ID: {transfer_id}\n"
            f"Amount: {amount:,.2f} {currency}\n"
            f"Status: {status_display}\n\n"
            f"I'll keep you updated as the status changes."
        )

    @staticmethod
    def profile_summary(profile_dict: dict) -> str:
        """Summarize a user profile for onboarding confirmation.

        Expects a dict with keys like language, sender_country,
        recipient_country, average_amount, and financial_literacy_level.
        """
        language = profile_dict.get("language", "English")
        sender = profile_dict.get("sender_country", "Not set")
        recipient = profile_dict.get("recipient_country", "Not set")
        amount = profile_dict.get("average_amount", 0.0)
        literacy = profile_dict.get("financial_literacy_level", "beginner")

        lines = [
            "Here is your profile:",
            "",
            f"  Language: {language}",
            f"  Sending from: {sender}",
            f"  Sending to: {recipient}",
            f"  Typical amount: {amount:,.2f}",
            f"  Explanation level: {literacy.title()}",
            "",
            "Does this look right? Reply YES to confirm or tell me what to change.",
        ]
        return "\n".join(lines)
