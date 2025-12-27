import pandas as pd
from datetime import datetime, timedelta
import os
import time

# Configurable paths
OUTPUT_FILE = "/data/raw/colcap.csv"

def fetch_colcap_synthetic(start_date, end_date):
    print("Generando datos sintéticos para pruebas (fallback)...")
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
    
    # 1. Buscar archivo manual
    manual_path = "/data/raw/manual_colcap.csv"
    if os.path.exists(manual_path):
        print(f"Archivo manual detectado: {manual_path}")
        try:
            # Leer con separador ; y formato numérico US (miles=, decimal=.)
            # Si el archivo varía, read_csv por defecto (decimal='.') suele funcionar mejor para "2,081.43" si se quitan las comas antes
            # Pero probemos configurando explícitamente formato US
            df = pd.read_csv(manual_path, sep=';', thousands=',', decimal='.')
            
            print(f"Info: Procesando archivo manual. Filas leidas: {len(df)}")
            print(f"Info: Columnas detectadas en CSV: {df.columns.tolist()}")
            
            # Limpiar nombres de columnas
            df.columns = [c.strip() for c in df.columns]
            
            # Mapear columnas BVC (Fecha -> date, Valor hoy -> close)
            rename_map = {
                'Fecha': 'date',
                'Valor hoy': 'close',
                'Date': 'date',
                'Price': 'close',
                'Close': 'close'
            }
            df = df.rename(columns=rename_map)
            
            # Filtrar columnas requeridas
            if 'date' in df.columns and 'close' in df.columns:
                 print("Archivo manual valido (columnas mapeadas correctamente)")
                 df = df[['date', 'close']]
                 
                 # Vista previa de datos manuales
                 print(f"Info: Primeras filas del archivo manual:\n{df.head(2)}")
                 
                 df['date'] = pd.to_datetime(df['date'])
                 # Convertir close a numérico (asegurar compatibilidad)
                 df['close'] = pd.to_numeric(df['close'], errors='coerce')
                 
                 count_before = len(df)
                 df = df.dropna()
                 count_after = len(df)
                 print(f"Info: Filas válidas importadas desde CSV: {count_after} (de {count_before})")
            else:
                 print(f"Columnas encontradas: {df.columns.tolist()}")
                 print("No se encontraron columnas 'Fecha'/'Valor hoy' ni sus variantes.")
                 df = None
        except Exception as e:
            print(f"Error leyendo archivo manual: {e}")
            df = None
    else:
        df = None

    # 2. Si no hay manual, Fallback sintético
    if df is None or df.empty:
        df = fetch_colcap_synthetic(start_date, end_date)
        
    if df is not None:
        # Guardar en formato simple: date,close
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Datos guardados en: {OUTPUT_FILE}")
        print(df.tail())
    else:
        print("Error fatal: No se pudieron obtener datos")

if __name__ == "__main__":
    main()
