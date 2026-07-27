#!/usr/bin/env python3
"""
run_entropy_pipeline.py
=======================
Runs the full entropy analysis for every track/driver/stint comparison
defined in COMPARISONS.

Architecture
------------
  • Reads entropy_v2_updated.ipynb and executes its cells in sequence.
  • Injects TRACK, DRIVER_REF/TEST, STINT_REF/TEST before execution.
  • Each comparison saves PDFs to its own SAVE_DIR subtree.
  • On error, logs the failure and moves to the next comparison.

Usage
-----
    # run all comparisons
    python run_entropy_pipeline.py

    # preview what would run (no execution)
    python run_entropy_pipeline.py --dry-run

    # only one track
    python run_entropy_pipeline.py --track charlotte_roval_2025

    # skip a comparison if its SAVE_DIR already has outputs
    python run_entropy_pipeline.py --skip-existing

    # point to a different notebook
    python run_entropy_pipeline.py --notebook path/to/entropy_v2.ipynb

Requirements
------------
    pip install nbformat

Setup (one time)
----------------
    1. In entropy_v2_updated.ipynb, find the "User Selection" cell (cell ~3)
       that contains TRACK, DRIVER_REF, STINT_REF, etc.
    2. In Jupyter, open the cell's metadata (⚙ button) and add the tag:
           parameters
       This lets run_entropy_pipeline.py know exactly which cell to replace.
       If you don't add the tag, the script falls back to auto-detection
       (looks for the first cell that contains all five variable names).
"""

from __future__ import annotations

import argparse
import logging
import sys
import textwrap
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# ── Notebook execution engine ─────────────────────────────────────────────────
try:
    import nbformat
except ImportError:
    sys.exit(
        "nbformat not found.  Install with:  pip install nbformat\n"
        "(nbclient is NOT required — we use exec() directly)"
    )

import matplotlib
matplotlib.use("Agg")   # non-interactive: never show GUI windows

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION — edit this section
# ══════════════════════════════════════════════════════════════════════════════

# Notebook to run (relative to this script's location)
DEFAULT_NOTEBOOK = Path(__file__).parent / "entropy_v3.ipynb"

# ── Comparisons ───────────────────────────────────────────────────────────────
# Each tuple: (TRACK, DRIVER_REF, STINT_REF, DRIVER_TEST, STINT_TEST)
#
# Naming convention:
#   DRIVER_REF  = the faster/reference driver
#   DRIVER_TEST = the driver being analysed relative to REF
#
# Tiered design from the paper:
#   A (expert) → ref for B (intermediate)
#   B (intermediate) → ref for C (beginner)
#
# *** EDIT DRIVER NAMES TO MATCH YOUR config.py DATASETS KEYS ***
COMPARISONS: List[Tuple[str, str, str, str, str]] = [

    # ── Charlotte Roval 2025 ─────────────────────────────────────────────────
    # Intermediate vs Expert
    ("charlotte_roval_2025", "Tomaz",      "stint_1", "Morsinaldo", "stint_1"),

    # Beginner vs Intermediate — before and after LLM feedback
    ("charlotte_roval_2025", "Morsinaldo", "stint_1", "DriverC",    "stint_1"),
    ("charlotte_roval_2025", "Morsinaldo", "stint_1", "DriverC",    "stint_2"),

    # Intra-driver: Intermediate improvement check
    ("charlotte_roval_2025", "Morsinaldo", "stint_1", "Morsinaldo", "stint_2"),

    # ── Summit Point ─────────────────────────────────────────────────────────
    ("summit_point",         "Tomaz",      "stint_1", "Morsinaldo", "stint_1"),
    ("summit_point",         "Morsinaldo", "stint_1", "DriverC",    "stint_1"),
    ("summit_point",         "Morsinaldo", "stint_1", "DriverC",    "stint_2"),
    ("summit_point",         "Morsinaldo", "stint_1", "Morsinaldo", "stint_2"),
]

# ── Output root (must match PROJECT_ROOT / BASE_IMG_DIR in the notebook) ──────
# Leave as None to use the path already set inside the notebook.
OVERRIDE_BASE_IMG_DIR: Path | None = None   # e.g. Path("/data/Racing4all/Iracing/img")

# ── Max seconds allowed per comparison (None = no limit) ─────────────────────
TIMEOUT_PER_COMPARISON: int | None = 600   # 10 min

# ══════════════════════════════════════════════════════════════════════════════
#  INTERNALS — normally no need to edit below
# ══════════════════════════════════════════════════════════════════════════════

LOG_FMT = "%(asctime)s  %(levelname)-8s  %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt="%H:%M:%S")
log = logging.getLogger("entropy_pipeline")


# ── Parameter cell injection ──────────────────────────────────────────────────

def _make_param_source(
    track: str,
    driver_ref: str,
    stint_ref: str,
    driver_test: str,
    stint_test: str,
    base_img_dir: Path | None,
) -> str:
    """Return the Python source that replaces the notebook's User Selection cell."""
    lines = [
        "# ── Injected by run_entropy_pipeline.py ──",
        f"TRACK       = {track!r}",
        f"track_id    = TRACK",
        f"DRIVER_REF  = {driver_ref!r}",
        f"STINT_REF   = {stint_ref!r}",
        f"DRIVER_TEST = {driver_test!r}",
        f"STINT_TEST  = {stint_test!r}",
    ]
    if base_img_dir is not None:
        lines.append(f"_OVERRIDE_BASE_IMG_DIR = {str(base_img_dir)!r}")
        lines.append("from pathlib import Path as _P")
        lines.append("BASE_IMG_DIR = _P(_OVERRIDE_BASE_IMG_DIR)")
    return "\n".join(lines)


def _find_param_cell_index(nb: nbformat.NotebookNode) -> int:
    """
    Return the index of the cell to replace with injected parameters.

    Priority:
      1. Cell tagged with 'parameters' in its metadata.
      2. First code cell that assigns ALL five key variables.
    """
    # Strategy 1: tagged cell
    for idx, cell in enumerate(nb.cells):
        tags = cell.get("metadata", {}).get("tags", [])
        if "parameters" in tags:
            log.debug("param cell found by tag at index %d", idx)
            return idx

    # Strategy 2: auto-detect — first code cell containing all five names
    required = {"TRACK", "DRIVER_REF", "STINT_REF", "DRIVER_TEST", "STINT_TEST"}
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        src = "".join(cell.source)
        if all(name in src for name in required):
            log.debug("param cell found by content at index %d", idx)
            return idx

    raise RuntimeError(
        "Could not find the parameters cell in the notebook.\n"
        "Either tag the User Selection cell with the 'parameters' tag in Jupyter,\n"
        "or make sure TRACK / DRIVER_REF / STINT_REF / DRIVER_TEST / STINT_TEST\n"
        "are all assigned in the same cell."
    )


# ── Cell executor ─────────────────────────────────────────────────────────────

def _execute_notebook(
    nb: nbformat.NotebookNode,
    param_src: str,
    param_idx: int,
    label: str,
) -> None:
    """
    Execute notebook cells one by one using exec() in a shared namespace.
    Raises on the first unhandled exception.
    """
    # Build fresh namespace with __builtins__ so exec() works normally
    ns: dict = {"__name__": "__main__", "__builtins__": __builtins__}

    # Inject matplotlib non-interactive mode so plt.show() is a no-op
    ns["_mpl_use_agg"] = True
    exec("import matplotlib; matplotlib.use('Agg')", ns)

    total = len(nb.cells)
    for cell_idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue

        # Use injected source for the parameter cell, original for all others
        src = param_src if cell_idx == param_idx else "".join(cell.source)

        # Skip empty cells and magic commands that exec() can't handle
        src_stripped = src.strip()
        if not src_stripped:
            continue
        if src_stripped.startswith("%"):
            # Convert %load_ext / %autoreload to no-ops silently
            continue

        log.debug("[%s]  executing cell %d / %d", label, cell_idx + 1, total)
        try:
            exec(compile(src, f"<cell {cell_idx}>", "exec"), ns)
        except Exception as exc:
            raise RuntimeError(
                f"[{label}]  cell {cell_idx} raised {type(exc).__name__}: {exc}"
            ) from exc


# ── SAVE_DIR existence check ───────────────────────────────────────────────────

def _save_dir_exists(
    nb: nbformat.NotebookNode,
    param_src: str,
    param_idx: int,
) -> bool:
    """
    Quick check: execute only up to and including the SAVE_DIR cell,
    then test whether any .pdf files already exist there.
    """
    ns: dict = {"__name__": "__main__", "__builtins__": __builtins__}
    exec("import matplotlib; matplotlib.use('Agg')", ns)

    for cell_idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        src = param_src if cell_idx == param_idx else "".join(cell.source)
        src_stripped = src.strip()
        if not src_stripped or src_stripped.startswith("%"):
            continue
        try:
            exec(compile(src, f"<cell {cell_idx}>", "exec"), ns)
        except Exception:
            pass   # ignore errors in this quick scan

        # Stop once SAVE_DIR is defined and points to an existing directory
        save_dir = ns.get("SAVE_DIR")
        if save_dir is not None:
            from pathlib import Path
            p = Path(str(save_dir))
            if p.exists() and any(p.rglob("*.pdf")):
                return True
            break   # SAVE_DIR just got set; no need to run further cells

    return False


# ── Single comparison runner ───────────────────────────────────────────────────

def run_comparison(
    track: str,
    driver_ref: str,
    stint_ref: str,
    driver_test: str,
    stint_test: str,
    notebook_path: Path,
    skip_existing: bool = False,
) -> bool:
    """
    Execute the notebook for one comparison.
    Returns True on success, False on failure.
    """
    label = (
        f"{track} | {driver_ref}({stint_ref}) → {driver_test}({stint_test})"
    )
    log.info("▶  %s", label)

    # Load a fresh copy of the notebook for each comparison
    nb = nbformat.read(str(notebook_path), as_version=4)
    param_idx  = _find_param_cell_index(nb)
    param_src  = _make_param_source(
        track, driver_ref, stint_ref, driver_test, stint_test,
        OVERRIDE_BASE_IMG_DIR,
    )

    # Optional: skip if outputs already exist
    if skip_existing and _save_dir_exists(nb, param_src, param_idx):
        log.info("   ↩ already exists — skipping")
        return True

    t0 = time.perf_counter()
    try:
        _execute_notebook(nb, param_src, param_idx, label)
        elapsed = time.perf_counter() - t0
        log.info("   ✅ done in %.1f s", elapsed)
        return True
    except Exception:
        elapsed = time.perf_counter() - t0
        log.error("   ❌ failed after %.1f s", elapsed)
        log.error(textwrap.indent(traceback.format_exc(), "      "))
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Entropy analysis pipeline — runs all track/driver comparisons.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples
            --------
              python run_entropy_pipeline.py
              python run_entropy_pipeline.py --dry-run
              python run_entropy_pipeline.py --track summit_point
              python run_entropy_pipeline.py --skip-existing --verbose
        """),
    )
    p.add_argument(
        "--notebook", type=Path, default=DEFAULT_NOTEBOOK,
        help="Path to entropy_v2_updated.ipynb (default: same directory as this script)",
    )
    p.add_argument(
        "--track", type=str, default=None,
        help="Run only comparisons for this track key (e.g. charlotte_roval_2025)",
    )
    p.add_argument(
        "--ref", type=str, default=None,
        help="Run only comparisons where DRIVER_REF matches this string",
    )
    p.add_argument(
        "--test", type=str, default=None,
        help="Run only comparisons where DRIVER_TEST matches this string",
    )
    p.add_argument(
        "--skip-existing", action="store_true",
        help="Skip comparison if its SAVE_DIR already contains .pdf files",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Print the list of comparisons that would run, then exit",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show DEBUG-level cell execution logs",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate notebook path
    if not args.notebook.exists():
        sys.exit(
            f"Notebook not found: {args.notebook}\n"
            "Make sure entropy_v2_updated.ipynb is in the same folder as this script,\n"
            "or pass --notebook /path/to/entropy_v2_updated.ipynb"
        )

    # Filter comparisons
    comparisons = COMPARISONS
    if args.track:
        comparisons = [c for c in comparisons if c[0] == args.track]
    if args.ref:
        comparisons = [c for c in comparisons if c[1] == args.ref]
    if args.test:
        comparisons = [c for c in comparisons if c[3] == args.test]

    if not comparisons:
        sys.exit("No comparisons match the given filters.")

    # Dry run: just print
    if args.dry_run:
        print(f"\n{'─'*66}")
        print(f"  DRY RUN — {len(comparisons)} comparison(s) would execute")
        print(f"  Notebook: {args.notebook}")
        print(f"{'─'*66}")
        for i, (trk, dr, sr, dt, st) in enumerate(comparisons, 1):
            print(f"  [{i:>2}]  {trk}")
            print(f"        REF  {dr} / {sr}")
            print(f"        TEST {dt} / {st}")
        print(f"{'─'*66}\n")
        return

    # Execute
    start_time = datetime.now()
    log.info("=" * 66)
    log.info("  Entropy Pipeline — %d comparison(s)", len(comparisons))
    log.info("  Notebook : %s", args.notebook)
    log.info("  Started  : %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    log.info("=" * 66)

    results: list[tuple[str, bool]] = []

    for i, (trk, dr, sr, dt, st) in enumerate(comparisons, 1):
        log.info("")
        log.info("[%d/%d] ─────────────────────────────────────────────────", i, len(comparisons))
        ok = run_comparison(
            track=trk,
            driver_ref=dr,
            stint_ref=sr,
            driver_test=dt,
            stint_test=st,
            notebook_path=args.notebook,
            skip_existing=args.skip_existing,
        )
        label = f"{trk}  {dr}({sr}) → {dt}({st})"
        results.append((label, ok))

    # Summary
    n_ok   = sum(1 for _, ok in results if ok)
    n_fail = len(results) - n_ok
    elapsed_total = (datetime.now() - start_time).total_seconds()

    log.info("")
    log.info("=" * 66)
    log.info("  PIPELINE COMPLETE")
    log.info("  ✅ Success : %d / %d", n_ok, len(results))
    if n_fail:
        log.info("  ❌ Failures: %d", n_fail)
    log.info("  Total time: %.0f s (%.1f min)", elapsed_total, elapsed_total / 60)
    log.info("=" * 66)

    if n_fail:
        log.warning("\nFailed comparisons:")
        for label, ok in results:
            if not ok:
                log.warning("  ✗  %s", label)
        sys.exit(1)


if __name__ == "__main__":
    main()
