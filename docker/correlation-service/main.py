import pandas as pd
import numpy as np
import os

DATA_PATH = "./data"
NEWS_FILE = os.path.join(DATA_PATH, "news_clean.csv")
COLCAP_FILE = os.path.join(DATA_PATH, "colcap.csv")

# ======================
# Leer datos
# ======================
news_df = pd.read_csv(NEWS_FILE)
colcap_df = pd.read_csv(COLCAP_FILE)

# ======================
# Fechas
# ======================
news_df["date"] = pd.to_datetime(news_df["date"])
colcap_df["Date"] = pd.to_datetime(colcap_df["Date"], dayfirst=False)

# ======================
# Limpiar precio COLCAP
# ======================
colcap_df["Price"] = colcap_df["Price"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)

# ======================
# Contar noticias por fecha
# ======================
news_counts = news_df.groupby("date").size().reset_index(name="news_count")

# ======================
# Merge con COLCAP
# ======================
merged = pd.merge(colcap_df, news_counts, left_on="Date", right_on="date", how="left")
merged["news_count"] = merged["news_count"].fillna(0)

# ======================
# Agrupar por semana
# ======================
merged["week"] = merged["Date"].dt.to_period("W")
weekly = merged.groupby("week")[["Price", "news_count"]].mean().reset_index()

# ======================
# Promedio móvil 3 semanas
# ======================
weekly["Price_smooth"] = weekly["Price"].rolling(window=3, min_periods=1).mean()
weekly["news_smooth"] = weekly["news_count"].rolling(window=3, min_periods=1).mean()

# ======================
# Logaritmo para reducir dispersión
# ======================
weekly["Price_log"] = np.log1p(weekly["Price_smooth"])
weekly["news_log"] = np.log1p(weekly["news_smooth"])

# ======================
# Correlación Spearman final
# ======================
correlation = weekly["news_log"].corr(weekly["Price_log"], method="spearman")
print(f"Correlación semanal suavizada y log (Spearman): {correlation}")
