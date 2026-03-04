"""
datasets.py
===========
Session / stint file registry for iRacing telemetry analysis.

IMPORTANT — Multi-file stints
------------------------------
A stint value may be either:
  • a single filename  (str)       → loaded as-is
  • a list of filenames (list[str]) → files are loaded and CONCATENATED
    in list order; lap numbers are offset so each file's laps append
    seamlessly after the previous file's laps.

This pattern fixes the silent data-loss that occurred when two IBT files
were registered under the same dict key (Python silently discards the
earlier duplicate key).

Example — two files forming a single stint:
    "Rodrigo": {
        "stint_1": [
            "file_part_a.ibt",
            "file_part_b.ibt",
        ]
    }
"""

from pathlib import Path

DATASETS: dict = {

    # =====================================================================
    # Mazda MX-5 — Charlotte Roval 2025
    # =====================================================================
    "charlotte_roval_2025": {
        "base_path": "G:/Meu Drive/Estudos/Datasets - Simracing/Mazda - Charlotte/",
        "car":       "Mazda MX-5",
        "sessions": {
            "Tomaz": {
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2025-11-26 13-56-41.ibt",
                "stint_2": "mx5 mx52016_charlotte 2025 roval2025 2026-03-01 17-16-27.ibt",
                "stint_3": "mx5 mx52016_charlotte 2025 roval2025 2026-03-01 16-20-04.ibt",
            },
            "Morsinaldo": {
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-01-27 16-13-55(Morsinaldo).ibt",
                "stint_2": "mx5 mx52016_charlotte 2025 roval2025 2026-01-28 15-24-41(Morsinaldo).ibt",
            },
            "Rodrigo": {
                # Previously, two stint_1 keys caused silent data loss.
                # Both files are now a single list → loader concatenates them.
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-02-08 15-06-22(Rodrigo).ibt",
            },
        },
    },

    # =====================================================================
    # Toyota GR86 — Summit Point
    # =====================================================================
    "summit_point": {
        "base_path": "G:/Meu Drive/Estudos/Datasets - Simracing/Toyota GR86 - Summit Point/",
        "car":       "Toyota GR86",
        "sessions": {
            "Tomaz": {
                "stint_1": "toyotagr86_summit summit raceway 2026-01-27 22-21-35.ibt",
            },
            "Morsinaldo": {
                "stint_1": "toyotagr86_summit summit raceway 2026-01-28 16-03-13(Morsinaldo).ibt",
                "stint_2": "toyotagr86_summit summit raceway 2026-01-30 08-56-59(Morsinaldo).ibt",
            },
            "Rodrigo": {
                # FIX: both files that previously shared the "stint_1" key
                # are now correctly declared as a concatenated list.
                "stint_1": [
                    "toyotagr86_summit summit raceway 2026-03-01 22-00-14(Rodrigo).ibt",
                    "toyotagr86_summit summit raceway 2026-03-01 21-47-29(Rodrigo).ibt",
                ],
            },
        },
    },
}


def resolve_stint_files(track_id: str, driver: str, stint: str) -> list[Path]:
    """
    Return an ordered list of Path objects for a given (track, driver, stint).

    Handles both single-file (str) and multi-file (list[str]) stint values.

    Parameters
    ----------
    track_id : str   Key in DATASETS, e.g. "summit_point"
    driver   : str   Real driver name, e.g. "Rodrigo"
    stint    : str   Stint key, e.g. "stint_1"

    Returns
    -------
    list[Path]  Absolute paths in file-concatenation order.
    """
    cfg       = DATASETS[track_id]
    base_path = Path(cfg["base_path"])
    entry     = cfg["sessions"][driver][stint]

    if isinstance(entry, str):
        return [base_path / entry]
    elif isinstance(entry, list):
        return [base_path / f for f in entry]
    else:
        raise TypeError(
            f"Unexpected stint value type {type(entry)} for "
            f"({track_id}, {driver}, {stint})"
        )
