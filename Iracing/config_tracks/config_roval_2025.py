# config_roval_2025.py

CUSTOM_EDGES = [
    0.0,      # 0: Início
    0.045,    # 1: T1
    0.105,    # 2: T2
    0.155,    # 3: T3
    0.205,    # 4: T4
    0.255,    # 5: T5/T6
    0.315,    # 6: T7
    0.365,    # 7: T8
    0.445,    # 8: Oval T1
    0.525,    # 9: Oval T2
    0.655,    # 10: Backstretch
    0.685,    # 11: Bus Stop Entry
    0.715,    # 12: Bus Stop Apex
    0.750,    # 13: Bus Stop Exit
    0.845,    # 14: Oval Turn 3
    0.930,    # 15: Oval Turn 4 (Termina antes da aproximação da chicane)
    0.970,    # 16: Final Chicane Entry (Ponto de 'setup' e frenagem inicial)
    0.985,    # 17: Final Chicane Exit (O complexo da chicane em si)
    1.0       # 18: Frontstretch / Finish (Linha de chegada)
]

# Nomes Oficiais dos 18 Setores
SECTOR_NAMES = {
    1: "T1 (Heartlands)", 2: "T2", 3: "T3 (Infield)", 4: "T4",
    5: "T5/T6 Transition", 6: "T7 (New Hairpin)", 7: "T8 (To Oval)",
    8: "Oval Turn 1", 9: "Oval Turn 2", 10: "Backstretch",
    11: "Bus Stop Entry", 12: "Bus Stop Apex", 13: "Bus Stop Exit",
    14: "Oval Turn 3", 15: "Oval Turn 4", 16: "Final Chicane Entry",
    17: "Final Chicane Exit", 18: "Frontstretch / Finish"
}