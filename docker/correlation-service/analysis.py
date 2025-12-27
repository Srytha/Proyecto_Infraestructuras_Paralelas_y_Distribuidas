# analysis.py

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATA_RAW = Path("/data/raw")
DATA_PROCESSED = Path("/data/processed")
DATA_RESULTS = Path("/data/results")

DATA_RESULTS.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1. Cargar COLCAP
# --------------------------------------------------

def load_colcap(path="/data/raw/colcap.csv"):
    try:
        logging.info(f"Cargando COLCAP desde {path}")
        df = pd.read_csv(path)
        # Esperamos columnas date, close
        # Convertir date a datetime
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
        return df
    except Exception as e:
        logging.error(f"Error cargando COLCAP: {e}")
        return pd.DataFrame(columns=["date", "close"])


# --------------------------------------------------
# 2. Cargar noticias procesadas
# --------------------------------------------------

def load_news():
    path = DATA_PROCESSED / "news.csv"
    try:
        logging.info(f"Cargando noticias desde {path}")
        if not path.exists():
            logging.warning("No se encontró archivo de noticias.")
            return pd.DataFrame(columns=["date", "text"])
            
        df = pd.read_csv(path, on_bad_lines='skip') # Saltar lineas corruptas

        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        return df
    except Exception as e:
        logging.error(f"Error cargando noticias: {e}")
        return pd.DataFrame(columns=["date", "text"])


# --------------------------------------------------
# 3. Agregar noticias por día
# --------------------------------------------------

def aggregate_news(df_news):
    if df_news.empty:
        return pd.DataFrame(columns=["date", "news_count"])
        
    # Agrupar por fecha (día)
    df_news["day"] = df_news["date"].dt.date
    
    daily_news = (
        df_news
        .groupby("day")
        .size()
        .reset_index(name="news_count")
    )
    daily_news["date"] = pd.to_datetime(daily_news["day"])
    return daily_news[["date", "news_count"]]


# --------------------------------------------------
# 4. Calcular correlación
# --------------------------------------------------

def compute_correlation(colcap_df, news_df):
    if colcap_df.empty or news_df.empty:
        logging.warning("Dataframes vacíos, no se puede calcular correlación")
        return pd.DataFrame(), 0.0

    # Unir por fecha
    merged = pd.merge(colcap_df, news_df, on="date", how="inner")
    
    if len(merged) < 1:
        logging.warning("Insuficientes datos coincidentes para correlación")
        return merged, 0.0
        
    corr = merged["close"].corr(merged["news_count"])
    
    return merged, corr

# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    colcap_df = load_colcap()
    news_df = load_news()

    daily_news = aggregate_news(news_df)

    merged, corr = compute_correlation(colcap_df, daily_news)

    if not merged.empty:
        output_path = DATA_RESULTS / "correlation.csv"
        merged.to_csv(output_path, index=False)
        logging.info(f"Resultados guardados en {output_path}")
        print(f"Correlación COLCAP vs Cantidad Noticias: {corr:.4f}")
    else:
        logging.warning("No se generaron resultados de correlación.")
