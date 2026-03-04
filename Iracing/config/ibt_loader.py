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
    if isinstance(paths, (str, Path)):
        paths = [paths]

    # Accept str or Path — normalise everything to Path
    paths = [Path(p) for p in paths]

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
    Drop infinities, drop rows missing key columns, sort, convert units,
    normalise LapDistPct and add derived channels.

    Added columns
    -------------
    Speed_KPH, Throttle_Pct, Brake_Pct,
    LatAccel_G, LongAccel_G, TotalAccel_G
    """
    df = df.copy()

    # Replace ±inf before any numeric operation
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # ── Unit conversions (before dropna so columns always exist) ─────────
    if "Speed_KPH" not in df.columns and "Speed" in df.columns:
        df["Speed_KPH"]    = df["Speed"]    * 3.6
    if "Throttle_Pct" not in df.columns and "Throttle" in df.columns:
        df["Throttle_Pct"] = df["Throttle"] * 100.0
    if "Brake_Pct" not in df.columns and "Brake" in df.columns:
        df["Brake_Pct"]    = df["Brake"]    * 100.0

    # ── Normalise LapDistPct (iRacing sometimes outputs 0–100) ───────────
    if "LapDistPct" in df.columns:
        mx = df["LapDistPct"].max()
        if pd.notna(mx) and mx > 1.5:
            df["LapDistPct"] = df["LapDistPct"] / 100.0

    # ── Drop rows missing structural columns ─────────────────────────────
    required = [c for c in
                ["Lap", "SessionTime", "LapDistPct", "Speed_KPH",
                 "Throttle_Pct", "Brake_Pct"]
                if c in df.columns]
    df.dropna(subset=required, inplace=True)

    df.sort_values(["Lap", "SessionTime"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ── G-force derived channels ─────────────────────────────────────────
    _g = 9.81
    if "LatAccel" in df.columns:
        df["LatAccel_G"]  = df["LatAccel"]  / _g
    if "LongAccel" in df.columns:
        df["LongAccel_G"] = df["LongAccel"] / _g
    if "LatAccel_G" in df.columns and "LongAccel_G" in df.columns:
        df["TotalAccel_G"] = np.sqrt(df["LatAccel_G"]**2 + df["LongAccel_G"]**2)

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
    min_completed_pct:  float = 0.995,
    max_start_pct:      float = 0.02,
    min_lap_time_s:     float = 45.0,
    max_lap_time_s:     float = 120.0,
    min_gps_coverage:   float = 1.0,    # 1.0 = 100 % of rows must have Lat+Lon
    verbose:            bool  = True,
) -> pd.DataFrame:
    """
    Return a per-lap validity table with columns:
        Lap, LapTime_s, StartPct, CompletedPct,
        FracLowSpeed, MaxSpeed_kph, GpsCoverage_Pct, Valid, InvalidReason

    Validity criteria (all must pass)
    ----------------------------------
    1. StartPct       <= max_start_pct          (lap started at S/F)
    2. CompletedPct   >= min_completed_pct       (nearly full lap)
    3. Lap not in manual_invalid
    4. FracLowSpeed   <= 0.25                    (not a slow/tow lap)
    5. MaxSpeed_kph   >= min_max_speed_kph
    6. LapTime_s      in [min_lap_time_s, max_lap_time_s]
    7. GpsCoverage_Pct >= min_gps_coverage       (complete GPS trace)
    8. IQR refinement  (applied when >= 5 valid laps exist)
    """
    manual_invalid = manual_invalid or set()
    has_gps = "Lat" in df.columns and "Lon" in df.columns
    rows = []

    for lap, grp in df.groupby("Lap", sort=True):
        gs       = grp.sort_values("SessionTime").copy()
        lap_time = _lap_time_seconds(gs)

        if has_gps:
            gps_ok = gs["Lat"].notna() & gs["Lon"].notna()
            gps_coverage = float(gps_ok.mean())
        else:
            gps_coverage = 1.0   # not penalised when GPS channels absent

        rows.append({
            "Lap":              int(lap),
            "LapTime_s":        float(lap_time),
            "StartPct":         float(gs["LapDistPct"].min()),
            "CompletedPct":     float(gs["LapDistPct"].max()),
            "FracLowSpeed":     float((gs["Speed_KPH"] < low_speed_kph).mean()),
            "MaxSpeed_kph":     float(gs["Speed_KPH"].max()),
            "GpsCoverage_Pct":  gps_coverage,
        })

    lap_df = pd.DataFrame(rows).sort_values("Lap").reset_index(drop=True)

    valid = (
        (lap_df["StartPct"]        <= max_start_pct)
        & (lap_df["CompletedPct"]  >= min_completed_pct)
        & (~lap_df["Lap"].isin(manual_invalid))
        & (lap_df["FracLowSpeed"]  <= 0.25)
        & (lap_df["MaxSpeed_kph"]  >= min_max_speed_kph)
        & (lap_df["LapTime_s"]     >= min_lap_time_s)
        & (lap_df["LapTime_s"]     <= max_lap_time_s)
        & (lap_df["GpsCoverage_Pct"] >= min_gps_coverage)
    )
    lap_df["Valid"] = valid

    # ── IQR refinement ────────────────────────────────────────────────────
    if lap_df["Valid"].sum() >= 5:
        q1, q3 = lap_df.loc[lap_df["Valid"], "LapTime_s"].quantile([0.25, 0.75])
        iqr     = float(q3 - q1)
        hi      = float(q3 + 1.5 * iqr)
        lo      = max(0.0, float(q1 - 1.5 * iqr))
        iqr_fail = ~lap_df["LapTime_s"].between(lo, hi)
        lap_df.loc[iqr_fail, "Valid"] = False

    # ── Invalidation reason (verbose) ────────────────────────────────────
    def _reason(row) -> str:
        if row["Valid"]:
            return "OK"
        reasons = []
        if row["StartPct"]       > max_start_pct:
            reasons.append(f"StartPct={row['StartPct']:.3f}>{max_start_pct}")
        if row["CompletedPct"]   < min_completed_pct:
            reasons.append(f"CompletedPct={row['CompletedPct']:.3f}<{min_completed_pct}")
        if row["Lap"] in manual_invalid:
            reasons.append("manual_invalid")
        if row["FracLowSpeed"]   > 0.25:
            reasons.append(f"FracLowSpeed={row['FracLowSpeed']:.2f}")
        if row["MaxSpeed_kph"]   < min_max_speed_kph:
            reasons.append(f"MaxSpeed={row['MaxSpeed_kph']:.1f}kph")
        if not (min_lap_time_s <= row["LapTime_s"] <= max_lap_time_s):
            reasons.append(f"LapTime={row['LapTime_s']:.1f}s")
        if row["GpsCoverage_Pct"] < min_gps_coverage:
            reasons.append(f"GPS={row['GpsCoverage_Pct']*100:.1f}%<100%")
        return " | ".join(reasons) if reasons else "IQR_outlier"

    lap_df["InvalidReason"] = lap_df.apply(_reason, axis=1)

    # ── Console report ────────────────────────────────────────────────────
    if verbose:
        valid_laps   = lap_df[lap_df["Valid"]]
        invalid_laps = lap_df[~lap_df["Valid"]]
        fastest      = valid_laps.sort_values("LapTime_s").iloc[0] if not valid_laps.empty else None

        print("─" * 62)
        print(f"  Lap Validity Report  ({len(lap_df)} laps total)")
        print("─" * 62)
        print(f"  ✅ Valid   : {len(valid_laps)} laps")
        if fastest is not None:
            mins   = int(fastest['LapTime_s'] // 60)
            secs   = fastest['LapTime_s'] % 60
            print(f"  🏆 Fastest : Lap {int(fastest['Lap'])}  "
                  f"({mins:02d}:{secs:06.3f})")
        print(f"  ❌ Invalid : {len(invalid_laps)} laps")
        for _, row in invalid_laps.iterrows():
            mins = int(row['LapTime_s'] // 60)
            secs = row['LapTime_s'] % 60
            print(f"     Lap {int(row['Lap']):>3}  {mins:02d}:{secs:06.3f}  → {row['InvalidReason']}")
        print("─" * 62)

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

def select_reference_laps(
    df: pd.DataFrame,
    validity: pd.DataFrame,
    driver_name: str = "",
    verbose: bool = True,
) -> tuple[int, int]:
    """
    Returns (fastest_lap_id, gps_reference_lap_id).

    fastest_lap     : lowest LapTime_s among Valid laps.
    gps_reference   : lap with widest GPS_Coverage (all laps, not just Valid),
                      ensuring the track geometry is complete even when the
                      fastest lap straddles an IBT file boundary.

    Prints a formatted selection report when verbose=True.
    """
    valid_rows = validity[validity["Valid"]]
    if valid_rows.empty:
        raise RuntimeError(f"[{driver_name}] No valid laps found.")

    fastest_row = valid_rows.sort_values("LapTime_s").iloc[0]
    fastest_lap = int(fastest_row["Lap"])

    # GPS reference: lap with highest GpsCoverage_Pct (any lap, not just valid),
    # so the track geometry is always complete even when the fastest lap has
    # a data gap at the IBT file boundary.
    GPS_COL = "GpsCoverage_Pct"
    if GPS_COL in validity.columns:
        gps_lap = int(
            validity.sort_values(GPS_COL, ascending=False).iloc[0]["Lap"]
        )
        gps_cov = float(
            validity.loc[validity["Lap"] == gps_lap, GPS_COL].values[0]
        )
    else:
        gps_lap = fastest_lap   # graceful fallback if column absent
        gps_cov = float("nan")

    if verbose:
        tag = f"[{driver_name}]" if driver_name else ""
        invalid_rows = validity[~validity["Valid"]]

        print(f"\n{'─'*55}")
        print(f"  Lap Selection Report {tag}")
        print(f"{'─'*55}")
        print(f"  ✅ Valid laps    : {sorted(valid_rows['Lap'].tolist())}")
        print(f"  🏁 Fastest lap   : Lap {fastest_lap}  "
              f"({fastest_row['LapTime_s']:.3f}s)")
        print(f"  🗺  GPS reference : Lap {gps_lap}  "
              f"(GPS coverage {gps_cov:.1%})")

        if not invalid_rows.empty:
            print(f"\n  ❌ Invalidated laps ({len(invalid_rows)}):")
            for _, r in invalid_rows.iterrows():
                mins = int(r['LapTime_s'] // 60)
                secs = r['LapTime_s'] % 60
                print(f"     Lap {int(r['Lap']):>3}  {mins:02d}:{secs:06.3f}"
                      f"  →  {r.get('InvalidReason', '—')}")
        print(f"{'─'*55}\n")

    return fastest_lap, gps_lap