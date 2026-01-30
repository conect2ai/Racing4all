# =============================================================================
# CONFIGURAÇÃO DE TELEMETRIA: CHARLOTTE ROVAL 2025 (Refinada)
# Foco: Isolamento da Frenagem Pesada e do New Hairpin (Curva em U)
# =============================================================================

TRACK_NAME = "Charlotte Roval 2025" # Nome oficial para os gráficos
CUSTOM_EDGES = [
    0.0,      # 00: Largada/Chegada
    0.045,    # 01: T1 (Heartlands)
    0.105,    # 02: T2
    0.155,    # 03: T3 (Infield)
    0.205,    # 04: T4
    0.280,    # 05: T5/T6 Transition (Aproximação)
    0.380,    # 06: Hairpin Setup (A "Parte Vermelha" - Zona de Frenagem)
    0.430,    # 07: New Hairpin (A Curva em U - Ponto mais lento)
    0.495,    # 08: Oval Turn 1 (Transição para a inclinação)
    0.580,    # 09: Oval Turn 2
    0.645,    # 10: Backstretch (Reta oposta do Oval)
    0.675,    # 11: Bus Stop Entry
    0.715,    # 12: Bus Stop Apex
    0.750,    # 13: Bus Stop Exit
    0.845,    # 14: Oval Turn 3
    0.930,    # 15: Oval Turn 4
    0.960,    # 16: Final Chicane Entry
    0.985,    # 17: Final Chicane Exit
    1.0       # 18: Frontstretch / Finish Line
]

SECTOR_NAMES = {
    1: "T1 (Heartlands)",
    2: "T2",
    3: "T3 (Infield)",
    4: "T4",
    5: "T5/T6 Transition",
    6: "Hairpin Setup",     # Novo setor para a frenagem pesada (Red Zone)
    7: "New Hairpin",       # A curva em U propriamente dita
    8: "Oval Turn 1",       # Subida para o Oval
    9: "Oval Turn 2",
    10: "Backstretch",
    11: "Bus Stop Entry",
    12: "Bus Stop Apex",
    13: "Bus Stop Exit",
    14: "Oval Turn 3",
    15: "Oval Turn 4",
    16: "Final Chicane Entry",
    17: "Final Chicane Exit",
    18: "Frontstretch"
}