# =============================================================================
# CONFIGURAÇÃO DE TELEMETRIA: SUMMIT POINT (UNIFICADA)
# PROJETO DOUTORADO - SETORIZAÇÃO SIMPLIFICADA
# =============================================================================

TRACK_NAME = "Summit Point - Main Circuit" # Nome oficial para os gráficos
CUSTOM_EDGES = [
    0.0,      # 00: Largada/Chegada
    0.105,    # 01: Main Straight & Braking (Unificado)
    0.215,    # 02: T1 Right Hander (Unificado T1 + T2)
    0.315,    # 03: T3 (Left-hander)
    0.410,    # 04: T4 (The Chute)
    0.500,    # 05: T5 (Carousel Entry)
    0.585,    # 06: T6/T7 (Carousel Mid)
    0.670,    # 07: T8 (Carousel Exit)
    0.780,    # 08: T9 (The Bridge)
    0.915,    # 09: T10 (Final Turn)
    1.0       # 10: Frontstretch
]

SECTOR_NAMES = {
    1: "Main Straight & Braking",
    2: "T1 Right Hander",
    3: "T3 (Left-hander)",
    4: "T4 (The Chute)",
    5: "T5 (Carousel Entry)",
    6: "T6/T7 (Carousel Mid)",
    7: "T8 (Carousel Exit)",
    8: "T9 (The Bridge)",
    9: "T10 (Final Turn)",
    10: "Frontstretch"
}