"""
driver_alias.py
===============
Maps real driver names (used as keys in DATASETS) to anonymised
display labels used in plots, titles, and exported filenames.

Keeping aliases here avoids scattering the mapping across notebooks.
"""

DRIVER_ALIAS: dict[str, str] = {
    "Rodrigo":    "Driver A",
    "Tomaz":      "Driver B",
    "Morsinaldo": "Driver C",
}
