"""
Reconnect Handler
Detects internet drops and meeting disconnections, triggers rejoin.
"""

import asyncio
import socket
from core.logger import setup_logger

logger = setup_logger("ReconnectHandler")


async def wait_for_internet(timeout_secs: int = 120) -> bool:
    """Wait until internet is back. Returns True if restored."""
    logger.warning("Internet connection lost. Waiting for reconnect...")
    for i in range(timeout_secs // 5):
        if _is_online():
            logger.info("Internet restored!")
            return True
        await asyncio.sleep(5)
    logger.error(f"No internet after {timeout_secs}s")
    return False


def _is_online() -> bool:
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False


async def handle_waiting_room(page, timeout_secs: int = 300):
    """
    Wait in Google Meet waiting room until admitted.
    Polls every 5 seconds for up to timeout_secs.
    """
    logger.info("Detected waiting room. Waiting to be admitted...")
    for _ in range(timeout_secs // 5):
        # Check if we've been admitted (controls become visible)
        try:
            leave_btn = page.locator('[aria-label*="Leave call"]')
            if await leave_btn.count() > 0:
                logger.info("Admitted from waiting room!")
                return True
        except Exception:
            pass
        await asyncio.sleep(5)
    logger.warning("Waiting room timeout — never admitted")
    return False


async def dismiss_popups(page):
    """Dismiss common browser/Meet popups."""
    popup_selectors = [
        'button:has-text("Got it")',
        'button:has-text("Dismiss")',
        'button:has-text("OK")',
        'button:has-text("Allow")',
        '[aria-label="Close"]',
        'button:has-text("Continue")',
    ]
    for sel in popup_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                await btn.click()
                logger.debug(f"Dismissed popup: {sel}")
                await asyncio.sleep(0.5)
        except Exception:
            pass
