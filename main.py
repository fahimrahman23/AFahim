"""
MeWe AutoFollow - Windows 11 Desktop GUI Application
Built with Python & Tkinter with Windows 11 Fluent design principles.
Zero password storage • Thread-safe Playwright integration • Safe usage limits
"""

import os
import sys
import time
import queue
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Enable Windows high-DPI awareness
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from config import AppConfig, PROFILE_NAME
from bot import MeWeBot

# Windows 11 Fluent Dark Palette
COLORS = {
    "bg_dark": "#1E1E1E",
    "surface": "#252526",
    "card_bg": "#2D2D30",
    "card_border": "#3E3E42",
    "primary": "#0078D4",       # Windows Accent Blue
    "primary_hover": "#1E90FF",
    "success": "#107C41",       # Fluent Green
    "success_hover": "#138847",
    "danger": "#C42B1C",        # Fluent Red
    "danger_hover": "#D83B01",
    "warning": "#FCE100",
    "text_main": "#FFFFFF",
    "text_secondary": "#CCCCCC",
    "text_muted": "#8A8886",
    "log_bg": "#181818",
    "log_text": "#D4D4D4",
    "tag_success": "#4EC9B0",
    "tag_warn": "#CE9178",
    "tag_error": "#F44747",
    "tag_info": "#9CDCFE",
}

class MeWeAutoFollowApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MeWe AutoFollow - Windows 11 Desktop Edition" + (f"  [Profile: {PROFILE_NAME}]" if PROFILE_NAME else ""))
        self.root.geometry("1100x750")
        self.root.minsize(980, 680)
        self.root.configure(bg=COLORS["bg_dark"])

        self.config = AppConfig.load()
        self.event_queue = queue.Queue()

        self.bot = MeWeBot(
            config=self.config,
            on_log=self._queue_log,
            on_stats=self._queue_stats,
            on_status=self._queue_status,
            on_captcha=self._queue_captcha,
            on_stop=self._queue_stop
        )

        self.start_timestamp = None
        self._setup_styles()
        self._create_widgets()

        self.root.after(100, self._process_event_queue)
        self.root.after(1000, self._update_timer)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._append_log("MeWe AutoFollow Desktop App initialized.", "INFO")
        self._append_log("Click 'Launch Chrome' to open a separate MeWe window.", "INFO")
        self._append_log("Privacy Assurance: This app never touches or stores your password.", "SUCCESS")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLORS["bg_dark"])
        style.configure("Card.TFrame", background=COLORS["card_bg"])
        style.configure("TLabel", background=COLORS["card_bg"], foreground=COLORS["text_main"], font=("Segoe UI", 9))
        style.configure("TCheckbutton", background=COLORS["card_bg"], foreground=COLORS["text_main"], font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", COLORS["card_bg"])])

    def _create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg=COLORS["bg_dark"], pady=12, padx=18)
        header.pack(fill=tk.X)
        title_box = tk.Frame(header, bg=COLORS["bg_dark"])
        title_box.pack(side=tk.LEFT)
        tk.Label(title_box, text="⚡ MeWe AutoFollow", font=("Segoe UI", 16, "bold"), fg=COLORS["text_main"], bg=COLORS["bg_dark"]).pack(anchor="w")
        tk.Label(title_box, text="Windows 11 Native Desktop Automation • Playwright Engine", font=("Segoe UI", 9), fg=COLORS["text_secondary"], bg=COLORS["bg_dark"]).pack(anchor="w")

        status_box = tk.Frame(header, bg=COLORS["bg_dark"])
        status_box.pack(side=tk.RIGHT)
        self.lbl_status_pill = tk.Label(status_box, text="● Browser: Not Open", font=("Segoe UI", 9, "bold"), fg=COLORS["text_muted"], bg=COLORS["surface"], padx=12, pady=4)
        self.lbl_status_pill.pack()

        # Content Split
        main = tk.Frame(self.root, bg=COLORS["bg_dark"], padx=14, pady=6)
        main.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main, bg=COLORS["bg_dark"], width=420)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        right = tk.Frame(main, bg=COLORS["bg_dark"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_browser_card(left)
        self._build_execution_card(left)
        self._build_settings_card(left)
        self._build_metrics_panel(right)
        self._build_logs_panel(right)

    def _build_browser_card(self, parent):
        card = tk.LabelFrame(parent, text=" 1. Chrome Browser Integration ", font=("Segoe UI", 10, "bold"), fg=COLORS["primary"], bg=COLORS["card_bg"], padx=10, pady=10)
        card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(card, text="Opens separate Chrome window. Log in manually; passwords are never saved.", font=("Segoe UI", 8), fg=COLORS["text_secondary"], bg=COLORS["card_bg"], justify=tk.LEFT).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(card, bg=COLORS["card_bg"])
        btn_row.pack(fill=tk.X, pady=4)
        self.btn_launch = tk.Button(btn_row, text="🌐 Open Chrome (MeWe)", font=("Segoe UI", 9, "bold"), bg=COLORS["primary"], fg=COLORS["text_main"], relief=tk.FLAT, pady=6, command=self._on_launch_browser)
        self.btn_launch.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.btn_close = tk.Button(btn_row, text="✕ Close", font=("Segoe UI", 9), bg=COLORS["surface"], fg=COLORS["text_secondary"], relief=tk.FLAT, pady=6, command=self._on_close_browser)
        self.btn_close.pack(side=tk.RIGHT, padx=(4, 0))

    def _build_execution_card(self, parent):
        card = tk.LabelFrame(parent, text=" 2. AutoFollow Controls ", font=("Segoe UI", 10, "bold"), fg=COLORS["primary"], bg=COLORS["card_bg"], padx=10, pady=10)
        card.pack(fill=tk.X, pady=(0, 10))
        self.btn_start = tk.Button(card, text="▶ START AUTOFOLLOW", font=("Segoe UI", 10, "bold"), bg=COLORS["success"], fg=COLORS["text_main"], relief=tk.FLAT, pady=8, command=self._on_start_bot)
        self.btn_start.pack(fill=tk.X, pady=(0, 6))

        row = tk.Frame(card, bg=COLORS["card_bg"])
        row.pack(fill=tk.X)
        self.btn_pause = tk.Button(row, text="⏸ Pause", font=("Segoe UI", 9), bg=COLORS["surface"], fg=COLORS["text_main"], relief=tk.FLAT, pady=6, state=tk.DISABLED, command=self._on_pause_bot)
        self.btn_pause.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.btn_stop = tk.Button(row, text="⏹ Emergency Stop", font=("Segoe UI", 9, "bold"), bg=COLORS["danger"], fg=COLORS["text_main"], relief=tk.FLAT, pady=6, state=tk.DISABLED, command=self._on_stop_bot)
        self.btn_stop.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

    def _build_settings_card(self, parent):
        card = tk.LabelFrame(parent, text=" 3. Safe Delays & Limits ", font=("Segoe UI", 10, "bold"), fg=COLORS["primary"], bg=COLORS["card_bg"], padx=10, pady=8)
        card.pack(fill=tk.BOTH, expand=True)

        grid = tk.Frame(card, bg=COLORS["card_bg"])
        grid.pack(fill=tk.X, pady=(0, 6))
        tk.Label(grid, text="Min Delay (s):", bg=COLORS["card_bg"], fg=COLORS["text_secondary"], font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")
        self.ent_min = tk.Entry(grid, width=7, bg=COLORS["surface"], fg=COLORS["text_main"])
        self.ent_min.insert(0, str(self.config.min_delay_seconds))
        self.ent_min.grid(row=0, column=1, padx=(4, 10), pady=2)

        tk.Label(grid, text="Max Delay (s):", bg=COLORS["card_bg"], fg=COLORS["text_secondary"], font=("Segoe UI", 8)).grid(row=0, column=2, sticky="w")
        self.ent_max = tk.Entry(grid, width=7, bg=COLORS["surface"], fg=COLORS["text_main"])
        self.ent_max.insert(0, str(self.config.max_delay_seconds))
        self.ent_max.grid(row=0, column=3, padx=(4, 0), pady=2)

        tk.Label(grid, text="Max Follows:", bg=COLORS["card_bg"], fg=COLORS["text_secondary"], font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=4)
        self.ent_limit = tk.Entry(grid, width=7, bg=COLORS["surface"], fg=COLORS["text_main"])
        self.ent_limit.insert(0, str(self.config.max_follows_session))
        self.ent_limit.grid(row=1, column=1, padx=(4, 10), pady=4)

        self.var_scroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Auto-scroll to load next profiles", variable=self.var_scroll).pack(anchor="w", pady=2)
        tk.Label(card, text="🛡 Unfollow Protection: Active (Will NEVER click Unfollow)", font=("Segoe UI", 8), fg="#4EC9B0", bg=COLORS["card_bg"]).pack(anchor="w", pady=(4, 0))

    def _build_metrics_panel(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        frame.pack(fill=tk.X, pady=(0, 10))
        self.metrics = {}
        for key, title, val, color in [
            ("session", "FOLLOWS (SESSION)", "0 / 50", COLORS["primary"]),
            ("scanned", "PROFILES SCANNED", "0", COLORS["tag_info"]),
            ("skipped", "SKIPPED (FOLLOWING)", "0", COLORS["tag_warn"]),
            ("time", "SESSION TIME", "00:00", COLORS["text_secondary"])
        ]:
            b = tk.Frame(frame, bg=COLORS["card_bg"], bd=1, relief=tk.SOLID, padx=12, pady=8)
            b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
            tk.Label(b, text=title, font=("Segoe UI", 7, "bold"), fg=COLORS["text_secondary"], bg=COLORS["card_bg"]).pack(anchor="w")
            lbl = tk.Label(b, text=val, font=("Segoe UI", 16, "bold"), fg=color, bg=COLORS["card_bg"])
            lbl.pack(anchor="w")
            self.metrics[key] = lbl

    def _build_logs_panel(self, parent):
        card = tk.LabelFrame(parent, text=" Live Activity Logs & History ", font=("Segoe UI", 10, "bold"), fg=COLORS["primary"], bg=COLORS["card_bg"], padx=8, pady=8)
        card.pack(fill=tk.BOTH, expand=True)

        self.txt_logs = tk.Text(card, bg=COLORS["log_bg"], fg=COLORS["log_text"], font=("Consolas", 9), bd=0)
        self.txt_logs.pack(fill=tk.BOTH, expand=True)
        self.txt_logs.tag_config("SUCCESS", foreground=COLORS["tag_success"])
        self.txt_logs.tag_config("WARN", foreground=COLORS["tag_warn"])
        self.txt_logs.tag_config("ERROR", foreground=COLORS["tag_error"])
        self.txt_logs.tag_config("INFO", foreground=COLORS["tag_info"])

    def _on_launch_browser(self):
        self.bot.launch_browser()

    def _on_close_browser(self):
        self.bot.close_browser()

    def _on_start_bot(self):
        # Apply the values typed in the UI
        try:
            min_d = float(self.ent_min.get())
            max_d = float(self.ent_max.get())
            limit = int(self.ent_limit.get())
        except ValueError:
            messagebox.showerror("Invalid settings", "Delays must be numbers and Max Follows a whole number.")
            return
        if min_d > max_d:
            min_d, max_d = max_d, min_d
        self.config.min_delay_seconds = max(1.0, min_d)
        self.config.max_delay_seconds = max(1.0, max_d)
        self.config.max_follows_session = max(0, limit)  # 0 = unlimited
        self.config.auto_scroll_enabled = self.var_scroll.get()
        self.config.save()

        self.start_timestamp = time.time()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL)
        self.bot.start()

    def _on_pause_bot(self):
        self.bot.pause()

    def _on_stop_bot(self):
        self.bot.stop("Emergency Stop")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)

    def _queue_log(self, msg, level="INFO"): self.event_queue.put(("log", msg, level))
    def _queue_stats(self, s): self.event_queue.put(("stats", s))
    def _queue_status(self, st): self.event_queue.put(("status", st))
    def _queue_captcha(self, m): self.event_queue.put(("captcha", m))
    def _queue_stop(self, r): self.event_queue.put(("stop", r))

    def _process_event_queue(self):
        while not self.event_queue.empty():
            ev = self.event_queue.get_nowait()
            if ev[0] == "log":
                self._append_log(ev[1], ev[2])
            elif ev[0] == "status":
                self.lbl_status_pill.config(text=f"● Status: {ev[1]}")
            elif ev[0] == "stop":
                self.btn_start.config(state=tk.NORMAL)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.DISABLED)
                self._append_log(f"Stopped: {ev[1]}", "WARN")
            elif ev[0] == "captcha":
                messagebox.showwarning("CAPTCHA", ev[1])
            elif ev[0] == "stats":
                s = ev[1]
                self.metrics["session"].config(text=f"{s.get('session_follows', 0)} / {self.config.max_follows_session or '∞'}")
                self.metrics["scanned"].config(text=str(s.get("profiles_scanned", 0)))
                self.metrics["skipped"].config(text=str(s.get("skipped_already_following", 0)))
        self.root.after(100, self._process_event_queue)

    def _update_timer(self):
        if self.bot.is_running and self.start_timestamp:
            el = int(time.time() - self.start_timestamp)
            m, s = divmod(el, 60)
            self.metrics["time"].config(text=f"{m:02d}:{s:02d}")
        self.root.after(1000, self._update_timer)

    def _append_log(self, msg, level="INFO"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_logs.insert(tk.END, f"[{ts}] [{level}] {msg}\n", level)
        self.txt_logs.see(tk.END)

    def _on_close(self):
        self.bot.shutdown()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MeWeAutoFollowApp(root)
    root.mainloop()
