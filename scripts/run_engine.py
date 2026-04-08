"""
run_engine.py
-------------
Main entry point — pycromanager engine version (reference).

Uses multi_d_acquisition_events and Acquisition engine.
Slower than run_coresnap.py due to per-event engine overhead
but kept as reference. Edit acquisition/config.py to set
all acquisition parameters before running.

Usage:
    python scripts/run_engine.py
"""

import time
import os
import numpy as np
import tifffile

from pycromanager import Acquisition

from acquisition.config import (
    N_TIMEPOINTS, INTERVAL_S,
    BF_CHANNEL, BF_EXPOSURE_MS,
    FL_CHANNEL, FL_EXPOSURE_MS,
    Z_START_UM, Z_END_UM, Z_STEP_UM,
    SAVE_PATH, DATASET_NAME, PIXEL_SIZE_UM,
)
from acquisition.connect import connect, load_positions
from acquisition.stage import move_xy_z
from acquisition.autofocus import lock_pfs
from acquisition.imaging.engine import build_events
from acquisition.logger import init_log, log

# ── Initialize ──────────────────────────────────────────────
core, studio = connect()
positions, bf_only_indices, both_indices = load_positions(core, studio)

init_log()
log("=" * 60)
log(f"Acquisition started : {time.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"Timepoints          : {N_TIMEPOINTS}  |  Interval: {INTERVAL_S}s")
log(f"Positions           : {len(positions)}  |  BF-only: {sorted(bf_only_indices)}")
log("=" * 60)

z_slices = list(np.arange(Z_START_UM, Z_END_UM + Z_STEP_UM / 2, Z_STEP_UM))

# Image buffer for accumulate_image callback
image_buffer = {}

def accumulate_image(image, metadata):
    axes    = metadata.get("Axes", {})
    p_idx   = axes.get("position", 0)
    z_idx   = axes.get("z", 0)
    ch_idx  = axes.get("channel", 0)
    t_idx   = axes.get("time", 0)
    channel = metadata.get("Channel", f"ch{ch_idx}")
    key = (p_idx, t_idx, channel)
    if key not in image_buffer:
        image_buffer[key] = {}
    image_buffer[key][z_idx] = image
    return image, metadata

def save_buffer(t_idx):
    """Write buffered images to tifffile after each timepoint."""
    out_dir = os.path.join(SAVE_PATH, DATASET_NAME)
    os.makedirs(out_dir, exist_ok=True)
    for pos in positions:
        p_idx   = pos["index"]
        p_label = pos["label"]
        for channel in [BF_CHANNEL] + ([FL_CHANNEL] if p_idx in both_indices else []):
            key = (p_idx, t_idx, channel)
            if key in image_buffer:
                slices = [image_buffer[key][z] for z in sorted(image_buffer[key])]
                stack  = np.stack(slices, axis=0) if len(slices) > 1 else slices[0][np.newaxis]
                fname  = f"{p_label}_t{t_idx:03d}_{channel}.tif"
                tifffile.imwrite(
                    os.path.join(out_dir, fname), stack, imagej=True,
                    resolution=(1/PIXEL_SIZE_UM, 1/PIXEL_SIZE_UM),
                    metadata={"unit": "um", "axes": "ZYX",
                              "Channel": channel, "Position": p_label}
                )
                log(f"    {fname}  {stack.shape}")
    image_buffer.clear()

# ── Main loop ───────────────────────────────────────────────
for t_idx in range(N_TIMEPOINTS):
    t_loop_start = time.time()
    log(f"\n--- Timepoint {t_idx + 1}/{N_TIMEPOINTS}  [{time.strftime('%H:%M:%S')}] ---")

    pos_times    = []
    z_locked_map = {}

    for pos in positions:
        p_idx   = pos["index"]
        p_label = pos["label"]
        log(f"  [{p_idx}] {p_label}")

        t0 = time.time()
        move_xy_z(core, pos["x_um"], pos["y_um"], pos["z_um"])
        t_move = time.time() - t0
        log(f"    stage move : {t_move:.2f}s")

        t0 = time.time()
        z_locked = lock_pfs(core, pos, log_fn=log)
        z_locked_map[p_idx] = z_locked
        t_pfs = time.time() - t0
        log(f"    PFS lock   : {t_pfs:.2f}s  z={z_locked:.2f} um")

        pos_times.append({"label": p_label, "move_s": t_move, "pfs_s": t_pfs})

    events = build_events(
        positions, bf_only_indices, z_slices,
        BF_CHANNEL, BF_EXPOSURE_MS,
        FL_CHANNEL, FL_EXPOSURE_MS,
        Z_START_UM, Z_END_UM, Z_STEP_UM,
        t_idx, z_locked_map,
    )

    log(f"\n  Sending {len(events)} events...")
    t0 = time.time()
    with Acquisition(image_process_fn=accumulate_image,
                     show_display=False) as acq:
        acq.acquire(events)
    t_acq = time.time() - t0
    log(f"  Acquisition time : {t_acq:.2f}s")

    log("  Writing tiff files...")
    t0 = time.time()
    save_buffer(t_idx)
    t_write = time.time() - t0
    log(f"  Write time       : {t_write:.2f}s")

    t_loop = time.time() - t_loop_start
    log(f"\n  Position timing summary:")
    log(f"  {'Position':<10} {'Move (s)':>10} {'PFS (s)':>10}")
    log(f"  {'-' * 32}")
    for pt in pos_times:
        log(f"  {pt['label']:<10} {pt['move_s']:>10.2f} {pt['pfs_s']:>10.2f}")

    log(f"\n  Total timepoint : {t_loop:.2f}s")
    log(f"  Breakdown       : "
        f"moves={sum(p['move_s'] for p in pos_times):.2f}s  "
        f"pfs={sum(p['pfs_s'] for p in pos_times):.2f}s  "
        f"acq={t_acq:.2f}s  write={t_write:.2f}s")

    wait_s = max(0, INTERVAL_S - t_loop)
    if t_idx < N_TIMEPOINTS - 1:
        log(f"  Waiting         : {wait_s:.1f}s until next timepoint...")
        time.sleep(wait_s)

log("\n" + "=" * 60)
log(f"Acquisition complete: {time.strftime('%Y-%m-%d %H:%M:%S')}")
log("=" * 60)
