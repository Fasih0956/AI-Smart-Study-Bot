"""
Watchdog — monitors the bot process and restarts it on crash.
Run this instead of bot.py for production unattended use.
Usage: python watchdog.py [--test]
"""

import subprocess
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/watchdog.log"),
    ]
)
logger = logging.getLogger("Watchdog")

MAX_RESTARTS = 10
RESTART_DELAY = 30  # seconds
CRASH_RESET_SECS = 300  # reset restart count if bot runs for 5+ min


def run():
    args = ["python", "bot.py"] + sys.argv[1:]
    restart_count = 0

    while restart_count < MAX_RESTARTS:
        logger.info(f"Starting bot (attempt {restart_count + 1}/{MAX_RESTARTS})...")
        start_time = time.time()

        try:
            proc = subprocess.run(args)
            elapsed = time.time() - start_time

            if proc.returncode == 0:
                logger.info("Bot exited cleanly. Watchdog stopping.")
                break

            if elapsed > CRASH_RESET_SECS:
                logger.info(f"Bot ran for {elapsed:.0f}s before crash. Resetting counter.")
                restart_count = 0
            else:
                restart_count += 1

            logger.warning(
                f"Bot crashed (code {proc.returncode}). "
                f"Restarting in {RESTART_DELAY}s... "
                f"[{restart_count}/{MAX_RESTARTS}]"
            )
            time.sleep(RESTART_DELAY)

        except KeyboardInterrupt:
            logger.info("Watchdog stopped by user.")
            break
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
            restart_count += 1
            time.sleep(RESTART_DELAY)

    if restart_count >= MAX_RESTARTS:
        logger.critical("Max restarts reached. Bot is likely broken. Check logs.")


if __name__ == "__main__":
    run()
