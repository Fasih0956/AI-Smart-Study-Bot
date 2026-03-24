# 🤖 Attendance Bot
**Automated Attendance for Google Meet & Zoom**
Windows 11 · Local Machine · NVIDIA GPU Supported

---

## Architecture Overview

```
attendance_bot/
├── bot.py                    ← Main entry point
├── watchdog.py               ← Crash recovery daemon
├── run.bat                   ← Windows run script
├── setup.bat                 ← One-time setup script
├── requirements.txt
│
├── config/
│   └── schedule.json         ← YOUR CLASS SCHEDULE (edit this)
│
├── core/
│   ├── config_loader.py      ← JSON config validation
│   ├── logger.py             ← Colored console + file logging
│   ├── scheduler.py          ← Class timing, consecutive class logic
│   └── session_manager.py    ← Join/monitor/leave orchestration
│
├── platforms/
│   ├── meet_handler.py       ← Google Meet automation (Playwright)
│   └── zoom_handler.py       ← Zoom web client automation
│
├── detection/
│   ├── attendance_detector.py ← Teacher phrase NLP (Urdu + English)
│   ├── burst_detector.py      ← 5+ "present" in 3s detection
│   └── whisper_asr.py         ← GPU-accelerated speech (fallback)
│
├── utils/
│   ├── caption_reader.py      ← Caption text buffer
│   ├── selectors.py           ← ALL DOM selectors (update here if UI changes)
│   ├── state_store.py         ← Runtime state (current class, status)
│   ├── attendance_logger.py   ← Excel + JSON history log
│   └── reconnect.py           ← Internet drop + waiting room handler
│
├── dashboard/
│   └── server.py              ← Flask dashboard at localhost:5000
│
├── logs/                      ← Auto-created
├── screenshots/               ← Auto-created (on errors)
└── profiles/chrome_profile/   ← Persistent Chrome login
```

---

## Quick Start

### Step 1 — Install
```bat
# Double-click setup.bat
# OR run in terminal:
setup.bat
```

### Step 2 — Configure Schedule
Edit `config/schedule.json`:
```json
{
  "student": {
    "name": "xyz",
    "roll_no": "xyz",
    "urdu_names": ["xyz"]
  },
  "classes": [
    {
      "id": "class_001",
      "day": "Saturday",
      "time": "06:56",
      "subject": "TEST CLASS 1",
      "link": "https://meet.google.com/pwu-ezkr-hsu",
      "platform": "meet",
      "duration": 120,
      "captions_available": true,
      "allowed_delay": 5,
      "_test": true
    }
  ]
}
```
### Step 3 Run python intall_chromedriver.py in cmd or powershell. This installs compatible chrome driver for bot automation.

### Step 4 — First Run (Login Chrome)
```bat
venv\Scripts\activate
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch_persistent_context('profiles/chrome_profile', channel='chrome', headless=False); b.new_page().goto('https://accounts.google.com'); input('Login to Google, then press Enter...')"
```
> This saves your Google session so the bot doesn't need to log in every time.

### Step 4 — Test Run
```bat
python bot.py --test
```
Joins the first class marked `"_test": true` immediately.

### Step 5 — Production Run (Unattended)
```bat
# With crash recovery:
python watchdog.py

# Or direct:
run.bat
```

---

## How It Works

### Google Meet Flow
```
Schedule triggers class
    ↓
Wait 1 minute (join_delay)
    ↓
Launch Chrome (persistent profile = no re-login)
    ↓
Navigate to Meet link
    ↓
Disable mic + camera
    ↓
Click "Join Now" / "Ask to join"
    ↓
Handle waiting room (auto-wait up to 5 min)
    ↓
Enable Live Captions
    ↓
Monitor Loop (every 2 seconds):
    ├── Read captions from DOM
    ├── Read chat messages
    ├── Run Burst Detector (5+ "present" in 3s)
    ├── Run Attendance Detector (teacher phrases)
    └── Send "Present" or "Mic kharab hai" as needed
    ↓
End Condition:
    ├── Host ends meeting → leave
    ├── End time reached → leave
    └── Internet drop → reconnect + rejoin
```

### Attendance Detection Logic
```
Caption text analyzed every 2 seconds:

IF burst (5+ "present" in chat within 3s):
    → Check captions for name/roll
    → If found: send "Present"

IF teacher says attendance phrase:
    + Name/roll in captions:
        → send "Present"
    + Only first name, question context:
        → send "Mic kharab hai"

Teacher phrases detected (Urdu + English):
  - "main attendance mark kar raha hun"
  - "attendance lgwa lain"
  - "I am marking attendance"
  - "attendance call kar raha hun"
  ... (16 total patterns)
```

### Zoom Flow
```
Join via web browser (no app needed)
    ↓
Stay silent for full duration
    ↓
At end time: send "Present" in chat
    ↓
Leave meeting
```

### Consecutive Classes
```
Class A ends at 09:00
Class B starts at 09:05
    ↓
Bot auto-detects gap ≤ 15 min
    ↓
Leaves Class A → immediately joins Class B
```

---

## Configuration Reference

### global_settings
| Key | Default | Description |
|-----|---------|-------------|
| `join_delay_minutes` | 1 | Wait N min after class start before joining |
| `leave_tolerance_minutes` | 5 | Stay N min past end time before leaving |
| `reconnect_attempts` | 3 | Retry join if it fails |
| `reconnect_delay_seconds` | 30 | Wait between retries |
| `screenshot_on_error` | true | Save screenshot on crash |
| `stealth_mode` | true | Remove browser automation fingerprints |
| `browser_profile` | `profiles/chrome_profile` | Persistent login location |

### Per-class fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique class ID |
| `day` | string | Monday–Sunday |
| `time` | string | HH:MM (24hr, Pakistan Time) |
| `subject` | string | Display name |
| `link` | string | Full meeting URL |
| `platform` | string | `"meet"` or `"zoom"` |
| `duration` | int | Class length in minutes |
| `captions_available` | bool | Enable caption monitoring |
| `allowed_delay` | int | Extra minutes tolerance at end |
| `_test` | bool | If true, joins immediately in --test mode |

---

## Dashboard

Open **http://localhost:5000** while the bot is running.

Shows:
- Current class status (IDLE / IN_CLASS)
- Whether attendance was marked
- Full session history table
- Platform badges (Meet / Zoom)

---

## Updating DOM Selectors

If Google Meet updates its UI and captions stop working:

1. Open `utils/selectors.py`
2. Right-click the caption in Meet → Inspect Element
3. Find the new `jsname` or class
4. Update `MEET["caption_container"]`

No other files need to change.

---

## GPU Acceleration (NVIDIA)

Whisper speech recognition uses CUDA automatically:
```bat
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Verify GPU is detected:
```python
import torch
print(torch.cuda.is_available())   # Should print: True
print(torch.cuda.get_device_name(0))  # Your GPU name
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't join | Check Chrome profile is logged into Google |
| Captions not reading | Update selectors in `utils/selectors.py` |
| "Join" button not found | Add `await asyncio.sleep(5)` before `_click_join()` |
| Zoom opens app instead of browser | Ensure link is `/j/` format, handler auto-converts |
| Audio not captured by Whisper | Install VB-Audio Virtual Cable |
| Bot crashes repeatedly | Check `logs/watchdog.log` for error details |
| Wrong time zone | Change `PKT = ZoneInfo("Asia/Karachi")` in scheduler.py |

---

## Dependencies

```
playwright==1.44.0          Browser automation
schedule==1.2.1             Class scheduling
openai-whisper==20231117    GPU speech recognition (optional)
flask==3.0.3                Dashboard web server
flask-socketio==5.3.6       Real-time dashboard updates
gspread==6.1.2              Google Sheets export (optional)
openpyxl==3.1.2             Excel attendance log
colorlog==6.8.2             Colored terminal output
rich==13.7.1                Pretty terminal tables
sounddevice==0.4.6          System audio capture
```

---

## File Outputs

| File | Contents |
|------|----------|
| `logs/bot_YYYYMMDD.log` | Full debug log |
| `logs/attendance_history.json` | All session records |
| `logs/attendance.xlsx` | Excel attendance sheet |
| `logs/state.json` | Live bot state |
| `logs/watchdog.log` | Crash/restart history |
| `screenshots/*.png` | Error screenshots |
