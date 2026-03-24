"""
Telegram Notifier
Sends real-time event notifications to your Telegram bot.

Setup:
  1. Message @BotFather on Telegram → /newbot → get BOT_TOKEN
  2. Message your bot once, then visit:
     https://api.telegram.org/bot<TOKEN>/getUpdates
     Copy your chat_id from the response
  3. Fill both values in config/schedule.json under "telegram"

Events notified:
  🟢 Joined class
  ✅ Attendance marked (Present sent)
  🔵 Burst detected (mass Present in chat)
  📢 Roll call — name detected in captions
  🔴 Left class
  📋 Class taken summary
  🏁 Class ended by host
  ⚠️  Reconnecting / error
  📅 Day summary (next class reminder)
"""

import requests
import threading
from datetime import datetime
from typing import Optional, Dict
from zoneinfo import ZoneInfo

PKT = ZoneInfo("Asia/Karachi")


class TelegramNotifier:
    def __init__(self, config: Dict):
        tg = config.get("telegram", {})
        self.enabled: bool = tg.get("enabled", False)
        self.token: str = tg.get("bot_token", "")
        self.chat_id: str = str(tg.get("chat_id", ""))
        self.student_name: str = config["student"]["name"]
        self._base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    # ──────────────────────────────────────────────
    # Public event methods
    # ──────────────────────────────────────────────

    def joined(self, cls: Dict):
        """Bot joined a class meeting."""
        now = self._now()
        emoji = "🧪" if cls.get("is_lab") else "📚"
        self._send(
            f"{emoji} *Joined Class*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🏫 Room: `{cls.get('room', 'N/A')}`\n"
            f"📅 Day: `{cls['day']}`\n"
            f"🕐 Joined at: `{now}`\n"
            f"⏳ Duration: `{cls['duration']} min`\n"
            f"🔗 Platform: `{cls['platform'].upper()}`"
        )

    def attendance_marked(self, cls: Dict, trigger: str):
        """Bot sent 'Present' in chat."""
        now = self._now()
        self._send(
            f"✅ *Attendance Marked!*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Time: `{now}`\n"
            f"🎯 Trigger: `{trigger}`\n"
            f"💬 Sent: `Present`"
        )

    def burst_detected(self, cls: Dict, count: int):
        """Mass 'present' burst detected in chat."""
        now = self._now()
        self._send(
            f"🔵 *Burst Detected*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Time: `{now}`\n"
            f"📊 Present messages: `{count}` in 3 seconds\n"
            f"🔍 Checking captions for your name..."
        )

    def name_detected(self, cls: Dict, detected_name: str, context: str):
        """Student name found in captions."""
        now = self._now()
        self._send(
            f"📢 *Name Detected in Captions*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Time: `{now}`\n"
            f"🎙️ Detected: `{detected_name}`\n"
            f"📝 Context: `{context[:80]}...`"
        )

    def roll_call_detected(self, cls: Dict):
        """Teacher is calling attendance roll."""
        now = self._now()
        self._send(
            f"📋 *Roll Call Detected!*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Time: `{now}`\n"
            f"🎙️ Teacher is marking attendance\n"
            f"👀 Watching for your name..."
        )

    def mic_kharab_sent(self, cls: Dict):
        """Bot sent 'Mic kharab hai' for question context."""
        now = self._now()
        self._send(
            f"🎤 *Question Detected*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Time: `{now}`\n"
            f"💬 Sent: `Mic kharab hai`\n"
            f"ℹ️ Teacher asked a question"
        )

    def left(self, cls: Dict, reason: str):
        """Bot left the meeting."""
        now = self._now()
        reason_map = {
            "host_ended": "Host ended the meeting",
            "end_time":   "Class end time reached",
            "manual":     "Manual stop",
            "error":      "Error / crash",
        }
        self._send(
            f"🔴 *Left Class*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Left at: `{now}`\n"
            f"📌 Reason: `{reason_map.get(reason, reason)}`"
        )

    def class_summary(self, cls: Dict, attendance_marked: bool, duration_in_secs: int):
        """End-of-class summary."""
        mins = duration_in_secs // 60
        status = "✅ Present marked" if attendance_marked else "⚠️ Not marked"
        self._send(
            f"📋 *Class Summary*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🏫 Room: `{cls.get('room', 'N/A')}`\n"
            f"⏱️ Time in class: `{mins} min`\n"
            f"🎯 Attendance: {status}"
        )

    def class_ended_by_host(self, cls: Dict):
        """Host ended the meeting."""
        now = self._now()
        self._send(
            f"🏁 *Class Ended by Host*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🕐 Time: `{now}`"
        )

    def reconnecting(self, cls: Dict, attempt: int, max_attempts: int):
        """Bot is reconnecting after a drop."""
        self._send(
            f"⚠️ *Reconnecting...*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🔄 Attempt: `{attempt}/{max_attempts}`\n"
            f"🌐 Checking internet..."
        )

    def error(self, cls: Optional[Dict], message: str):
        """Generic error notification."""
        subject = cls['subject'] if cls else "Unknown"
        self._send(
            f"❌ *Bot Error*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{subject}`\n"
            f"💥 Error: `{message[:200]}`"
        )

    def next_class_reminder(self, cls: Dict, minutes_until: int):
        """Upcoming class reminder."""
        emoji = "🧪" if cls.get("is_lab") else "📚"
        self._send(
            f"{emoji} *Upcoming Class*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📖 Subject: `{cls['subject']}`\n"
            f"🏫 Room: `{cls.get('room', 'N/A')}`\n"
            f"⏰ Starting in: `{minutes_until} minutes`\n"
            f"🔗 Platform: `{cls['platform'].upper()}`"
        )

    def day_summary(self, classes_today: list):
        """Morning summary of today's classes."""
        if not classes_today:
            self._send("📅 *No classes today.* Enjoy your day! 🎉")
            return

        lines = ["📅 *Today's Schedule*", "━━━━━━━━━━━━━━━━"]
        for cls in classes_today:
            lab_tag = " 🧪" if cls.get("is_lab") else ""
            lines.append(
                f"• `{cls['time']}` — *{cls['subject']}*{lab_tag} "
                f"({cls.get('room', '')})"
            )
        lines.append(f"\n📊 Total: `{len(classes_today)}` classes")
        self._send("\n".join(lines))

    def bot_started(self, total_classes: int):
        """Bot startup notification."""
        now = self._now()
        self._send(
            f"🤖 *Attendance Bot Started*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 Student: `{self.student_name}`\n"
            f"📚 Classes loaded: `{total_classes}`\n"
            f"🕐 Started at: `{now}`\n"
            f"🌐 Dashboard: `http://localhost:5000`"
        )

    def bot_stopped(self):
        """Bot shutdown notification."""
        now = self._now()
        self._send(
            f"🛑 *Attendance Bot Stopped*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🕐 Stopped at: `{now}`"
        )

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────

    def _now(self) -> str:
        return datetime.now(PKT).strftime("%I:%M %p")

    def _send(self, text: str):
        """Send message in a daemon thread so it never blocks the bot."""
        if not self.enabled:
            return
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            return
        t = threading.Thread(target=self._post, args=(text,), daemon=True)
        t.start()

    def _post(self, text: str):
        try:
            requests.post(
                self._base_url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
        except Exception:
            pass  # Never let Telegram failure crash the bot
