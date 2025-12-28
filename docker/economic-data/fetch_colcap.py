import pandas as pd
from datetime import datetime, timedelta
import os
import glob
import re

# Configurable paths
OUTPUT_FILE = "/data/raw/colcap.csv"
MANUAL_CSV_DIR = "/data/raw"

def fetch_colcap_synthetic(start_date, end_date):
    """Genera datos sintéticos como fallback."""
    print("Generando datos sintéticos para pruebas (fallback)...")
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    import numpy as np
    
    base_value = 1400
    changes = np.random.randn(len(date_range)) * 10
    values = base_value + np.cumsum(changes)
    
    df = pd.DataFrame({
        'date': date_range,
        'close': values
    })
    return df


def load_single_csv(filepath):
    """Carga y normaliza un archivo CSV de COLCAP."""
    print(f"  Cargando: {os.path.basename(filepath)}")
    
    try:
        # Intentar con separador ; primero (formato BVC)
        df = pd.read_csv(filepath, sep=';', thousands=',', decimal='.')
    except:
        # Fallback a coma
        df = pd.read_csv(filepath)
    
    # Limpiar nombres de columnas
    df.columns = [c.strip() for c in df.columns]
    
    # Mapear columnas conocidas
    rename_map = {
        'Fecha': 'date',
        'Valor hoy': 'close',
        'Date': 'date',
        'Price': 'close',
        'Close': 'close'
    }
    df = df.rename(columns=rename_map)
    
    if 'date' not in df.columns or 'close' not in df.columns:
        print(f"    ⚠ Columnas no reconocidas: {df.columns.tolist()}")
        return None
    
    df = df[['date', 'close']]
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.dropna()
    
    print(f"    ✓ {len(df)} filas válidas")
    return df


def find_colcap_csvs():
    """Encuentra todos los CSVs de COLCAP con patrón de fechas."""
    # Patrón: cualquier cosa que parezca fechas con guiones
    # Ejemplos: 2024-02-01--2024-05-01.csv, 202-02-01--2024-05-01.csv
    pattern = os.path.join(MANUAL_CSV_DIR, "*--*.csv")
    files = glob.glob(pattern)
    
    # También buscar manual_colcap.csv
    manual_single = os.path.join(MANUAL_CSV_DIR, "manual_colcap.csv")
    if os.path.exists(manual_single):
        files.append(manual_single)
    
    return sorted(files)


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    # 1. Buscar archivos CSV de COLCAP
    csv_files = find_colcap_csvs()
    
    if csv_files:
        print(f"Encontrados {len(csv_files)} archivos CSV de COLCAP:")
        
        all_dfs = []
        for csv_file in csv_files:
            df = load_single_csv(csv_file)
            if df is not None and not df.empty:
                all_dfs.append(df)
        
        if all_dfs:
            # Combinar todos los DataFrames
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            # Eliminar duplicados por fecha (quedarse con el último valor)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            
            # Ordenar por fecha
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
            
            print(f"\n=== RESUMEN ===")
            print(f"Total de registros combinados: {len(combined_df)}")
            print(f"Rango de fechas: {combined_df['date'].min()} a {combined_df['date'].max()}")
            
            df = combined_df
        else:
            print("No se pudieron cargar datos de los archivos CSV.")
            df = None
    else:
        print("No se encontraron archivos CSV de COLCAP.")
        df = None
    
    # 2. Fallback sintético si no hay datos
    if df is None or df.empty:
        df = fetch_colcap_synthetic(start_date, end_date)
    
    # 3. Guardar resultado
    if df is not None and not df.empty:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nDatos guardados en: {OUTPUT_FILE}")
        print("\nÚltimas 5 filas:")
        print(df.tail())
    else:
        print("Error fatal: No se pudieron obtener datos")


if __name__ == "__main__":
    main()

