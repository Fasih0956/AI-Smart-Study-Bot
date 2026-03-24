"""
Telegram Bot Setup — run this once to get your bot token and chat_id.
Usage:  python telegram_setup.py
"""

import requests

print("""
╔══════════════════════════════════════════════╗
║       Telegram Bot Setup — Step by Step      ║
╚══════════════════════════════════════════════╝

STEP 1 — Create your Telegram Bot:
  1. Open Telegram → search @BotFather
  2. Send: /newbot
  3. Choose a name: e.g. "Fasih Attendance Bot"
  4. Choose a username: e.g. "fasih_attendance_bot"
  5. BotFather gives you a TOKEN — copy it below

""")

token = input("Paste your BOT TOKEN here: ").strip()

if not token:
    print("No token entered. Exiting.")
    exit()

print("""
STEP 2 — Get your Chat ID:
  1. Open Telegram → find your new bot
  2. Send it ANY message (e.g. "hi")
  3. Press Enter below to fetch your chat_id
""")
input("Press Enter after messaging your bot...")

try:
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
    data = r.json()
    updates = data.get("result", [])
    if not updates:
        print("❌ No messages found. Make sure you sent a message to your bot first.")
        exit()
    chat_id = updates[-1]["message"]["chat"]["id"]
    print(f"\n✅ Found chat_id: {chat_id}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

print(f"""
STEP 3 — Add to your config/schedule.json:

  "telegram": {{
    "enabled": true,
    "bot_token": "{token}",
    "chat_id": "{chat_id}"
  }},

Copy the block above into your schedule.json file.
""")

# Test message
try:
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "✅ *Attendance Bot connected!*\nTelegram notifications are working.",
            "parse_mode": "Markdown"
        },
        timeout=10
    )
    if r.json().get("ok"):
        print("✅ Test message sent to your Telegram! Check it now.")
    else:
        print("⚠️  Could not send test message:", r.json())
except Exception as e:
    print(f"❌ Test message error: {e}")
