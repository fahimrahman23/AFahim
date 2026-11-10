"""
MeWe AutoFollow - Configuration Manager
Handles safe persistent settings in the user's home profile directory.
Strict Privacy Rule: No passwords or personal credentials are ever saved.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class AppConfig:
    min_delay_seconds: float = 4.0
    max_delay_seconds: float = 9.0
    max_follows_session: int = 50
    max_follows_daily: int = 150
    scroll_step_pixels: int = 650
    scroll_pause_seconds: float = 2.5
    cooldown_after_follows: int = 15
    cooldown_break_seconds: int = 60
    use_system_chrome: bool = True
    custom_chrome_path: str = ""
    stop_on_captcha: bool = True
    auto_scroll_enabled: bool = True

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
        profile_dir = cls.get_config_dir() / "chrome_user_data"
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
            return cls(**{k: v for k, v in data.items() if k in valid})
        except Exception:
            return cls()
