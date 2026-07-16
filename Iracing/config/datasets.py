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
                "stint_2":[
                    "mx5 mx52016_charlotte 2025 roval2025 2026-03-01 17-16-27.ibt",
                    "mx5 mx52016_charlotte 2025 roval2025 2026-03-01 16-20-04.ibt",
                ],
                "stint_3": "mx5 mx52016_charlotte 2025 roval2025 2026-05-11 22-43-15.ibt",
                "stint_4": "mx5 mx52016_charlotte 2025 roval2025 2026-05-11 23-11-08.ibt",
            },
            "Morsinaldo": {
                "warmp-up": "mx5 mx52016_charlotte 2025 roval2025 2026-07-03 15-02-02(Morsinaldo-aquecimento).ibt",
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-07-03 15-23-22(Morsinaldo-stint1).ibt",
                "stint_2":"mx5 mx52016_charlotte 2025 roval2025 2026-07-03 17-26-36(Morsinaldo-stint2).ibt",
                "stint_3": "mx5 mx52016_charlotte 2025 roval2025 2026-07-03 17-54-10(Morsinaldo-stint3).ibt",
                "stint_4": "mx5 mx52016_charlotte 2025 roval2025 2026-07-03 18-06-38(Morsinaldo-stint4).ibt",
                "stint_5": "mx5 mx52016_charlotte 2025 roval2025 2026-07-03 18-20-07(Morsinaldo-stint5).ibt"
            },
            "Rodrigo": {
                # Previously, two stint_1 keys caused silent data loss.
                # Both files are now a single list → loader concatenates them.
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-02-08 15-06-22(Rodrigo).ibt",
            },
            "Thallys": {
                "warmup": "mx5 mx52016_charlotte 2025 roval2025 2026-07-01 19-43-55(aquecimento).ibt",
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-07-01 19-54-22(Thallys-stint1).ibt",
                "stint_2": "mx5 mx52016_charlotte 2025 roval2025 2026-07-01 20-24-18(Thallys-stint2).ibt",
                "stint_3": "mx5 mx52016_charlotte 2025 roval2025 2026-07-01 20-59-35(Thallys-stint3).ibt",
                "stint_4": "mx5 mx52016_charlotte 2025 roval2025 2026-07-01 21-17-46(Thallys-stint4).ibt",
                "stint_5": "mx5 mx52016_charlotte 2025 roval2025 2026-07-01 21-38-37(Thallys-stint5).ibt",
            },
            "Igor": {
                "warmup": "mx5 mx52016_charlotte 2025 roval2025 2026-07-11 14-33-08(igor-aquecimento).ibt",
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-07-11 14-53-43(igor-stint1).ibt",
                "stint_2": "mx5 mx52016_charlotte 2025 roval2025 2026-07-11 15-15-18(igor-stint2).ibt",
                "stint_3": "mx5 mx52016_charlotte 2025 roval2025 2026-07-11 15-36-02(igor-stint3).ibt",
                "stint_4": "mx5 mx52016_charlotte 2025 roval2025 2026-07-11 15-43-42(igor-stint4).ibt",
                "stint_5": "mx5 mx52016_charlotte 2025 roval2025 2026-07-11 15-58-02(igor-stint5).ibt",
            },
            "Hilton": {
                "warmup": "mx5 mx52016_charlotte 2025 roval2025 2026-07-06 12-34-29(hilton-aquecimento).ibt",
                "stint_1": "mx5 mx52016_charlotte 2025 roval2025 2026-07-06 12-52-30(hilton-stint1).ibt",
                "stint_2": "mx5 mx52016_charlotte 2025 roval2025 2026-07-06 14-23-38(hilton-stint2).ibt",
                "stint_3": "mx5 mx52016_charlotte 2025 roval2025 2026-07-06 14-43-21(hilton-stint3).ibt",
                "stint_4": "mx5 mx52016_charlotte 2025 roval2025 2026-07-06 15-00-26(hilton-stint4).ibt",
                "stint_5": "mx5 mx52016_charlotte 2025 roval2025 2026-07-06 15-21-27(hilton-stint5).ibt",
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
                "warmup":  "toyotagr86_summit summit raceway 2026-07-16 17-18-40(Tomaz-aquecimento).ibt",
                "stint_1": "toyotagr86_summit summit raceway 2026-07-16 17-32-50(Tomaz-stint1).ibt",
                "stint_2": "toyotagr86_summit summit raceway 2026-07-16 17-53-00(Tomaz-stint2).ibt",
                "stint_3": "toyotagr86_summit summit raceway 2026-07-16 18-08-13(Tomaz-stint3).ibt",
                "stint_4": "toyotagr86_summit summit raceway 2026-07-16 18-26-28(Tomaz-stint4).ibt",
                "stint_5": "toyotagr86_summit summit raceway 2026-07-16 18-39-20(Tomaz-stint5).ibt",
            },
            "Morsinaldo": {
                "stint_1": "toyotagr86_summit summit raceway 2026-07-06 16-03-42(morsinaldo-stint1).ibt",
                "stint_2": "toyotagr86_summit summit raceway 2026-07-06 16-25-28(morsinaldo-stint2).ibt",
                "stint_3": "toyotagr86_summit summit raceway 2026-07-06 16-38-47(morsinaldo-stint3).ibt",
                "stint_4": "toyotagr86_summit summit raceway 2026-07-06 17-01-50(morsinaldo-stint4).ibt",
                "stint_5": "toyotagr86_summit summit raceway 2026-07-06 17-13-21(morsinaldo-stint5).ibt",
            },
            "Rodrigo": {
                # FIX: both files that previously shared the "stint_1" key
                # are now correctly declared as a concatenated list.
                "stint_1": [
                    "toyotagr86_summit summit raceway 2026-03-01 22-00-14(Rodrigo).ibt",
                    "toyotagr86_summit summit raceway 2026-03-01 21-47-29(Rodrigo).ibt",
                ],
            },
            "Thallys": {
                "aquecimento": "toyotagr86_summit summit raceway 2026-07-06 20-19-23(Thallys-aquecimento).ibt",
                "stint_1": "toyotagr86_summit summit raceway 2026-07-06 20-30-59(Thallys-stint1).ibt",
                "stint_2": "toyotagr86_summit summit raceway 2026-07-06 20-58-37(Thallys-stint2).ibt",
                "stint_3": "toyotagr86_summit summit raceway 2026-07-06 21-18-41(Thallys-stint3).ibt",
                "stint_4": "toyotagr86_summit summit raceway 2026-07-06 21-48-51(Thallys-stint4).ibt",
                "stint_5": "toyotagr86_summit summit raceway 2026-07-06 22-01-39(Thallys-stint5).ibt",

            },
            "Igor": {
                "warmup": "toyotagr86_summit summit raceway 2026-07-11 16-39-19(igor-aquecimento).ibt",
                "stint_1": "toyotagr86_summit summit raceway 2026-07-11 16-49-26(igor-stint1).ibt",
                "stint_2": "toyotagr86_summit summit raceway 2026-07-11 17-00-33(igor-stint2).ibt",
                "stint_3": "toyotagr86_summit summit raceway 2026-07-11 17-08-30(igor-stint3).ibt",
                "stint_4": "toyotagr86_summit summit raceway 2026-07-11 17-16-52(igor-stint4).ibt",
                "stint_5": "toyotagr86_summit summit raceway 2026-07-11 17-38-46(igor-stint5).ibt",
            },
            "Hilton": {
                "stint_1": "toyotagr86_summit summit raceway 2026-07-07 13-11-39(hilton-stint1).ibt",
                "stint_2": "toyotagr86_summit summit raceway 2026-07-07 13-42-19(hilton-stint-2).ibt",
                "stint_3": "toyotagr86_summit summit raceway 2026-07-07 13-53-09(hilton-stint3).ibt",
                "stint_4": "toyotagr86_summit summit raceway 2026-07-07 14-06-48(hilton-stint4).ibt",
                "stint_5": "toyotagr86_summit summit raceway 2026-07-07 14-21-27(hilton-stint5).ibt",
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
