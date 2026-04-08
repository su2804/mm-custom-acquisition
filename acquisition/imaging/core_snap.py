"""
core_snap.py
------------
Fast imaging via core.snap_image() — bypasses the Pycromanager
acquisition engine entirely for minimal per-slice overhead.

This is the recommended approach for z-stacks where engine overhead
(~1s/event) would dominate over actual exposure time.
"""

import numpy as np
from ..config import CHANNEL_GROUP, Z_STAGE
from ..stage import wait_for_z


def snap_frame(core):
    """Snap one image and return as 2D numpy array."""
    core.snap_image()
    tagged = core.get_tagged_image()
    return np.reshape(tagged.pix, [tagged.tags["Height"], tagged.tags["Width"]])


def acquire_single(core, channel, exposure_ms):
    """
    Apply config preset, set exposure, snap one image.
    Returns 2D numpy array.
    """
    core.set_config(CHANNEL_GROUP, channel)
    core.wait_for_config(CHANNEL_GROUP, channel)
    core.set_exposure(exposure_ms)
    return snap_frame(core)


def acquire_zstack(core, channel, exposure_ms, z_center, z_offsets):
    """
    Acquire a z-stack via core.snap_image() in a tight loop.

    Applies config and exposure once, then loops:
        move Z -> wait for settle -> snap -> next slice

    Returns Z stage to z_center after stack.

    Parameters
    ----------
    core : Core
        Pycromanager Core object
    channel : str
        MM config preset name (e.g. "488nm")
    exposure_ms : float
        Exposure time in ms
    z_center : float
        PFS-locked absolute Z position (um)
    z_offsets : list of float
        Z offsets relative to z_center (um)

    Returns
    -------
    images : list of 2D np.ndarray
        Images ordered by z_offsets index
    """
    core.set_config(CHANNEL_GROUP, channel)
    core.wait_for_config(CHANNEL_GROUP, channel)
    core.set_exposure(exposure_ms)

    images = []
    for z_offset in z_offsets:
        z_abs = z_center + z_offset
        core.set_position(Z_STAGE, z_abs)
        wait_for_z(core, z_abs)
        core.snap_image()
        tagged = core.get_tagged_image()
        images.append(np.reshape(tagged.pix,
                      [tagged.tags["Height"], tagged.tags["Width"]]))

    # Return to center after stack
    core.set_position(Z_STAGE, z_center)
    return images
