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

from config import AppConfig
from bot import MeWeBot

# Windows 11 Fluent Dark Palette

COLORS = {
    "bg_dark": "#1E1E1E",
    "surface": "#252526",
    "card_bg": "#2D2D30",
    "card_border": "#3E3E42",
    "primary": "#0078D4",
    "primary_hover": "#1E90FF",
    "success": "#107C41",
    "success_hover": "#138847",
    "danger": "#C42B1C",
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
