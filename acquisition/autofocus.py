"""
autofocus.py
------------
Nikon PFS locking helpers.
"""

import time
from .config import PFS_DEVICE, PFS_OFFSET_DEV, PFS_POLL_MS, PFS_TIMEOUT_S


def wait_for_pfs_lock(core, log_fn=print, timeout=PFS_TIMEOUT_S):
    """
    Poll TIPFSStatus until locked or timeout.
    Returns True if locked, False if timed out.
    """
    deadline    = time.time() + timeout
    first_check = True
    while time.time() < deadline:
        try:
            status = core.get_property(PFS_DEVICE, "Status")
        except Exception:
            status = ""
        if first_check:
            first_check = False
        if any(s in status for s in ["Within range", "Locked", "In Focus", "lock"]):
            return True
        time.sleep(PFS_POLL_MS / 1000.0)
    return False


def lock_pfs(core, pos_dict, log_fn=print):
    """
    Set PFS offset for position and wait for lock.
    Returns absolute Z (um) after locking.
    """
    core.set_position(PFS_OFFSET_DEV, pos_dict["pfs_offset"])
    locked = wait_for_pfs_lock(core, log_fn)
    if not locked:
        log_fn(f"    WARNING: PFS did not lock at {pos_dict['label']} -- continuing.")
    return core.get_position("TIZDrive")
