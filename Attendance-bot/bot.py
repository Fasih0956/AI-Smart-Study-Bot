"""
╔══════════════════════════════════════════════════════════════╗
║           ATTENDANCE BOT - Main Entry Point                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from core.scheduler import ClassScheduler
from core.config_loader import ConfigLoader
from core.logger import setup_logger
from dashboard.server import DashboardServer
from utils.telegram_notifier import TelegramNotifier

logger = setup_logger("AttendanceBot")
PKT = ZoneInfo("Asia/Karachi")
DAYS = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}


class AttendanceBot:
    def __init__(self):
        self.config    = ConfigLoader.load("config/schedule.json")
        self.scheduler = ClassScheduler(self.config)
        self.dashboard = DashboardServer()
        self.tg        = TelegramNotifier(self.config)
        self._stop_event = asyncio.Event()

    async def start(self):
        logger.info("=" * 60)
        logger.info("  ATTENDANCE BOT STARTING")
        logger.info(f"  Student : {self.config['student']['name']}")
        logger.info(f"  Roll No : {self.config['student']['roll_no']}")
        logger.info(f"  Classes : {len(self.config['classes'])}")
        logger.info("=" * 60)

        threading.Thread(target=self.dashboard.run, daemon=True).start()
        logger.info("Dashboard → http://localhost:5000")

        self.tg.bot_started(len(self.config["classes"]))
        today_name = DAYS[datetime.now(PKT).weekday()]
        today_classes = sorted(
            [c for c in self.config["classes"] if c["day"] == today_name and not c.get("_test")],
            key=lambda x: x["time"]
        )
        self.tg.day_summary(today_classes)

        try:
            await self.scheduler.run()
        except asyncio.CancelledError:
            # CancelledError is raised when Ctrl+C cancels the task
            # Leave meeting first WHILE loop is still running
            await self._leave_active_meeting()
        finally:
            self.tg.bot_stopped()
            logger.info("Bot stopped.")

    async def _leave_active_meeting(self):
        """Leave active meeting — called inside async context so event loop is still running."""
        logger.info("Shutting down — leaving active meeting...")
        session = self.scheduler.session
        if session and session.current_handler:
            try:
                await session.current_handler.leave()
                logger.info("Left meeting successfully.")
            except Exception as e:
                logger.warning(f"Leave error: {e}")
        else:
            logger.info("No active meeting.")


def main():
    if "--test" in sys.argv:
        test_mode = True
    else:
        test_mode = False

    bot = AttendanceBot()

    if test_mode:
        logger.info("TEST MODE: Running first _test class immediately")
        test_classes = [c for c in bot.config["classes"] if c.get("_test")]
        if test_classes:
            bot.config["classes"] = test_classes
            bot.scheduler.test_mode = True

    async def run():
        task = asyncio.create_task(bot.start())
        try:
            await task
        except asyncio.CancelledError:
            pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        logger.info("Ctrl+C — cancelling tasks...")
        # Cancel all tasks while loop is still running
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        # Run until cancellation completes (this is where _leave_active_meeting runs)
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    finally:
        loop.close()
        logger.info("Goodbye.")


if __name__ == "__main__":
    main()