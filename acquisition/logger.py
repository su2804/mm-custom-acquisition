"""
logger.py
---------
Timing log — prints to console and writes to timing_log.txt.
"""

import os
import time
from .config import SAVE_PATH, DATASET_NAME

_log_path = None


def init_log():
    """Initialize log file. Call once before acquisition starts."""
    global _log_path
    out_dir    = os.path.join(SAVE_PATH, DATASET_NAME)
    os.makedirs(out_dir, exist_ok=True)
    _log_path  = os.path.join(out_dir, "timing_log.txt")


def log(msg):
    """Print to console and append to timing_log.txt."""
    print(msg)
    if _log_path is not None:
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
