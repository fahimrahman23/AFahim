"""
MeWe AutoFollow - Playwright Automation Engine (single-thread version)

IMPORTANT: Playwright's sync API only works from the thread that created it.
Every Playwright call here (launch, click, scroll, close) runs inside ONE
dedicated thread. The UI only sends commands / flips flags.
"""

import re
import time
import random
import queue
import threading
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext, Page, Locator
from config import AppConfig

# Exactly "Follow" / "+ Follow" / "Follow member" ... never "Following"
FOLLOW_TEXT_RE = re.compile(r"^\s*\+?\s*follow(\s+(member|profile|user|page))?\s*$", re.IGNORECASE)

UNSAFE_KEYWORDS = [
    "unfollow", "following", "requested", "pending", "connected",
    "connection", "friends", "friend", "joined", "cancel",
    "disconnect", "leave", "block", "mute", "remove"
]

# Scrolls the window AND any inner scrollable container (MeWe lists are
# usually inside an inner container, so window.scrollBy alone does nothing).
SCROLL_JS = """
(step) => {
  window.scrollBy(0, step);
  document.querySelectorAll('*').forEach(el => {
    if (el.scrollHeight > el.clientHeight + 50) {
      const oy = getComputedStyle(el).overflowY;
      if (oy === 'auto' || oy === 'scroll') el.scrollTop += step;
    }
  });
}
"""

MAX_EMPTY_SCROLLS = 25      # stop if this many scrolls in a row find nothing
MAX_FAIL_STREAK = 5         # stop if this many clicks in a row fail


class MeWeBot:
    def __init__(self, config: AppConfig, on_log, on_stats, on_status, on_captcha, on_stop):
        self.config = config
        self.on_log = on_log
        self.on_stats = on_stats
        self.on_status = on_status
        self.on_captcha = on_captcha
        self.on_stop = on_stop

        self._cmds: "queue.Queue[str]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._thread_lock = threading.Lock()

        self._running = False
        self._paused = False
        self._browser_open = False

        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        self._empty_scrolls = 0
        self._fail_streak = 0

        self.stats = self._fresh_stats()

    # ------------------------------------------------------------------ state
    @staticmethod
    def _fresh_stats() -> dict:
        return {
            "session_follows": 0,
            "profiles_scanned": 0,
            "skipped_already_following": 0,
            "errors": 0,
            "scrolls_performed": 0,
            "start_time": 0.0,
        }

    @property
    def is_browser_open(self) -> bool:
        return self._browser_open

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._running and self._paused

    def _emit_stats(self) -> None:
        self.on_stats(dict(self.stats))

    # ------------------------------------------------------- public (UI side)
    def launch_browser(self) -> None:
        """Non-blocking: asks the Playwright thread to open Chrome."""
        self._ensure_thread()
        self._cmds.put("launch")

    def close_browser(self) -> None:
        self.stop("Browser closed")
        self._cmds.put("close")

    def shutdown(self) -> None:
        """Call when the app window closes."""
        self._running = False
        self._cmds.put("quit")
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=5)

    def start(self) -> None:
        if self._running:
            return
        self._ensure_thread()

        if not self._browser_open:
            self._cmds.put("launch")
            self.on_log(
                "Chrome was not open. Opening it now: log into MeWe, open the page "
                "that lists people with Follow buttons, then press START again.",
                "WARN",
            )
            self.on_stop("Open the people list in Chrome, then press START")
            return

        self.stats = self._fresh_stats()
        self.stats["start_time"] = time.time()
        self._empty_scrolls = 0
        self._fail_streak = 0
        self._paused = False
        self._running = True
        self._emit_stats()
        self.on_status("Running AutoFollow")
        self.on_log("AutoFollow started. Scanning visible Follow buttons...", "SUCCESS")

    def pause(self) -> None:
        if not self._running:
            return
        self._paused = not self._paused
        self.on_status("Paused" if self._paused else "Running AutoFollow")

    def stop(self, reason: str = "Stopped") -> None:
        was_running = self._running
        self._running = False
        self._paused = False
        if was_running:
            self.on_status("Stopped")
            self.on_stop(reason)

    # ---------------------------------------------- Playwright thread (only!)
    def _ensure_thread(self) -> None:
        with self._thread_lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._pw_main, name="PlaywrightThread", daemon=True
                )
                self._thread.start()

    def _pw_main(self) -> None:
        while True:
            try:
                while True:
                    cmd = self._cmds.get_nowait()
                    if cmd == "launch":
                        self._do_launch()
                    elif cmd == "close":
                        self._do_close()
                    elif cmd == "quit":
                        self._do_close()
                        return
            except queue.Empty:
                pass

            if self._running and not self._paused and self._browser_open:
                try:
                    self._step()
                except Exception as e:
                    self.stats["errors"] += 1
                    self.on_log(f"Error: {str(e).splitlines()[0] if str(e) else e!r}", "ERROR")
                    self._sleep(1.5)
            else:
                time.sleep(0.2)

    def _sleep(self, seconds: float) -> None:
        """Sleep, but wake up early on Stop or when a command is waiting."""
        end = time.time() + seconds
        while time.time() < end:
            if not self._running or not self._cmds.empty():
                return
            time.sleep(min(0.2, max(0.0, end - time.time())))

    def _do_launch(self) -> None:
        if self._browser_open and self._page and not self._page.is_closed():
            self.on_log("Browser is already open.", "INFO")
            return

        self.on_status("Launching Chrome...")
        self.on_log("Launching Chrome window with persistent profile...", "INFO")
        try:
            if not self._playwright:
                self._playwright = sync_playwright().start()

            user_data_dir = str(self.config.get_chrome_profile_dir())
            launch_args = ["--no-default-browser-check", "--no-first-run", "--start-maximized"]
            channel = "chrome" if self.config.use_system_chrome else None

            try:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir, headless=False, channel=channel,
                    args=launch_args, no_viewport=True, chromium_sandbox=True,
                )
            except Exception:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir, headless=False,
                    args=launch_args, no_viewport=True, chromium_sandbox=True,
                )

            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
            self._browser_open = True
            self.on_log("Navigating to https://mewe.com ...", "INFO")
            self._page.goto("https://mewe.com", wait_until="domcontentloaded", timeout=45000)

            self.on_status("Chrome Ready (MeWe loaded)")
            self.on_log(
                "Chrome opened. Log in, open the page with Follow buttons, then press START.",
                "SUCCESS",
            )
        except Exception as e:
            self._browser_open = False
            self.on_log(f"Failed to launch Chrome: {e}", "ERROR")
            self.on_status("Launch Error")

    def _do_close(self) -> None:
        self._running = False
        for closer in (
            lambda: self._context.close() if self._context else None,
            lambda: self._playwright.stop() if self._playwright else None,
        ):
            try:
                closer()
            except Exception:
                pass
        self._context = None
        self._page = None
        self._playwright = None
        self._browser_open = False
        self.on_status("Browser Closed")

    # ------------------------------------------------------------ main logic
    def _step(self) -> None:
        cfg = self.config
        page = self._page

        if page is None or page.is_closed():
            self._browser_open = False
            self.on_log("Chrome window was closed. Click 'Open Chrome' again.", "ERROR")
            self.stop("Browser closed")
            return

        if cfg.max_follows_session > 0 and self.stats["session_follows"] >= cfg.max_follows_session:
            self.on_log(f"Session limit reached ({self.stats['session_follows']}). Stopping.", "SUCCESS")
            self.stop("Limit reached")
            return

        if cfg.stop_on_captcha and self._captcha_visible():
            self.on_captcha("CAPTCHA detected. Solve it manually in Chrome, then press START.")
            self.on_log("CAPTCHA detected. Stopped.", "WARN")
            self.stop("CAPTCHA detected")
            return

        btn = self._find_next_follow_button()

        if btn is not None:
            self._empty_scrolls = 0
            self.stats["profiles_scanned"] += 1
            try:
                # mark it so we never click the same element twice
                btn.evaluate("e => e.setAttribute('data-af-done', '1')")
                btn.scroll_into_view_if_needed(timeout=2000)
                self._sleep(random.uniform(0.3, 0.7))
                btn.click(timeout=3000)
            except Exception as err:
                self.stats["errors"] += 1
                self._fail_streak += 1
                first = str(err).splitlines()[0] if str(err) else repr(err)
                self.on_log(f"Click failed: {first}", "WARN")
                self._emit_stats()
                if self._fail_streak >= MAX_FAIL_STREAK:
                    self.on_log("Too many failed clicks in a row. Stopping.", "ERROR")
                    self.stop("Too many click errors")
                else:
                    self._sleep(1.0)
                return

            self._fail_streak = 0
            self.stats["session_follows"] += 1
            self._emit_stats()
            self.on_log(
                f"Followed profile! [Session: {self.stats['session_follows']} / {cfg.max_follows_session or '∞'}]",
                "SUCCESS",
            )

            delay = round(random.uniform(cfg.min_delay_seconds, cfg.max_delay_seconds), 2)
            self.on_log(f"Waiting {delay}s...", "INFO")
            self._sleep(delay)

            n = cfg.cooldown_after_follows
            if n and self.stats["session_follows"] % n == 0 and self._running:
                self.on_log(f"Cooldown: resting {cfg.cooldown_break_seconds}s", "INFO")
                self._sleep(cfg.cooldown_break_seconds)
            return

        # ---- no Follow button visible right now
        self._empty_scrolls += 1

        if self._empty_scrolls == 1:
            self.on_log(f"No Follow button visible on: {page.url}", "WARN")
            self.on_log("Tip: open a page that lists people with a Follow button.", "INFO")

        if not cfg.auto_scroll_enabled:
            self._sleep(2.0)
            return

        if self._empty_scrolls > MAX_EMPTY_SCROLLS:
            self.on_log("No more Follow buttons found after many scrolls. Stopping.", "WARN")
            self.stop("No more profiles")
            return

        self.on_log("Scrolling down to discover more profiles...", "INFO")
        self._scroll()
        self._sleep(cfg.scroll_pause_seconds + random.uniform(0.5, 1.5))

    def _scroll(self) -> None:
        step = int(self.config.scroll_step_pixels or 650)
        self._page.evaluate(SCROLL_JS, step)
        self.stats["scrolls_performed"] += 1

    def _captcha_visible(self) -> bool:
        try:
            return self._page.locator(
                "iframe[src*='captcha' i], iframe[title*='captcha' i]"
            ).first.is_visible()
        except Exception:
            return False

    def _find_next_follow_button(self) -> Optional[Locator]:
        """Re-scan the page every time, return the first safe visible Follow button."""
        page = self._page
        finders = (
            lambda: page.get_by_role("button", name=FOLLOW_TEXT_RE),
            lambda: page.get_by_text(FOLLOW_TEXT_RE),
        )
        for make in finders:
            try:
                loc = make()
                for i in range(min(loc.count(), 40)):
                    btn = loc.nth(i)
                    if self._is_safe_follow_button(btn):
                        return btn
            except Exception:
                continue
        return None

    def _is_safe_follow_button(self, locator: Locator) -> bool:
        try:
            if not locator.is_visible():
                return False
            if locator.get_attribute("data-af-done", timeout=500) is not None:
                return False
            text = (locator.inner_text(timeout=500) or "").strip().lower()
            aria = (locator.get_attribute("aria-label", timeout=500) or "").strip().lower()
            combined = f"{text} {aria}"
            for unsafe in UNSAFE_KEYWORDS:
                if unsafe in combined:
                    self.stats["skipped_already_following"] += 1
                    return False
            return bool(FOLLOW_TEXT_RE.match(text))
        except Exception:
            return False
