"""
Zoom Handler - Join with mic/cam off, leave when done.
No attendance detection needed for Zoom.
"""

import asyncio
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright, BrowserContext
from core.logger import setup_logger

logger = setup_logger("ZoomHandler")


class ZoomHandler:
    def __init__(self, cls: Dict, config: Dict):
        self.cls        = cls
        self.config     = config
        self.settings   = config["global_settings"]
        self.student    = config["student"]
        self.link       = cls.get("link", "").strip()
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page       = None

    def _to_web_url(self, link: str) -> str:
        if "/wc/" in link:
            return link
        if "/j/" in link:
            base       = link.split("/j/")[0]
            rest       = link.split("/j/")[1]
            meeting_id = rest.split("?")[0]
            query      = "?" + rest.split("?")[1] if "?" in rest else ""
            return f"{base}/wc/{meeting_id}/join{query}"
        return link

    async def join(self):
        if not self.link:
            raise RuntimeError("No link provided for this class — skipping.")

        logger.info(f"[Zoom] Joining: {self.link}")

        profile = Path(self.settings.get("browser_profile", "profiles/bot_profile")).absolute()
        profile.mkdir(parents=True, exist_ok=True)

        if self.playwright:
            try:
                await self.context.close()
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
            self.context    = None
            self.page       = None

        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream",
                "--disable-notifications",
                "--mute-audio",
                "--start-maximized",
            ],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
        )
        self.page = await self.context.new_page()
        await self.page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        async def close_extra_pages(page):
            if page != self.page:
                await page.close()
        self.context.on("page", close_extra_pages)

        web_url = self._to_web_url(self.link)
        logger.info(f"[Zoom] Web URL: {web_url}")
        await self.page.goto(web_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        # Dismiss cookies
        try:
            btn = self.page.locator('#onetrust-accept-btn-handler').first
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Fill name
        name = self.student.get("name", "Student")
        try:
            inp = self.page.locator("#input-for-name").first
            if await inp.count() > 0:
                await inp.click()
                await inp.fill(name)
                logger.info(f"[Zoom] Name: {name}")
        except Exception as e:
            logger.warning(f"[Zoom] Name fill failed: {e}")
        await asyncio.sleep(0.5)

        # Mute mic
        try:
            btn = self.page.locator("#preview-audio-control-button").first
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(0.3)
                logger.info("[Zoom] Mic muted")
        except Exception as e:
            logger.warning(f"[Zoom] Mic mute failed: {e}")

        # Stop camera
        try:
            btn = self.page.locator("#preview-video-control-button").first
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(0.3)
                logger.info("[Zoom] Camera off")
        except Exception as e:
            logger.warning(f"[Zoom] Camera off failed: {e}")

        # Join
        await self._click_join()
        logger.info("[Zoom] Joined successfully.")

    async def _click_join(self):
        max_wait_mins = 20
        for attempt in range(max_wait_mins * 6):
            try:
                btn = self.page.locator('button:has-text("Join")').first
                if await btn.count() > 0:
                    if await btn.get_attribute("disabled") is None:
                        await btn.click()
                        logger.info("[Zoom] Clicked Join")
                        await asyncio.sleep(3)
                        return
            except Exception:
                pass
            if attempt % 12 == 0 and attempt > 0:
                logger.info(f"[Zoom] Waiting... ({attempt//6}/{max_wait_mins} min)")
            await asyncio.sleep(10)
        raise RuntimeError(f"[Zoom] Join button not found after {max_wait_mins} min")

    async def send_chat(self, message: str):
        pass  # No chat needed for Zoom

    async def check_and_respond(self, tg, cls, state):
        pass  # No monitoring needed for Zoom

    async def is_meeting_ended(self) -> bool:
        try:
            for phrase in ["meeting has been ended", "ended by host", "meeting is over"]:
                if await self.page.locator(f':has-text("{phrase}")').count() > 0:
                    return True
        except Exception:
            pass
        return False

    async def screenshot(self, path: str):
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            await self.page.screenshot(path=path)
        except Exception:
            pass

    async def leave(self):
        try:
            for sel in ['[aria-label="Leave"]', 'button:has-text("Leave")']:
                btn = self.page.locator(sel).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(1)
                    confirm = self.page.locator('button:has-text("Leave Meeting")').first
                    if await confirm.count() > 0:
                        await confirm.click()
                    logger.info("[Zoom] Left.")
                    break
        except Exception as e:
            logger.warning(f"[Zoom] Leave failed: {e}")
        finally:
            try:
                await self.context.close()
                await self.playwright.stop()
            except Exception:
                pass