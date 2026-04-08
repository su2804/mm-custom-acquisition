# mm-custom-acquisition

Custom Micro-Manager acquisition scripts for multi-position, multi-channel, z-stack time-lapse imaging using Pycromanager.

## Hardware

Developed and tested on:

- **Microscope:** Nikon Ti-E
- **Camera:** Photometrics Prime 95B (16-bit)
- **Spinning disk:** Yokogawa CSUW1
- **Light source:** Lumencor SPECTRAX
- **Autofocus:** Nikon PFS (TIPFSStatus / TIPFSOffset)
- **Stages:** TIXYDrive (XY), TIZDrive (Z)
- **DAQ:** NI100x DigitalIO

## Acquisition Logic

- N timepoints at a fixed interval
- Last 2 positions → BF only (A_phase, single slice at PFS-locked z)
- All other positions → BF (A_phase, single slice) + 488nm z-stack
- PFS locked at each position before imaging
- XY and Z moved simultaneously (MDA-style)
- Stage settling via tolerance polling (not fixed timeout)

## Two Implementations

### 1. Core Snap (`scripts/run_coresnap.py`) — Recommended
Bypasses the Pycromanager acquisition engine entirely. Uses `core.snap_image()` directly in a tight loop for minimal per-slice overhead. Fastest option for z-stacks.

### 2. Engine (`scripts/run_engine.py`) — Reference
Uses Pycromanager's `multi_d_acquisition_events` and `Acquisition` engine. Slower due to per-event overhead but useful as a reference or for future hardware sequencing support.

## Output

Images saved as ImageJ-compatible hyperstacks via tifffile:

```
SAVE_PATH/DATASET_NAME/
  Pos0_t000_A_phase.tif     # single z-slice
  Pos0_t000_488nm.tif       # z-stack (Z, Y, X)
  Pos1_t000_A_phase.tif
  Pos1_t000_488nm.tif
  Pos2_t000_A_phase.tif     # BF only
  Pos3_t000_A_phase.tif     # BF only
  Pos0_t001_A_phase.tif
  ...
  timing_log.txt            # detailed per-position timing
```

## Timing Log Example

```
============================================================
Acquisition started : 2026-04-07 16:54:58
Timepoints          : 5  |  Interval: 180s
Positions           : 4  |  BF-only: [2, 3]
============================================================
--- Timepoint 1/5  [16:54:58] ---
  [0] Pos0
    stage move : 0.29s
    PFS lock   : 0.02s  z=5812.80 um
    -> BF + 488nm z-stack (61 slices)
    saved Pos0_t000_A_phase.tif  (1, 1200, 1200)
    saved Pos0_t000_488nm.tif  (61, 1200, 1200)
    acquire+save : 46.80s

  Position timing summary:
  Position     Move (s)    PFS (s)   Img+Save (s)
  Pos0             0.29       0.02          46.80

  Total timepoint : 51.84s
  Breakdown       : moves=1.22s  pfs=0.04s  img+save=46.80s
  Waiting         : 128.2s until next timepoint...
```

## Installation

```bash
# Clone the repo
git clone https://github.com/su2804/mm-custom-acquisition.git
cd mm-custom-acquisition

# Create conda environment
conda create -n pycromanager_env python=3.11
conda activate pycromanager_env

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Open Micro-Manager 2.0 and load your hardware config
2. Set up your position list in MM
3. Start the ZMQ server: **Plugins → Developer Tools → Start ZMQ server**
4. Edit `acquisition/config.py` to set your parameters (SAVE_PATH, N_TIMEPOINTS, etc.)
5. Run:

```bash
python scripts/run_coresnap.py
```

## Parameters

All parameters are defined in `acquisition/config.py`:

| Parameter | Description | Default |
|---|---|---|
| `SAVE_PATH` | Root directory for saving images | `path/to/your/data` |
| `DATASET_NAME` | Subfolder name | `custom_acq` |
| `N_TIMEPOINTS` | Number of timepoints | `5` |
| `INTERVAL_S` | Interval between timepoints (seconds) | `180` |
| `BF_CHANNEL` | Brightfield channel config name | `A_phase` |
| `BF_EXPOSURE_MS` | Brightfield exposure (ms) | `10.0` |
| `FL_CHANNEL` | Fluorescence channel config name | `488nm` |
| `FL_EXPOSURE_MS` | Fluorescence exposure (ms) | `200.0` |
| `Z_START_UM` | Z-stack start offset from PFS z (µm) | `-9.0` |
| `Z_END_UM` | Z-stack end offset from PFS z (µm) | `9.0` |
| `Z_STEP_UM` | Z-stack step size (µm) | `0.3` |
| `XY_TOLERANCE_UM` | XY stage settle tolerance (µm) | `2.0` |
| `Z_TOLERANCE_UM` | Z stage settle tolerance (µm) | `0.5` |
| `PFS_TIMEOUT_S` | PFS lock timeout (seconds) | `15` |

## 2D vs Z-stack

To acquire single z-slices only (no z-stack), set in the script:

```python
Z_START_UM = 0.0
Z_END_UM   = 0.0
Z_STEP_UM  = 1
```

## Known Limitations & Future Work

- **Z-stack speed:** Bottleneck is TIZDrive settle time (~0.65s/slice). Hardware triggering via NI DAQ + Expose Out cable would reduce this to exposure time only.
- **Channel switching:** Lumencor SPECTRAX + CSUW1 filter wheel switching adds ~1s overhead per channel change.
- **Planned optimizations:**
  - Pre-position Z to stack start during XY move
  - Parallel image save during stage move (threading)
  - Hardware-triggered z-stepping via NI DAQ

## Requirements

- Micro-Manager 2.0.3+
- Python 3.11
- See `requirements.txt`
