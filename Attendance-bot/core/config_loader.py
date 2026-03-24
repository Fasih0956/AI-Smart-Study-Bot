"""Config loader - minimal validation."""
import json
from pathlib import Path

class ConfigLoader:
    @staticmethod
    def load(path: str) -> dict:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {path}")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert "student"  in config, "Missing student"
        assert "classes"  in config, "Missing classes"
        for i, cls in enumerate(config["classes"]):
            assert "day"      in cls, f"Class {i} missing day"
            assert "time"     in cls, f"Class {i} missing time"
            assert "duration" in cls, f"Class {i} missing duration"
            assert "subject"  in cls, f"Class {i} missing subject"
            assert "platform" in cls, f"Class {i} missing platform"
            assert "link"     in cls, f"Class {i} missing link"
        return config