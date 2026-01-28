# =============================================================================
# CONFIGURAÇÃO DE TELEMETRIA: SUMMIT POINT (MAIN CIRCUIT)
# PROJETO DOUTORADO - ANÁLISE DE CONDUÇÃO
# =============================================================================

CUSTOM_EDGES = [
    0.0,      # 00: Largada/Chegada
    0.075,    # 01: Main Straight (Reta principal)
    0.105,    # 02: T1 Braking Setup (Frenagem pesada da T1)
    0.145,    # 03: T1 Apex/Exit (Ponto de rotação e saída)
    0.215,    # 04: T2 (A "curva infinita" à direita)
    0.315,    # 05: T3 (Esquerda técnica antes do Chute)
    0.410,    # 06: T4 The Chute (Descida acentuada)
    0.485,    # 07: T5 Carousel Entry (Entrada da ferradura)
    0.585,    # 08: T6/T7 Carousel Mid (Manutenção de grip lateral)
    0.680,    # 09: T8 Carousel Exit (Saída e tração)
    0.780,    # 10: T9 (Curva rápida à direita sob a ponte)
    0.915,    # 11: T10 Bridge Corner (Curva final para a reta)
    1.0       # 12: Frontstretch / Finish
]

SECTOR_NAMES = {
    1: "Main Straight",
    2: "T1 Braking Setup",
    3: "T1 (Big Bend)",
    4: "T2 (Right-hander)",
    5: "T3 (Left-hander)",
    6: "T4 (The Chute)",
    7: "T5 (Carousel Entry)",
    8: "T6/T7 (Carousel Mid)",
    9: "T8 (Carousel Exit)",
    10: "T9 (The Bridge)",
    11: "T10 (Final Turn)",
    12: "Frontstretch"
}