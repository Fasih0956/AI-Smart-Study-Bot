"""In-memory state store shared across components."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class StateStore:
    _state: Dict[str, Any] = {
        "current_class": None,
        "status": "idle",
        "attendance_marked": False,
        "session_start": None,
        "last_caption": "",
        "last_event": "",
    }

    def set_current_class(self, cls: Dict):
        self._state["current_class"] = cls
        self._state["status"] = "in_class"
        self._state["session_start"] = datetime.now().isoformat()
        self._state["attendance_marked"] = False
        self._save()

    def mark_attendance(self):
        self._state["attendance_marked"] = True
        self._save()

    def set_idle(self):
        self._state["status"] = "idle"
        self._state["current_class"] = None
        self._save()

    def update(self, key: str, value: Any):
        self._state[key] = value

    def get(self, key: str) -> Any:
        return self._state.get(key)

    def all(self) -> Dict:
        return dict(self._state)

    def _save(self):
        Path("logs").mkdir(exist_ok=True)
        with open("logs/state.json", "w") as f:
            json.dump(self._state, f, indent=2, default=str)
