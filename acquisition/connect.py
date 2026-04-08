"""
connect.py
----------
Connect to Micro-Manager and load position list.
"""

from pycromanager import Core, Studio
from .config import XY_STAGE, Z_STAGE, PFS_OFFSET_DEV, N_BF_ONLY


def connect():
    """
    Connect to running MM instance.
    Returns (core, studio) or raises SystemExit if connection fails.
    """
    print("Connecting to Micro-Manager...")
    try:
        core   = Core()
        studio = Studio()
        print(f"  Connected  |  MM version: {core.get_version_info()}")
        core.set_property("Core", "TimeoutMs", "30000")
        return core, studio
    except Exception as e:
        print(f"  Could not connect: {e}")
        print("  Make sure:")
        print("    1. Micro-Manager 2.0 is open")
        print("    2. ZMQ server is running (Plugins -> Developer Tools -> Start ZMQ server)")
        print("    3. Port 4827 is not blocked by a firewall")
        raise SystemExit(1)


def load_positions(core, studio):
    """
    Load position list from MM GUI.
    Physically moves to each position to read coordinates.
    Returns (positions, bf_only_indices, both_indices).
    """
    position_list = studio.get_position_list_manager().get_position_list()
    n_positions   = position_list.get_number_of_positions()

    if n_positions == 0:
        print("ERROR: No positions in MM position list. Please load positions first.")
        raise SystemExit(1)

    print(f"Found {n_positions} positions.")

    positions = []
    for i in range(n_positions):
        pos   = position_list.get_position(i)
        label = pos.get_label()
        pos.go_to_position(pos, core)
        core.wait_for_device(XY_STAGE)
        x_um       = core.get_x_position(XY_STAGE)
        y_um       = core.get_y_position(XY_STAGE)
        z_um       = core.get_position(Z_STAGE)
        pfs_offset = core.get_position(PFS_OFFSET_DEV)
        positions.append({
            "index"     : i,
            "label"     : label,
            "x_um"      : x_um,
            "y_um"      : y_um,
            "z_um"      : z_um,
            "pfs_offset": pfs_offset,
        })
        print(f"  [{i}] {label}  XY=({x_um:.1f}, {y_um:.1f})  Z={z_um:.1f}  PFS={pfs_offset:.2f}")

    bf_only_indices = set(range(n_positions - N_BF_ONLY, n_positions))
    both_indices    = set(range(0, n_positions - N_BF_ONLY))
    print(f"\nBF-only : {sorted(bf_only_indices)}")
    print(f"BF+FL   : {sorted(both_indices)}")

    return positions, bf_only_indices, both_indices
