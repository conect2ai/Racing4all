import irsdk
import time
import pandas as pd
import os
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS (Atualizado para seu PC) ---
PROJECT_ROOT = Path("C:/Users/PC/Documents/GitHub/Racing4all")
DATA_DIR = PROJECT_ROOT / "Iracing" / "Data_Logs"
DATA_DIR.mkdir(parents=True, exist_ok=True) # Cria a pasta se não existir

# Nome do arquivo final
EXCEL_PATH = DATA_DIR / "stint_telemetry_summary.xlsx"

ir = irsdk.IRSDK()
ir.startup()

# Variáveis de controle
last_processed_lap = -1
fuel_at_lap_start = 0.0
driver_name = "Conectando..."
lap_results = [] # Lista para acumular os dados na memória

print(f"🏁 Monitoramento iniciado. Os dados serão salvos em:\n{EXCEL_PATH}")

def save_lap_to_excel(new_data):
    """Adiciona a volta ao arquivo Excel existente ou cria um novo."""
    df_new = pd.DataFrame([new_data])
    
    if not EXCEL_PATH.exists():
        # Cria o arquivo pela primeira vez
        df_new.to_excel(EXCEL_PATH, index=False)
    else:
        # Lê o existente, concatena e salva
        df_old = pd.read_excel(EXCEL_PATH)
        df_final = pd.concat([df_old, df_new], ignore_index=True)
        df_final.to_excel(EXCEL_PATH, index=False)
    
    print(f"💾 Arquivo Excel atualizado com a Volta {new_data['Volta']}")

try:
    while True:
        if ir.is_connected:
            # Identificação do Piloto
            if driver_name == "Conectando...":
                try:
                    idx = ir['DriverInfo']['DriverCarIdx']
                    driver_name = ir['DriverInfo']['Drivers'][idx]['UserName']
                    print(f"👤 Piloto: {driver_name}")
                except: pass

            current_lap = ir['Lap']
            
            # Quando a volta muda
            if current_lap > last_processed_lap:
                if last_processed_lap != -1:
                    last_lap_time = ir['LapLastLapTime']
                    incidents = ir['PlayerCarMyIncidentCount']
                    fuel_now = ir['FuelLevel']
                    consumption = fuel_at_lap_start - fuel_now
                    
                    if last_lap_time > 0:
                        # Criar dicionário com os dados da volta
                        data_row = {
                            "Piloto": driver_name,
                            "Volta": last_processed_lap,
                            "Tempo_s": round(last_lap_time, 3),
                            "Consumo_L": round(consumption, 3),
                            "Incidentes": incidents,
                            "Timestamp": time.strftime("%H:%M:%S")
                        }
                        
                        # Salva no Excel instantaneamente
                        save_lap_to_excel(data_row)
                
                # Sincroniza para a nova volta
                last_processed_lap = current_lap
                fuel_at_lap_start = ir['FuelLevel']
            
            time.sleep(0.1)
        else:
            driver_name = "Conectando..."
            time.sleep(2)

except KeyboardInterrupt:
    print("\n🛑 Monitoramento encerrado. Todos os dados foram salvos.")
finally:
    ir.shutdown()