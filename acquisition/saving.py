"""
saving.py
---------
Save images as ImageJ-compatible hyperstacks via tifffile.
"""

import os
import numpy as np
import tifffile
from .config import SAVE_PATH, DATASET_NAME, PIXEL_SIZE_UM


def save_stack(p_label, t_idx, channel, images):
    """
    Save a list of 2D numpy arrays as an ImageJ-compatible hyperstack.

    Parameters
    ----------
    p_label : str
        Position label (e.g. "Pos0")
    t_idx : int
        Timepoint index
    channel : str
        Channel name (e.g. "A_phase", "488nm")
    images : list of 2D np.ndarray
        Images ordered by z index

    Returns
    -------
    fname : str
        Saved filename
    shape : tuple
        Shape of saved stack (Z, Y, X)
    """
    out_dir = os.path.join(SAVE_PATH, DATASET_NAME)
    os.makedirs(out_dir, exist_ok=True)

    fname = f"{p_label}_t{t_idx:03d}_{channel}.tif"
    fpath = os.path.join(out_dir, fname)

    stack = np.stack(images, axis=0) if len(images) > 1 else images[0][np.newaxis]

    tifffile.imwrite(
        fpath,
        stack,
        imagej=True,
        resolution=(1 / PIXEL_SIZE_UM, 1 / PIXEL_SIZE_UM),
        metadata={
            "unit"     : "um",
            "axes"     : "ZYX",
            "Channel"  : channel,
            "Position" : p_label,
            "TimePoint": t_idx,
        }
    )
    return fname, stack.shape
