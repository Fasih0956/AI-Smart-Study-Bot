"""
One-time Google login via Playwright Chromium.
Run: python login_google.py
"""
from playwright.sync_api import sync_playwright
import os, shutil

PROFILE = os.path.abspath("profiles/bot_profile")

# Delete old broken profile
if os.path.exists(PROFILE):
    print(f"Deleting old profile: {PROFILE}")
    shutil.rmtree(PROFILE)

os.makedirs(PROFILE, exist_ok=True)
print(f"Fresh profile: {PROFILE}")
print()
print("Chrome will open. Sign in with k240956@nu.edu.pk")
print("After signing in fully, close the Chrome window.")
print()
input("Press Enter to open Chrome...")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE,
        headless=False,
        args=[
            "--no-sandbox",
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
        ],
        ignore_default_args=["--enable-automation"],
        no_viewport=True,
    )
    page = ctx.new_page()
    page.goto("https://accounts.google.com")
    print("\nBrowser open. Sign in, then close the window.")

    try:
        ctx.wait_for_event("close", timeout=300000)
    except Exception:
        pass

print("\nProfile saved. Run: python bot.py --test")