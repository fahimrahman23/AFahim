"""
MeWe AutoFollow - Configuration Manager
Handles safe persistent settings in the user's home profile directory.
Strict Privacy Rule: No passwords or personal credentials are ever saved.
"""

import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict

def _get_profile_name() -> str:
    """Reads '--profile NAME' from the command line (empty = default profile)."""
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--profile" and i + 1 < len(args):
            return "".join(ch for ch in args[i + 1] if ch.isalnum() or ch in "-_")
        if a.startswith("--profile="):
            return "".join(ch for ch in a.split("=", 1)[1] if ch.isalnum() or ch in "-_")
    return ""


PROFILE_NAME = _get_profile_name()


@dataclass
class AppConfig:
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 2.0
    max_follows_session: int = 0  # 0 = unlimited
    max_follows_daily: int = 150
    scroll_step_pixels: int = 650
    scroll_pause_seconds: float = 1.0
    cooldown_after_follows: int = 100
    cooldown_break_seconds: int = 20
    use_system_chrome: bool = True
    custom_chrome_path: str = ""
    stop_on_captcha: bool = True
    auto_scroll_enabled: bool = True
    config_version: int = 2

    @classmethod
    def get_config_dir(cls) -> Path:
        if os.name == "nt":
            app_data = os.getenv("APPDATA")
            base = Path(app_data) if app_data else Path.home()
            path = base / "MeWeAutoFollow"
        else:
            path = Path.home() / ".mewe_autofollow"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_chrome_profile_dir(cls) -> Path:
        folder = f"chrome_user_data_{PROFILE_NAME}" if PROFILE_NAME else "chrome_user_data"
        profile_dir = cls.get_config_dir() / folder
        profile_dir.mkdir(parents=True, exist_ok=True)
        return profile_dir

    @classmethod
    def get_config_file_path(cls) -> Path:
        return cls.get_config_dir() / "config.json"

    def save(self) -> None:
        try:
            with open(self.get_config_file_path(), "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            print(f"[Config] Save failed: {e}")

    @classmethod
    def load(cls) -> "AppConfig":
        file_path = cls.get_config_file_path()
        if not file_path.exists():
            cfg = cls()
            cfg.save()
            return cfg
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid = set(cls.__dataclass_fields__.keys())
            cfg = cls(**{k: v for k, v in data.items() if k in valid})
            # Older config files: apply the new speed defaults once
            if data.get("config_version", 1) < cls.config_version:
                cfg.min_delay_seconds = 1.0
                cfg.max_delay_seconds = 2.0
                cfg.max_follows_session = 0
                cfg.scroll_pause_seconds = 1.0
                cfg.cooldown_after_follows = 100
                cfg.cooldown_break_seconds = 20
                cfg.config_version = cls.config_version
                cfg.save()
            return cfg
        except Exception:
            return cls()
