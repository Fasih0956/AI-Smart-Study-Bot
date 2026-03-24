"""
Run this after setup.bat to confirm everything installed correctly.
Usage: python verify_install.py
"""

import sys

checks = []

def check(name, fn):
    try:
        result = fn()
        checks.append((True, name, result or "OK"))
    except Exception as e:
        checks.append((False, name, str(e)[:80]))

check("Python 3.10+",        lambda: f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
check("playwright",          lambda: __import__("playwright") and "OK")
check("flask",               lambda: __import__("flask") and "OK")
check("flask_socketio",      lambda: __import__("flask_socketio") and "OK")
check("requests",            lambda: __import__("requests") and "OK")
check("schedule",            lambda: __import__("schedule") and "OK")
check("openpyxl",            lambda: __import__("openpyxl") and "OK")
check("colorlog",            lambda: __import__("colorlog") and "OK")
check("numpy",               lambda: __import__("numpy").__version__)
check("sounddevice",         lambda: __import__("sounddevice") and "OK")
check("speech_recognition",  lambda: __import__("speech_recognition") and "OK")
check("torch (PyTorch)",     lambda: __import__("torch").__version__)
check("torch CUDA",          lambda: "YES ✓" if __import__("torch").cuda.is_available() else "NO (CPU only)")
check("whisper",             lambda: __import__("whisper") and "OK")

print("\n  Attendance Bot — Install Verification")
print("  " + "─" * 42)
all_ok = True
for ok, name, detail in checks:
    icon = "✅" if ok else "❌"
    print(f"  {icon}  {name:<26} {detail}")
    if not ok:
        all_ok = False

print("  " + "─" * 42)
if all_ok:
    print("  All checks passed! Run: python bot.py --test\n")
else:
    print("  Some checks failed. Re-run setup.bat\n")
    print("  TIP: Whisper and PyAudio are optional —")
    print("       the bot works without them (captions-only mode)\n")
