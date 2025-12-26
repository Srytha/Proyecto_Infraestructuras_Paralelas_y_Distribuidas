# analysis.py

import pandas as pd
from pathlib import Path

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")
DATA_RESULTS = Path("data/results")

DATA_RESULTS.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1. Cargar COLCAP (BVC)
# --------------------------------------------------

def load_colcap(path="/app/data/raw/colcap.csv"):
    df = pd.read_csv(path)

    # Normalizar columnas
    df.columns = [c.lower().strip() for c in df.columns]

    # Renombrar columnas relevantes
    if "último" in df.columns:
        df["ultimo"] = (
            df["último"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
    elif "ultimo" in df.columns:
        df["ultimo"] = (
            df["ultimo"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
    else:
        raise ValueError("No se encontró columna de valor de mercado en COLCAP")

    return df[["nombre", "ultimo"]]


# --------------------------------------------------
# 2. Cargar noticias procesadas
# --------------------------------------------------

def load_news():
    df = pd.read_csv(DATA_PROCESSED / "news.csv")

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["date"] = pd.to_datetime(df["date"])

    return df


# --------------------------------------------------
# 3. Agregar noticias por día
# --------------------------------------------------

def aggregate_news(df_news):
    daily_news = (
        df_news
        .groupby("date")
        .size()
        .reset_index(name="news_count")
    )
    return daily_news


# --------------------------------------------------
# 4. Calcular correlación
# --------------------------------------------------

def compute_correlation(colcap_df, news_df):
    total_news = len(news_df)
    avg_market_value = colcap_df["ultimo"].mean()

    return {
        "total_news": total_news,
        "avg_market_value": avg_market_value
    }

def save_results(result, path="/app/data/results/correlation.csv"):
    df = pd.DataFrame([result])
    df.to_csv(path, index=False)



# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    colcap_df = load_colcap()
    news_df = load_news()

    daily_news = aggregate_news(news_df)

    merged, corr = compute_correlation(colcap_df, daily_news)

    merged.to_csv(DATA_RESULTS / "correlation.csv", index=False)

    print(f"Correlación COLCAP vs noticias: {corr:.4f}")
