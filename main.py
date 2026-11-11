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
    "primary": "#0078D4",       # Windows Accent Blue
    "primary_hover": "#1E90FF",
    "success": "#107C41",       # Fluent Green
    "success_hover": "#138847",
    "danger": "#C42B1C",        # Fluent Red
    "danger_hover": "#D83B01",
    "warning": "#FCE100",
