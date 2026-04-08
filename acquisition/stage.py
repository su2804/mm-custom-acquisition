"""
stage.py
--------
MDA-style stage movement helpers.
XY and Z moved simultaneously, settling by tolerance not fixed timeout.
"""

import time
from .config import (XY_STAGE, Z_STAGE,
                     XY_TOLERANCE_UM, Z_TOLERANCE_UM, STAGE_TIMEOUT_S)


def wait_for_xy(core, target_x, target_y,
                tolerance=XY_TOLERANCE_UM, timeout=STAGE_TIMEOUT_S):
    """
    Poll XY position every 10ms until within tolerance of target.
    Mirrors MDA's ToleranceX/Y settling logic.
    Returns True if settled, False if timed out.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        x = core.get_x_position(XY_STAGE)
        y = core.get_y_position(XY_STAGE)
        if abs(x - target_x) < tolerance and abs(y - target_y) < tolerance:
            return True
        time.sleep(0.01)
    return False


def wait_for_z(core, target_z,
               tolerance=Z_TOLERANCE_UM, timeout=STAGE_TIMEOUT_S):
    """
    Poll Z position every 5ms until within tolerance of target.
    Returns True if settled, False if timed out.
    """
    time.sleep(0.05)   # minimum settle time
    deadline = time.time() + timeout
    while time.time() < deadline:
        z = core.get_position(Z_STAGE)
        if abs(z - target_z) < tolerance:
            return True
        time.sleep(0.005)
    return False


def move_xy_z(core, x_um, y_um, z_um):
    """
    Start XY and Z moves simultaneously then wait for both to settle.
    Mirrors MDA's simultaneous move behavior.
    """
    core.set_xy_position(XY_STAGE, x_um, y_um)
    core.set_position(Z_STAGE, z_um)
    wait_for_xy(core, x_um, y_um)
    wait_for_z(core, z_um)
