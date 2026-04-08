"""
engine.py
---------
Pycromanager acquisition engine based imaging using
multi_d_acquisition_events. Slower than core_snap due to
per-event engine overhead (~1s/event) but kept as reference
and for future hardware sequencing support.
"""

from pycromanager import Acquisition, multi_d_acquisition_events
from ..config import CHANNEL_GROUP


def build_events(positions, bf_only_indices, z_slices,
                 bf_channel, bf_exposure_ms,
                 fl_channel, fl_exposure_ms,
                 z_start_um, z_end_um, z_step_um,
                 t_idx, z_locked_map):
    """
    Build pycromanager event list for one timepoint.

    Parameters
    ----------
    positions : list of dict
        Position dicts with index, label, x_um, y_um, z_um
    bf_only_indices : set
        Position indices that get BF only
    z_slices : list of float
        Z offsets for fluorescence stack
    bf_channel, fl_channel : str
        MM config preset names
    bf_exposure_ms, fl_exposure_ms : float
        Exposures in ms
    z_start_um, z_end_um, z_step_um : float
        Z-stack range and step
    t_idx : int
        Current timepoint index
    z_locked_map : dict
        {p_idx: z_locked_um} — PFS-locked Z per position

    Returns
    -------
    events : list of dict
    """
    events = []

    for pos in positions:
        p_idx    = pos["index"]
        z_locked = z_locked_map[p_idx]

        if p_idx in bf_only_indices:
            bf_events = multi_d_acquisition_events(
                channel_group=CHANNEL_GROUP,
                channels=[bf_channel],
                channel_exposures_ms=[bf_exposure_ms],
                z_start=z_locked,
                z_end=z_locked,
                z_step=1,
                order="tcz",
            )
            for e in bf_events:
                e["axes"]["time"]     = t_idx
                e["axes"]["position"] = p_idx
                e["x"]               = pos["x_um"]
                e["y"]               = pos["y_um"]
                events.append(e)

        else:
            # BF single slice
            bf_events = multi_d_acquisition_events(
                channel_group=CHANNEL_GROUP,
                channels=[bf_channel],
                channel_exposures_ms=[bf_exposure_ms],
                z_start=z_locked,
                z_end=z_locked,
                z_step=1,
                order="tcz",
            )
            for e in bf_events:
                e["axes"]["time"]     = t_idx
                e["axes"]["position"] = p_idx
                e["x"]               = pos["x_um"]
                e["y"]               = pos["y_um"]
                events.append(e)

            # FL z-stack
            fl_events = multi_d_acquisition_events(
                channel_group=CHANNEL_GROUP,
                channels=[fl_channel],
                channel_exposures_ms=[fl_exposure_ms],
                z_start=z_locked + z_start_um,
                z_end=z_locked + z_end_um,
                z_step=z_step_um,
                order="tcz",
            )
            for e in fl_events:
                e["axes"]["time"]     = t_idx
                e["axes"]["position"] = p_idx
                e["x"]               = pos["x_um"]
                e["y"]               = pos["y_um"]
                events.append(e)

    return events


def run_acquisition_engine(events, image_process_fn=None):
    """
    Run pycromanager Acquisition engine with given events.
    Returns after all events complete.
    """
    with Acquisition(image_process_fn=image_process_fn,
                     show_display=False) as acq:
        acq.acquire(events)
