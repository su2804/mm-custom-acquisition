"""
config.py
---------
All user-editable acquisition parameters.
Edit this file before running either script.
"""

# ── Save location ──────────────────────────────────────────
SAVE_PATH    = r"F:\Sofia\WI25\pH\DiffpH"
DATASET_NAME = "custom_acq"

# ── Timepoints ─────────────────────────────────────────────
N_TIMEPOINTS = 5
INTERVAL_S   = 180       # seconds between timepoints

# ── Channels ───────────────────────────────────────────────
CHANNEL_GROUP  = "Confocal"
BF_CHANNEL     = "A_phase"
BF_EXPOSURE_MS = 10.0
FL_CHANNEL     = "488nm"
FL_EXPOSURE_MS = 200.0

# ── Z-stack ────────────────────────────────────────────────
# Set Z_START_UM = Z_END_UM = 0, Z_STEP_UM = 1 for 2D acquisition
Z_START_UM = -9.0
Z_END_UM   =  9.0
Z_STEP_UM  =  0.3
PIXEL_SIZE_UM = 0.1123

# ── Hardware device names ──────────────────────────────────
XY_STAGE       = "TIXYDrive"
Z_STAGE        = "TIZDrive"
PFS_DEVICE     = "TIPFSStatus"
PFS_OFFSET_DEV = "TIPFSOffset"

# ── Stage settling ─────────────────────────────────────────
XY_TOLERANCE_UM = 2.0
Z_TOLERANCE_UM  = 0.5
STAGE_TIMEOUT_S = 10

# ── PFS ────────────────────────────────────────────────────
PFS_POLL_MS   = 50
PFS_TIMEOUT_S = 15

# ── Position partitioning ──────────────────────────────────
# Last N_BF_ONLY positions will be BF only
# All others will get BF + FL z-stack
N_BF_ONLY = 2
