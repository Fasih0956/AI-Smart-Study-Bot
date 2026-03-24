"""
Attendance Logger
Logs every session result to Excel and a JSON history file.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from core.logger import setup_logger

logger = setup_logger("AttendanceLogger")


class AttendanceLogger:
    def __init__(self):
        Path("logs").mkdir(exist_ok=True)
        self.json_log = Path("logs/attendance_history.json")
        self.excel_log = Path("logs/attendance.xlsx")
        self._history = self._load_history()

    def _load_history(self):
        if self.json_log.exists():
            with open(self.json_log, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_history(self):
        with open(self.json_log, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2, default=str, ensure_ascii=False)

    def log_session(self, cls: Dict, marked: bool = True):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "subject": cls.get("subject", "Unknown"),
            "platform": cls.get("platform", "unknown"),
            "link": cls.get("link", ""),
            "day": cls.get("day", ""),
            "time": cls.get("time", ""),
            "status": "present" if marked else "joined_no_mark",
        }
        self._history.append(entry)
        self._save_history()
        self._write_excel()
        logger.info(
            f"[Log] Session logged: {entry['subject']} — "
            f"{'PRESENT' if marked else 'NO MARK'}"
        )

    def log_failure(self, cls: Dict, error: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "subject": cls.get("subject", "Unknown"),
            "platform": cls.get("platform", "unknown"),
            "status": "failed",
            "error": error,
        }
        self._history.append(entry)
        self._save_history()

    def _write_excel(self):
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Attendance Log"

            headers = ["Date", "Time", "Subject", "Platform", "Day", "Status"]
            ws.append(headers)

            for entry in self._history:
                ts = entry.get("timestamp", "")
                date_str = ts[:10] if ts else ""
                time_str = ts[11:16] if ts else ""
                ws.append([
                    date_str,
                    time_str,
                    entry.get("subject", ""),
                    entry.get("platform", ""),
                    entry.get("day", ""),
                    entry.get("status", ""),
                ])

            wb.save(str(self.excel_log))
        except ImportError:
            pass  # openpyxl not installed
        except Exception as e:
            logger.warning(f"Excel write failed: {e}")
