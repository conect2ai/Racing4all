"""
track_configs.py
================
Centralised track sector definitions for iRacing telemetry analysis.
Each entry maps a track_id → { track_name, custom_edges, sector_names }.

custom_edges  : list of LapDistPct breakpoints (0.0 → 1.0 inclusive).
sector_names  : 1-based dict { sector_int → display_label }.
"""

TRACK_CONFIGS: dict = {

    # ─────────────────────────────────────────────────────────────
    # Charlotte Motor Speedway — Roval 2025
    # ─────────────────────────────────────────────────────────────
    "charlotte_roval_2025": {
        "track_name": "Charlotte Roval 2025",
        "custom_edges": [
            0.0,   0.045, 0.105, 0.155, 0.205, 0.280, 0.380, 0.430,
            0.495, 0.580, 0.645, 0.675, 0.715, 0.750, 0.845, 0.930,
            0.960, 0.985, 1.0,
        ],
        "sector_names": {
            1:  "T1 (Heartlands)",
            2:  "T2",
            3:  "T3 (Infield)",
            4:  "T4",
            5:  "T5/T6 Transition",
            6:  "Hairpin Setup",
            7:  "New Hairpin",
            8:  "Oval Turn 1",
            9:  "Oval Turn 2",
            10: "Backstretch",
            11: "Bus Stop Entry",
            12: "Bus Stop Apex",
            13: "Bus Stop Exit",
            14: "Oval Turn 3",
            15: "Oval Turn 4",
            16: "Final Chicane Entry",
            17: "Final Chicane Exit",
            18: "Frontstretch",
        },
    },

    # ─────────────────────────────────────────────────────────────
    # Summit Point — Main Circuit
    # ─────────────────────────────────────────────────────────────
    "summit_point": {
        "track_name": "Summit Point - Main Circuit",
        "custom_edges": [
            0.0,   0.105, 0.215, 0.315, 0.410, 0.500,
            0.585, 0.670, 0.780, 0.915, 1.0,
        ],
        "sector_names": {
            1:  "Main Straight & Braking",
            2:  "T1 Right Hander",
            3:  "T3 (Left-hander)",
            4:  "T4 (The Chute)",
            5:  "T5 (Carousel Entry)",
            6:  "T6/T7 (Carousel Mid)",
            7:  "T8 (Carousel Exit)",
            8:  "T9 (The Bridge)",
            9:  "T10 (Final Turn)",
            10: "Frontstretch",
        },
    },
}
