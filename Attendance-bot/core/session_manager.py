"""
Session Manager — orchestrates joining, monitoring, and leaving.

Timing rules (all relative to scheduled class time in JSON):
1. Join 2 min after scheduled start
2. Keep trying to join for up to 20 min from scheduled start
3. Leave at: scheduled_end + 5 min (or +7 min after attendance detected)
4. Rejoin if host ends early, until class_end + 5 min
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from core.logger import setup_logger
from platforms.meet_handler import MeetHandler
from platforms.zoom_handler import ZoomHandler
from utils.state_store import StateStore
from utils.attendance_logger import AttendanceLogger
from utils.telegram_notifier import TelegramNotifier

logger = setup_logger("SessionManager")
PKT = ZoneInfo("Asia/Karachi")


class SessionManager:
    def __init__(self, config: Dict):
        self.config      = config
        self.settings    = config["global_settings"]
        self.student     = config["student"]
        self.state       = StateStore()
        self.att_logger  = AttendanceLogger()
        self.tg          = TelegramNotifier(config)
        self.current_handler = None

    async def attend(self, cls: Dict, is_last: bool = True):
        platform = cls["platform"]
        subject  = cls["subject"]

        # Skip if no link
        link = cls.get("link", "").strip()
        if not link:
            logger.warning(f"[{subject}] No link — skipping.")
            return

        self.state = StateStore()
        self.state.set_current_class(cls)

        # All times relative to scheduled start in JSON
        scheduled_start = self._scheduled_start(cls)
        hard_end        = scheduled_start + timedelta(
            minutes=cls["duration"] + 5  # scheduled_end + 5 min
        )

        logger.info(
            f"[{subject}] Session | "
            f"scheduled={scheduled_start.strftime('%H:%M')} "
            f"hard_end={hard_end.strftime('%H:%M')}"
        )

        handler = self._get_handler(platform, cls)
        self.current_handler = handler
        session_start = time.time()
        joined = False

        # ── Join phase ──────────────────────────────────────
        # Try joining until 20 min after scheduled start
        join_deadline = scheduled_start + timedelta(minutes=20)
        attempt = 0
        while datetime.now(PKT) <= join_deadline:
            attempt += 1
            try:
                await handler.join()
                logger.info(f"[{subject}] Joined (attempt {attempt})")
                self.tg.joined(cls)
                joined = True
                break
            except RuntimeError as e:
                err = str(e)
                # Hard stop — no point retrying these
                if "No link" in err or "skipping" in err.lower():
                    logger.warning(f"[{subject}] {err} — skipping class.")
                    self.current_handler = None
                    return
                logger.warning(f"[{subject}] Join attempt {attempt} failed: {err}")
                remaining = (join_deadline - datetime.now(PKT)).total_seconds()
                if remaining > 0:
                    await asyncio.sleep(min(30, remaining))
            except Exception as e:
                logger.warning(f"[{subject}] Join attempt {attempt} failed: {e}")
                remaining = (join_deadline - datetime.now(PKT)).total_seconds()
                if remaining > 0:
                    await asyncio.sleep(min(30, remaining))

        if not joined:
            logger.error(f"[{subject}] Could not join within 20 min — skipping.")
            self.tg.error(cls, "Could not join within 20 min")
            self.att_logger.log_failure(cls, "Join timeout")
            self.current_handler = None
            return

        # ── Monitor + Rejoin phase ──────────────────────────
        try:
            await self._monitor_with_rejoin(handler, cls, hard_end)
        except Exception as e:
            logger.error(f"[{subject}] Session error: {e}")
            self.tg.error(cls, str(e))
        finally:
            duration_secs = int(time.time() - session_start)
            try:
                await handler.leave()
            except Exception:
                pass
            self.current_handler = None
            self.tg.left(cls, "end_time")
            self.tg.class_summary(cls, self.state.get("attendance_marked"), duration_secs)
            self.att_logger.log_session(cls, marked=bool(self.state.get("attendance_marked")))
            logger.info(f"[{subject}] Session ended.")

    async def _monitor_with_rejoin(self, handler, cls: Dict, hard_end: datetime):
        """
        Leave ONLY when one of these 3 conditions is met:
        1. scheduled_end + 5min reached (hard_end)
        2. Host ended the meeting for everyone
        3. Participant count < 5 for 2 consecutive minutes
        Nothing else causes a leave.
        """
        platform = cls["platform"]
        subject  = cls["subject"]

        logger.info(f"[{subject}] Monitoring until {hard_end.strftime('%H:%M')}")

        while True:
            now = datetime.now(PKT)

            # Case 1: Time up
            if now >= hard_end:
                logger.info(f"[{subject}] End time {hard_end.strftime('%H:%M')} reached — leaving.")
                break

            # Case 2 & 3: Meeting ended (host ended or count < 5 for 2min)
            if await handler.is_meeting_ended():
                logger.info(f"[{subject}] Meeting ended — leaving.")
                self.tg.class_ended_by_host(cls)
                break

            # Meet: run attendance detection
            if platform == "meet":
                await handler.check_and_respond(self.tg, cls, self.state)

            await asyncio.sleep(2)

    def _scheduled_start(self, cls: Dict) -> datetime:
        """Returns scheduled start as timezone-aware datetime (PKT)."""
        now = datetime.now(PKT)
        h, m = map(int, cls["time"].split(":"))
        start = now.replace(hour=h, minute=m, second=0, microsecond=0)
        # If scheduled time already passed today, it's still today
        return start

    def _get_handler(self, platform: str, cls: Dict):
        if platform == "meet":
            return MeetHandler(cls, self.config)
        elif platform == "zoom":
            return ZoomHandler(cls, self.config)
        else:
            raise ValueError(f"Unknown platform: {platform}")

    def _get_next_class(self, cls: Dict) -> Optional[Dict]:
        today = cls["day"]
        h, m  = map(int, cls["time"].split(":"))
        this_end = h * 60 + m + cls.get("duration", 60)
        candidates = []
        for other in self.config["classes"]:
            if other["day"] != today:
                continue
            if other["subject"] == cls["subject"] and other["time"] == cls["time"]:
                continue
            oh, om = map(int, other["time"].split(":"))
            if oh * 60 + om >= this_end:
                candidates.append((oh * 60 + om, other))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]