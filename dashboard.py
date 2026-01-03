import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# -----------------------------
# Configuración general
# -----------------------------
st.set_page_config(
    page_title="Dashboard Noticias vs COLCAP",
    layout="wide"
)

# -----------------------------
# Carga de datos
# -----------------------------
correlation = pd.read_csv(
    "data/results/correlation.csv",
    parse_dates=["date"]
)

news = pd.read_csv(
    "data/processed/news_worker_1.csv",
    parse_dates=["date"]
)

colcap = pd.read_csv(
    "data/raw/colcap.csv",
    parse_dates=["date"]
)

st.title("Análisis Distribuido de Noticias y COLCAP")

# =====================================================
# 1. Evolución temporal
# =====================================================
st.header("1. Evolución temporal")

fig, ax1 = plt.subplots(figsize=(16, 6))

# COLCAP
ax1.plot(
    correlation["date"],
    correlation["close"],
    color="tab:blue",
    label="COLCAP"
)
ax1.set_ylabel("COLCAP", color="tab:blue")
ax1.tick_params(axis="y", labelcolor="tab:blue")

# Formato de fechas
ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
fig.autofmt_xdate()

# Noticias (segundo eje)
ax2 = ax1.twinx()
ax2.plot(
    correlation["date"],
    correlation["news_count"],
    color="tab:red",
    label="Cantidad de noticias",
    alpha=0.7
)
ax2.set_ylabel("Cantidad de noticias", color="tab:red")
ax2.tick_params(axis="y", labelcolor="tab:red")

# Título
ax1.set_title("Evolución temporal: COLCAP vs Noticias")

st.pyplot(fig)

# =====================================================
# 2. Correlación Noticias vs COLCAP
# =====================================================
st.header("2. Correlación Noticias vs COLCAP")

fig2, ax = plt.subplots(figsize=(8, 6))
ax.scatter(
    correlation["news_count"],
    correlation["close"],
    alpha=0.6
)
ax.set_xlabel("Cantidad de noticias")
ax.set_ylabel("COLCAP")
ax.set_title("Relación entre noticias y COLCAP")

st.pyplot(fig2)

# =====================================================
# 3. Noticias por Crawl (Common Crawl)
# =====================================================
st.header("3. Noticias por Crawl (Common Crawl)")

crawl_counts = news["crawl"].value_counts()

fig3, ax = plt.subplots(figsize=(10, 5))
crawl_counts.plot(kind="bar", ax=ax)
ax.set_xlabel("Crawl")
ax.set_ylabel("Cantidad de noticias")
ax.set_title("Distribución de noticias por crawl")

st.pyplot(fig3)

# =====================================================
# 4. Capacidad del sistema
# =====================================================
st.header("4. Capacidad del sistema")

worker_data = {
    "worker_1": len(news)
}

workers_df = pd.DataFrame.from_dict(
    worker_data,
    orient="index",
    columns=["Noticias procesadas"]
)

fig4, ax = plt.subplots(figsize=(6, 4))
workers_df.plot(kind="bar", ax=ax, legend=False)
ax.set_xlabel("Worker")
ax.set_ylabel("Noticias procesadas")
ax.set_title("Capacidad de procesamiento por worker")

st.pyplot(fig4)