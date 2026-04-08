"""
run_coresnap.py
---------------
Main entry point — core snap version (recommended).

Bypasses pycromanager engine for imaging, uses core.snap_image()
directly for fast z-stacks. Edit acquisition/config.py to set
all acquisition parameters before running.

Usage:
    python scripts/run_coresnap.py
"""

import time
import numpy as np

from acquisition.config import (
    N_TIMEPOINTS, INTERVAL_S,
    BF_CHANNEL, BF_EXPOSURE_MS,
    FL_CHANNEL, FL_EXPOSURE_MS,
    Z_START_UM, Z_END_UM, Z_STEP_UM,
)
from acquisition.connect import connect, load_positions
from acquisition.stage import move_xy_z
from acquisition.autofocus import lock_pfs
from acquisition.imaging.core_snap import acquire_single, acquire_zstack
from acquisition.saving import save_stack
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

z_offsets = list(np.arange(Z_START_UM, Z_END_UM + Z_STEP_UM / 2, Z_STEP_UM))
n_slices  = len(z_offsets)

# ── Main loop ───────────────────────────────────────────────
for t_idx in range(N_TIMEPOINTS):
    t_loop_start = time.time()
    log(f"\n--- Timepoint {t_idx + 1}/{N_TIMEPOINTS}  [{time.strftime('%H:%M:%S')}] ---")

    pos_times = []

    for pos in positions:
        p_idx   = pos["index"]
        p_label = pos["label"]
        log(f"  [{p_idx}] {p_label}")

        # Stage move
        t0 = time.time()
        move_xy_z(core, pos["x_um"], pos["y_um"], pos["z_um"])
        t_move = time.time() - t0
        log(f"    stage move : {t_move:.2f}s")

        # PFS lock
        t0 = time.time()
        z_locked = lock_pfs(core, pos, log_fn=log)
        t_pfs = time.time() - t0
        log(f"    PFS lock   : {t_pfs:.2f}s  z={z_locked:.2f} um")

        # Acquire and save
        t0 = time.time()

        if p_idx in bf_only_indices:
            log(f"    -> BF only")
            bf_img = acquire_single(core, BF_CHANNEL, BF_EXPOSURE_MS)
            fname, shape = save_stack(p_label, t_idx, BF_CHANNEL, [bf_img])
            log(f"    saved {fname}  {shape}")

        else:
            log(f"    -> BF + {FL_CHANNEL} z-stack ({n_slices} slices)")

            bf_img = acquire_single(core, BF_CHANNEL, BF_EXPOSURE_MS)
            fname, shape = save_stack(p_label, t_idx, BF_CHANNEL, [bf_img])
            log(f"    saved {fname}  {shape}")

            fl_imgs = acquire_zstack(core, FL_CHANNEL, FL_EXPOSURE_MS,
                                     z_locked, z_offsets)
            fname, shape = save_stack(p_label, t_idx, FL_CHANNEL, fl_imgs)
            log(f"    saved {fname}  {shape}")

        t_img = time.time() - t0
        log(f"    acquire+save : {t_img:.2f}s")

        pos_times.append({
            "label" : p_label,
            "move_s": t_move,
            "pfs_s" : t_pfs,
            "img_s" : t_img,
        })

    # Timepoint summary
    t_loop = time.time() - t_loop_start
    log(f"\n  Position timing summary:")
    log(f"  {'Position':<10} {'Move (s)':>10} {'PFS (s)':>10} {'Img+Save (s)':>14}")
    log(f"  {'-' * 46}")
    for pt in pos_times:
        log(f"  {pt['label']:<10} {pt['move_s']:>10.2f} {pt['pfs_s']:>10.2f} {pt['img_s']:>14.2f}")

    log(f"\n  Total timepoint : {t_loop:.2f}s")
    log(f"  Breakdown       : "
        f"moves={sum(p['move_s'] for p in pos_times):.2f}s  "
        f"pfs={sum(p['pfs_s'] for p in pos_times):.2f}s  "
        f"img+save={sum(p['img_s'] for p in pos_times):.2f}s")

    wait_s = max(0, INTERVAL_S - t_loop)
    if t_idx < N_TIMEPOINTS - 1:
        log(f"  Waiting         : {wait_s:.1f}s until next timepoint...")
        time.sleep(wait_s)

log("\n" + "=" * 60)
log(f"Acquisition complete: {time.strftime('%Y-%m-%d %H:%M:%S')}")
log("=" * 60)
