"""
Downloads correct ChromeDriver for your Chrome version.
Run: python install_chromedriver.py
"""
import subprocess, urllib.request, urllib.error, zipfile, io, os, sys, json
from pathlib import Path

# ── Find Chrome ────────────────────────────────────────────────
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
]
chrome = next((p for p in CHROME_PATHS if os.path.exists(p)), None)
if not chrome:
    print("[ERROR] Chrome not found.")
    sys.exit(1)
print(f"Chrome: {chrome}")

# ── Get version ────────────────────────────────────────────────
try:
    out = subprocess.check_output(f'"{chrome}" --version',
        shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    version = out.split()[-1]   # e.g. 134.0.6998.89
    major   = version.split(".")[0]
    build   = ".".join(version.split(".")[:3])  # e.g. 134.0.6998
    print(f"Chrome version: {version}  (major={major}  build={build})")
except Exception as e:
    print(f"Cannot read Chrome version: {e}")
    sys.exit(1)

# ── Download ChromeDriver ──────────────────────────────────────
driver_dir = Path("chromedriver_bin")
driver_dir.mkdir(exist_ok=True)
driver_exe = driver_dir / "chromedriver.exe"

def try_download(url):
    print(f"  Trying: {url}")
    try:
        data = urllib.request.urlopen(url, timeout=60).read()
        print(f"  Downloaded {len(data)//1024} KB")
        return data
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  Failed: {e}")
        return None

def extract_driver(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    for name in z.namelist():
        if name.endswith("chromedriver.exe"):
            exe_data = z.open(name).read()
            driver_exe.write_bytes(exe_data)
            print(f"  Extracted: {driver_exe} ({driver_exe.stat().st_size//1024} KB)")
            return True
    print("  chromedriver.exe not found in zip")
    return False

print("\nFinding correct ChromeDriver...")

# Strategy 1: Use known-good versions API
data = None
try:
    api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    print(f"  Fetching versions list...")
    resp = urllib.request.urlopen(api_url, timeout=30).read()
    versions_data = json.loads(resp)
    versions = versions_data.get("versions", [])

    # Find best matching version (same major, closest build)
    matches = [v for v in versions if v["version"].startswith(major + ".")]
    if not matches:
        matches = versions  # fallback to any version

    # Sort by version descending, pick closest to our build
    def version_key(v):
        parts = v["version"].split(".")
        return tuple(int(x) for x in parts)

    matches.sort(key=version_key, reverse=True)

    # Find one that has win64 chromedriver download
    for v in matches:
        downloads = v.get("downloads", {}).get("chromedriver", [])
        win64 = next((d["url"] for d in downloads if d["platform"] == "win64"), None)
        if win64:
            print(f"  Best match: {v['version']}")
            data = try_download(win64)
            if data:
                break
except Exception as e:
    print(f"  API lookup failed: {e}")

# Strategy 2: Try exact version win64
if not data:
    url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
    data = try_download(url)

# Strategy 3: Try build prefix with win64
if not data:
    for suffix in ["0", "1", "2", "3", "4", "5"]:
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{build}.{suffix}/win64/chromedriver-win64.zip"
        data = try_download(url)
        if data:
            break

# Strategy 4: Old endpoint (Chrome < 115)
if not data:
    try:
        latest_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major}"
        latest = urllib.request.urlopen(latest_url, timeout=10).read().decode().strip()
        url = f"https://chromedriver.storage.googleapis.com/{latest}/chromedriver_win32.zip"
        data = try_download(url)
    except Exception:
        pass

if not data:
    print("\n[ERROR] Could not download ChromeDriver.")
    print("Manual download:")
    print(f"  1. Go to: https://googlechromelabs.github.io/chrome-for-testing/")
    print(f"  2. Find version matching Chrome {major}.x.x.x")
    print(f"  3. Download win64 chromedriver zip")
    print(f"  4. Extract chromedriver.exe into: chromedriver_bin\\")
    input("Press Enter to exit...")
    sys.exit(1)

if not extract_driver(data):
    print("[ERROR] Extraction failed.")
    sys.exit(1)

# ── Verify ─────────────────────────────────────────────────────
with open(driver_exe, "rb") as f:
    header = f.read(2)

if header != b"MZ":
    print(f"[ERROR] Not a valid exe (header={header})")
    sys.exit(1)

print(f"\nSUCCESS! ChromeDriver ready.")
print(f"Now run: python login_google.py")