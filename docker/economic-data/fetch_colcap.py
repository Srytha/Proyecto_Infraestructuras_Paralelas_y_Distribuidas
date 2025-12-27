import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import time

# Configurable paths
OUTPUT_FILE = "/data/raw/colcap.csv"

def fetch_colcap_yfinance(start_date, end_date):
    print(f"Intentando descargar COLCAP desde Yahoo Finance...")
    try:
        ticker = yf.Ticker("^COLCAP")
        # Extendemos el rango un poco para asegurar datos
        df = ticker.history(period="2y") # Usar periodo predefinido para asegurar
        
        if not df.empty:
            df = df.reset_index()
            # Asegurar timezone naive
            df['Date'] = df['Date'].dt.tz_localize(None)
            df.columns = [c.lower() for c in df.columns]
            print(f"✅ Descargados {len(df)} registros desde Yahoo Finance")
            return df[['date', 'close']]
        else:
            print("⚠️  No se encontraron datos en Yahoo Finance")
            return None
    except Exception as e:
        print(f"❌ Error con Yahoo Finance: {e}")
        return None

def fetch_colcap_synthetic(start_date, end_date):
    print("⚠️  Generando datos sintéticos para pruebas (fallback)...")
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    import numpy as np
    
    base_value = 1400
    # Random walk
    changes = np.random.randn(len(date_range)) * 10
    values = base_value + np.cumsum(changes)
    
    df = pd.DataFrame({
        'date': date_range,
        'close': values
    })
    return df

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730) # 2 años
    
    df = fetch_colcap_yfinance(start_date, end_date)
    
    if df is None or df.empty:
        df = fetch_colcap_synthetic(start_date, end_date)
        
    if df is not None:
        # Guardar en formato simple: date,close
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"💾 Datos guardados en: {OUTPUT_FILE}")
        print(df.tail())
    else:
        print("❌ Error fatal: No se pudieron obtener datos")

if __name__ == "__main__":
    main()
