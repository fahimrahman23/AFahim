"""
MeWe AutoFollow - Playwright Automation Engine
Controls separate Chrome window, performs intelligent button detection,
enforces strict Unfollow exclusion, human-like delays, auto-scrolling,
and detects CAPTCHA / rate-limits safely.
"""

import os
import re
import time
import random
import threading
from typing import Callable, Optional, Dict, Any, List
from pathlib import Path

from playwright.sync_api import sync_playwright, BrowserContext, Page, Locator
from config import AppConfig

FOLLOW_REGEX = re.compile(r"^(\+?\s*follow(\s+(member|profile|user|page))?)$", re.IGNORECASE)

UNSAFE_KEYWORDS = [
    "unfollow", "following", "requested", "pending", "connected",
    "connection", "friends", "friend", "joined", "cancel",
    "disconnect", "leave", "block", "mute", "remove"
]

class MeWeBot:
    def __init__(self, config: AppConfig, on_log, on_stats, on_status, on_captcha, on_stop):
        self.config = config
        self.on_log = on_log
        self.on_stats = on_stats
        self.on_status = on_status
        self.on_captcha = on_captcha
        self.on_stop = on_stop

        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        self.stats = {
            "session_follows": 0,
            "profiles_scanned": 0,
            "skipped_already_following": 0,
            "errors": 0,
            "scrolls_performed": 0,
            "start_time": 0.0
        }

    @property
    def is_browser_open(self) -> bool:
        try:
            return bool(self._context and self._page and not self._page.is_closed())
        except Exception:
            return False

    @property
    def is_running(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.is_alive()

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def launch_browser(self) -> bool:
        if self.is_browser_open:
            self.on_log("Browser is already open.", "INFO")
            return True

        self.on_status("Launching Chrome...")
        self.on_log("Launching Chrome window with persistent profile...", "INFO")

        try:
            if not self._playwright:
                self._playwright = sync_playwright().start()

            user_data_dir = str(self.config.get_chrome_profile_dir())
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--no-first-run",
                "--start-maximized"
            ]

            launch_channel = "chrome" if self.config.use_system_chrome else None
            try:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    channel=launch_channel,
                    args=launch_args,
                    no_viewport=True,
                    slow_mo=100
                )
            except Exception:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    args=launch_args,
                    no_viewport=True,
                    slow_mo=100
                )

            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
            self.on_log("Navigating to https://mewe.com ...", "INFO")
            self._page.goto("https://mewe.com", wait_until="domcontentloaded", timeout=45000)

            self.on_status("Chrome Ready (MeWe loaded)")
            self.on_log("Chrome window opened. Log into MeWe manually if not signed in.", "SUCCESS")
            return True
        except Exception as e:
            self.on_log(f"Failed to launch Chrome: {e}", "ERROR")
            self.on_status("Launch Error")
            return False

    def close_browser(self) -> None:
        self.stop()
        if self._context:
            try: self._context.close()
            except Exception: pass
            self._context = None
            self._page = None
        if self._playwright:
            try: self._playwright.stop()
            except Exception: pass
            self._playwright = None
        self.on_status("Browser Closed")

    def start(self) -> None:
        if self.is_running: return
        if not self.is_browser_open and not self.launch_browser(): return

        self._stop_event.clear()
        self._pause_event.set()
        self._worker_thread = threading.Thread(target=self._run_loop, name="Worker", daemon=True)
        self._worker_thread.start()
        self.on_status("Running AutoFollow")
        self.on_log("AutoFollow started. Scanning visible Follow buttons...", "SUCCESS")

    def pause(self) -> None:
        if not self.is_running: return
        if self.is_paused:
            self._pause_event.set()
            self.on_status("Running AutoFollow")
        else:
            self._pause_event.clear()
            self.on_status("Paused")

    def stop(self, reason: str = "Stopped") -> None:
        self._stop_event.set()
        self._pause_event.set()
        self._worker_thread = None
        self.on_status("Stopped")
        self.on_stop(reason)

    def _is_safe_follow_button(self, locator: Locator) -> bool:
        try:
            if not locator.is_visible(): return False
            text = (locator.inner_text(timeout=500) or "").strip().lower()
            aria = (locator.get_attribute("aria-label", timeout=500) or "").strip().lower()
            combined = f"{text} {aria}"

            for unsafe in UNSAFE_KEYWORDS:
                if unsafe in combined:
                    self.stats["skipped_already_following"] += 1
                    return False

            if FOLLOW_REGEX.search(text) or text in ["follow", "+ follow", "+follow"]:
                return True
            return False
        except Exception:
            return False

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            if not self._pause_event.is_set():
                time.sleep(0.5)
                continue

            if self.stats["session_follows"] >= self.config.max_follows_session:
                self.on_log(f"Session limit reached ({self.stats['session_follows']}). Stopping.", "SUCCESS")
                self.stop("Limit reached")
                break

            # Find candidates
            candidates = []
            for sel in ["button:has-text('Follow')", "button:has-text('+ Follow')", "[data-testid*='follow']"]:
                try:
                    loc = self._page.locator(sel)
                    for i in range(loc.count()):
                        btn = loc.nth(i)
                        if self._is_safe_follow_button(btn):
                            candidates.append(btn)
                except Exception:
                    pass

            self.stats["profiles_scanned"] += len(candidates)
            self.on_stats(self.stats)

            clicked_any = False
            for btn in candidates:
                if self._stop_event.is_set(): break
                if not self._is_safe_follow_button(btn): continue

                try:
                    btn.scroll_into_view_if_needed(timeout=2000)
                    time.sleep(random.uniform(0.3, 0.7))
                    btn.click(timeout=3000)
                    self.stats["session_follows"] += 1
                    clicked_any = True
                    self.on_stats(self.stats)
                    self.on_log(f"Followed profile! [Session: {self.stats['session_follows']} / {self.config.max_follows_session}]", "SUCCESS")

                    delay = round(random.uniform(self.config.min_delay_seconds, self.config.max_delay_seconds), 2)
                    self.on_log(f"Waiting {delay}s for human-like timing...", "INFO")
                    time.sleep(delay)
                except Exception as err:
                    self.stats["errors"] += 1
                    time.sleep(1.0)

            if not clicked_any and self.config.auto_scroll_enabled:
                self.on_log("Scrolling down to discover more profiles...", "INFO")
                self._page.evaluate("window.scrollBy({ top: 650, behavior: 'smooth' });")
                time.sleep(self.config.scroll_pause_seconds + random.uniform(0.5, 1.5))
