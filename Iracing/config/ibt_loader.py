"""
telemetry/loader.py
===================
Core IBT loading, cleaning, lap validation, and sector assignment
for iRacing telemetry analysis.

Key feature — Multi-file stint concatenation
---------------------------------------------
``load_stint()`` accepts a list of IBT file paths and concatenates
them into a single DataFrame.  Lap numbers from subsequent files are
offset so laps form a continuous, strictly increasing sequence.
SessionTime is similarly offset to maintain chronological ordering.

This design eliminates the N/A results that occurred when short stints
(too few laps per file) were analysed in isolation.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy  as np
import pandas as pd

# ── irsdk (optional) ─────────────────────────────────────────────────────────
try:
    import irsdk
    IRSDK_AVAILABLE = True
except ImportError:
    IRSDK_AVAILABLE = False
    print("[WARN] irsdk not installed — run: pip install irsdk")

# ── Channels to extract from IBT files ───────────────────────────────────────
IBT_CHANNELS: list[str] = [
    "Lat",
    "Lon",
    # Timing
    "SessionTime",
    "Lap",
    "LapDistPct",
    # Driver inputs
    "Throttle",
    "ThrottleRaw",
    "Brake",
    "BrakeRaw",
    "SteeringWheelAngle",
    # Vehicle dynamics
    "Speed",
    "LatAccel",
    "LongAccel",
    "YawRate",
    # Context
    "RPM",
    "Gear",
    "BrakeABSactive",
]


# ═════════════════════════════════════════════════════════════════════════════
# Low-level IBT loader
# ═════════════════════════════════════════════════════════════════════════════

def _load_single_ibt(ibt_path: Path) -> pd.DataFrame:
    """
    Read one IBT file and return a raw DataFrame.

    Raises
    ------
    RuntimeError       if irsdk is not installed.
    FileNotFoundError  if the file does not exist.
    """
    if not IRSDK_AVAILABLE:
        raise RuntimeError("irsdk is required — pip install irsdk")
    if not ibt_path.exists():
        raise FileNotFoundError(f"IBT file not found: {ibt_path}")

    ibt = irsdk.IBT()
    try:
        ibt.open(str(ibt_path))
        data = {ch: ibt.get_all(ch) for ch in IBT_CHANNELS}
    finally:
        ibt.close()

    return pd.DataFrame(data)


# ═════════════════════════════════════════════════════════════════════════════
# Multi-file stint loader  (PUBLIC)
# ═════════════════════════════════════════════════════════════════════════════

def load_stint(
    paths: list[Path] | Path,
    *,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Load one or more IBT files that constitute a single stint and return
    a single, concatenated DataFrame with continuous lap numbering.

    Parameters
    ----------
    paths   : single Path or list of Paths (concatenation order = list order).
    verbose : print per-file progress.

    Returns
    -------
    pd.DataFrame  Raw telemetry (all IBT_CHANNELS) with adjusted Lap and
                  SessionTime columns so the stint is a contiguous sequence.

    Notes
    -----
    Lap offset strategy
        max_lap[file_n] + 1  →  base for file_n+1's lap numbers.
    SessionTime offset strategy
        max_session_time[file_n] + median_sample_interval  →  base for file_n+1.
    """
    if isinstance(paths, Path):
        paths = [paths]

    frames: list[pd.DataFrame] = []
    lap_offset  = 0
    time_offset = 0.0

    for idx, p in enumerate(paths):
        if verbose:
            print(f"    [{idx+1}/{len(paths)}] Loading {p.name} …", end=" ")

        df = _load_single_ibt(p)

        if df.empty:
            if verbose:
                print("SKIPPED (empty)")
            continue

        # ── Apply offsets for files after the first ───────────────────────
        if lap_offset > 0:
            df["Lap"]         = df["Lap"].astype(float) + lap_offset
            df["SessionTime"] = df["SessionTime"].astype(float) + time_offset

        # ── Compute offsets for the NEXT file ─────────────────────────────
        lap_offset  = int(df["Lap"].max()) + 1

        valid_times = df["SessionTime"].dropna().sort_values()
        if len(valid_times) > 1:
            dt = float(np.median(np.diff(valid_times.values[:500])))
        else:
            dt = 1.0 / 60.0   # fallback: 60 Hz
        time_offset = float(df["SessionTime"].max()) + dt

        frames.append(df)
        if verbose:
            print(f"OK ({len(df):,} samples, laps {int(df['Lap'].min())}–{int(df['Lap'].max())})")

    if not frames:
        return pd.DataFrame(columns=IBT_CHANNELS)

    return pd.concat(frames, ignore_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# Unit conversion & derived channels
# ═════════════════════════════════════════════════════════════════════════════

def basic_clean_and_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows with null keys, sort, convert units, and add derived channels.

    Added columns
    -------------
    Speed_KPH, Throttle_Pct, Brake_Pct,
    LatAccel_G, LongAccel_G, TotalAccel_G
    """
    df = df.copy()
    df.dropna(subset=["SessionTime", "Lap", "LapDistPct"], inplace=True)
    df.sort_values(["Lap", "SessionTime"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    df["Speed_KPH"]    = df["Speed"]    * 3.6
    df["Throttle_Pct"] = df["Throttle"] * 100.0
    df["Brake_Pct"]    = df["Brake"]    * 100.0

    _g = 9.81
    df["LatAccel_G"]   = df["LatAccel"]  / _g
    df["LongAccel_G"]  = df["LongAccel"] / _g
    df["TotalAccel_G"] = np.sqrt(df["LatAccel_G"] ** 2 + df["LongAccel_G"] ** 2)

    return df


# ═════════════════════════════════════════════════════════════════════════════
# Lap validity filter
# ═════════════════════════════════════════════════════════════════════════════

def _lap_time_seconds(group: pd.DataFrame) -> float:
    gs = group.sort_values("SessionTime")
    return float(gs["SessionTime"].iloc[-1] - gs["SessionTime"].iloc[0])


def build_lap_validity_table(
    df: pd.DataFrame,
    manual_invalid:     set   | None = None,
    low_speed_kph:      float = 10.0,
    min_max_speed_kph:  float = 60.0,
    min_completed_pct:  float = 0.98,
    min_lap_time_s:     float = 45.0,
    max_lap_time_s:     float = 120.0,
) -> pd.DataFrame:
    """
    Return a per-lap validity table (columns: Lap, LapTime_s, CompletedPct,
    FracLowSpeed, MaxSpeed_kph, Valid).

    Validity criteria
    -----------------
    1. LapDistPct >= min_completed_pct  (nearly complete lap)
    2. Lap not in manual_invalid
    3. Fraction of samples below low_speed_kph <= 0.25
    4. Max speed >= min_max_speed_kph   (rules out tow laps)
    5. LapTime_s in [min_lap_time_s, max_lap_time_s]
    6. IQR-based outlier removal (applied only when >= 5 valid laps exist)
    """
    manual_invalid = manual_invalid or set()
    rows = []

    for lap, grp in df.groupby("Lap", sort=True):
        gs       = grp.sort_values("SessionTime").copy()
        lap_time = _lap_time_seconds(gs)
        rows.append({
            "Lap":          int(lap),
            "LapTime_s":    float(lap_time),
            "CompletedPct": float(gs["LapDistPct"].max()),
            "FracLowSpeed": float((gs["Speed_KPH"] < low_speed_kph).mean()),
            "MaxSpeed_kph": float(gs["Speed_KPH"].max()),
        })

    lap_df = pd.DataFrame(rows).sort_values("Lap").reset_index(drop=True)

    valid = (
        (lap_df["CompletedPct"] >= min_completed_pct)
        & (~lap_df["Lap"].isin(manual_invalid))
        & (lap_df["FracLowSpeed"] <= 0.25)
        & (lap_df["MaxSpeed_kph"] >= min_max_speed_kph)
        & (lap_df["LapTime_s"]    >= min_lap_time_s)
        & (lap_df["LapTime_s"]    <= max_lap_time_s)
    )
    lap_df["Valid"] = valid

    # IQR refinement
    if lap_df["Valid"].sum() >= 5:
        q1, q3 = lap_df.loc[lap_df["Valid"], "LapTime_s"].quantile([0.25, 0.75])
        iqr     = float(q3 - q1)
        hi      = float(q3 + 1.5 * iqr)
        lo      = max(0.0, float(q1 - 1.5 * iqr))
        lap_df.loc[:, "Valid"] &= lap_df["LapTime_s"].between(lo, hi)

    return lap_df


# ═════════════════════════════════════════════════════════════════════════════
# Sector assignment
# ═════════════════════════════════════════════════════════════════════════════

def assign_sectors(df: pd.DataFrame, edges: list[float]) -> pd.DataFrame:
    """
    Append a 1-based integer 'Sector' column derived from LapDistPct
    and the provided sector edge list.

    Parameters
    ----------
    df    : DataFrame containing a 'LapDistPct' column (0.0 – 1.0).
    edges : Sorted list of LapDistPct breakpoints including 0.0 and 1.0.
    """
    df = df.copy()
    df["Sector"] = pd.cut(
        df["LapDistPct"],
        bins=edges,
        labels=range(1, len(edges)),
        include_lowest=True,
        right=True,
    ).astype("Int64")
    return df


# ═════════════════════════════════════════════════════════════════════════════
# Convenience: load a full stint end-to-end
# ═════════════════════════════════════════════════════════════════════════════

def load_and_prepare_stint(
    paths:           list[Path] | Path,
    edges:           list[float],
    max_lap_time_s:  float = 120.0,
    min_lap_time_s:  float = 45.0,
    manual_invalid:  set   | None = None,
    verbose:         bool  = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full pipeline: load → clean → validate → assign sectors.

    Returns
    -------
    (df_valid, validity_table)
        df_valid       : cleaned DataFrame containing only valid laps with
                         sector assignments.
        validity_table : full per-lap validity table (for diagnostics).
    """
    df_raw    = load_stint(paths, verbose=verbose)
    if df_raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_clean  = basic_clean_and_units(df_raw)
    validity  = build_lap_validity_table(
        df_clean,
        manual_invalid=manual_invalid,
        max_lap_time_s=max_lap_time_s,
        min_lap_time_s=min_lap_time_s,
    )
    valid_laps = validity.loc[validity["Valid"], "Lap"].tolist()

    if not valid_laps:
        return pd.DataFrame(), validity

    df_valid = df_clean[df_clean["Lap"].isin(valid_laps)].copy()
    df_valid = assign_sectors(df_valid, edges)

    return df_valid, validity
