# config/__init__.py  — versão corrigida

from .track_configs import TRACK_CONFIGS
from .datasets      import DATASETS, resolve_stint_files
from .driver_alias  import DRIVER_ALIAS
from .ibt_loader    import (          # ← era "from telemetry import ..."
    load_stint,
    load_and_prepare_stint,
    basic_clean_and_units,
    build_lap_validity_table,
    assign_sectors,
    IRSDK_AVAILABLE,
    IBT_CHANNELS,
    basic_clean_and_units,
)

__all__ = [
    "TRACK_CONFIGS", "DATASETS", "DRIVER_ALIAS", "resolve_stint_files",
    "load_stint", "load_and_prepare_stint", "basic_clean_and_units",
    "build_lap_validity_table", "assign_sectors",
    "IRSDK_AVAILABLE", "IBT_CHANNELS", "basic_clean_and_units"
]