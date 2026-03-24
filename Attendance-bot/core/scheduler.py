"""
Class Scheduler — manages timing, overlapping classes, and multi-session handling.

Overlap handling:
- If class B starts while class A is still running, launch class B in a NEW parallel task
- When class A finishes, it does NOT join class B (already running)
- Each session tracks which class IDs are currently active
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

from core.logger import setup_logger
from core.session_manager import SessionManager
from utils.state_store import StateStore

logger = setup_logger("Scheduler")

DAYS = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
}

PKT = ZoneInfo("Asia/Karachi")


class ClassScheduler:
    def __init__(self, config: Dict):
        self.config   = config
        self.classes  = config["classes"]
        self.settings = config["global_settings"]
        self.student  = config["student"]
        self.running  = True
        self.test_mode = False
        self.state    = StateStore()
        self.session  = SessionManager(config)
        # Track class IDs currently running in parallel sessions
        self._active_ids: Set[str] = set()

    def stop(self):
        self.running = False

    def _cls_id(self, cls: Dict) -> str:
        if "id" not in cls:
            cls["id"] = f"{cls['day']}_{cls['time']}_{cls['subject']}".replace(" ", "_")
        return cls["id"]

    def _next_run_time(self, cls: Dict) -> Optional[datetime]:
        """Calculate next datetime this class should run."""
        now = datetime.now(PKT)
        target_weekday = DAYS.get(cls["day"])
        if target_weekday is None:
            return None

        h, m = map(int, cls["time"].split(":"))
        days_ahead = (target_weekday - now.weekday()) % 7
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        target += timedelta(days=days_ahead)

        if target <= now and days_ahead == 0:
            duration  = cls.get("duration", 60)
            class_end = target + timedelta(minutes=duration)
            if now < class_end:
                logger.info(
                    f"[Scheduler] [{cls['subject']}] started "
                    f"{int((now-target).seconds/60)}min ago — joining now"
                )
                return now
            else:
                target += timedelta(weeks=1)

        return target

    def _seconds_until(self, target: datetime) -> float:
        return max(0, (target - datetime.now(PKT)).total_seconds())

    async def run(self):
        logger.info("Scheduler started.")

        if self.test_mode:
            test_classes = [c for c in self.classes if c.get("_test")]
            if not test_classes:
                logger.error("No _test class found in schedule.json")
                return
            await self._launch_session(test_classes[0])
            return

        ran_today: Set[str] = set()

        while self.running:
            upcoming = self._get_upcoming_classes()

            # Filter: skip already ran AND currently active
            upcoming = [
                (cls, t) for cls, t in upcoming
                if self._cls_id(cls) not in ran_today
                and self._cls_id(cls) not in self._active_ids
            ]

            if not upcoming:
                logger.info("No upcoming classes. Sleeping 1 hour.")
                await asyncio.sleep(3600)
                ran_today.clear()
                continue

            upcoming.sort(key=lambda x: x[1])
            next_cls, next_time = upcoming[0]
            wait_secs = self._seconds_until(next_time)

            logger.info(
                f"Next: [{next_cls['subject']}] on {next_cls['day']} "
                f"at {next_cls['time']} — in {wait_secs/60:.1f} min"
            )

            if wait_secs > 60:
                await asyncio.sleep(wait_secs - 60)
                logger.info(f"60s until [{next_cls['subject']}]...")
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(wait_secs)

            # Mark ran BEFORE launching to prevent duplicate
            ran_today.add(self._cls_id(next_cls))

            # Check if an overlapping class is already active
            # If so, launch this class as a parallel asyncio task
            if self._active_ids:
                logger.info(
                    f"[{next_cls['subject']}] Launching in parallel "
                    f"(active: {self._active_ids})"
                )
                asyncio.create_task(self._launch_session(next_cls))
            else:
                await self._launch_session(next_cls)

        logger.info("Scheduler stopped.")

    def _get_upcoming_classes(self) -> List:
        results = []
        for cls in self.classes:
            t = self._next_run_time(cls)
            if t:
                results.append((cls, t))
        return results

    async def _launch_session(self, cls: Dict):
        """
        Launch a single class session.
        Tracks active IDs so overlapping classes don't re-join each other.
        """
        cls_id = self._cls_id(cls)

        # Wait 2 min after scheduled start before joining
        now = datetime.now(PKT)
        h, m = map(int, cls["time"].split(":"))
        scheduled = now.replace(hour=h, minute=m, second=0, microsecond=0)
        join_at   = scheduled + timedelta(minutes=2)
        wait_secs = (join_at - now).total_seconds()

        if not self.test_mode and wait_secs > 0:
            logger.info(
                f"[{cls['subject']}] Waiting until {join_at.strftime('%H:%M')} "
                f"({wait_secs:.0f}s)..."
            )
            await asyncio.sleep(wait_secs)

        # Register as active
        self._active_ids.add(cls_id)
        logger.info(f"[{cls['subject']}] Session started. Active: {self._active_ids}")

        try:
            session = SessionManager(self.config)
            self.session = session  # keep reference for shutdown
            await session.attend(cls)
        except Exception as e:
            logger.error(f"[{cls['subject']}] Session error: {e}")
        finally:
            self._active_ids.discard(cls_id)
            logger.info(f"[{cls['subject']}] Session ended. Active: {self._active_ids}")