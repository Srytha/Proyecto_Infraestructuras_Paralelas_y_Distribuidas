import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# Carpeta donde se guardarán los HTML y CSV
DATA_PATH = os.getenv("DATA_PATH", "./data")
os.makedirs(DATA_PATH, exist_ok=True)

# Portales abiertos para noticias económicas
SOURCES = {
    "eltiempo": "https://www.eltiempo.com/economia",
    "larepublica": "https://www.larepublica.co/economia"
}

# Rango de fechas históricas
START_DATE = datetime(2015, 1, 1)
END_DATE = datetime(2025, 12, 31)

# Lista para almacenar información de noticias
news_list = []

# Función para descargar HTML de una URL
def download_html(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except requests.HTTPError as e:
        print(f"Error al descargar {url}: {e}")
        return ""
    except requests.RequestException as e:
        print(f"Error de conexión {url}: {e}")
        return ""

# Recorrer meses y guardar HTML de portada si existe
current = START_DATE
while current <= END_DATE:
    for name, base_url in SOURCES.items():
        url = f"{base_url}?mes={current.month}&anio={current.year}"
        html = download_html(url)
        if html:
            filename = os.path.join(DATA_PATH, f"{name}_{current.year}_{current.month}.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            news_list.append({
                "portal": name,
                "date": current.strftime("%Y-%m-%d"),
                "url": url,
                "file": filename
            })
            print(f"Guardado: {filename}")
        time.sleep(0.5)  # evitar saturar el portal
    # Siguiente mes
    if current.month == 12:
        current = current.replace(year=current.year + 1, month=1)
    else:
        current = current.replace(month=current.month + 1)

# Guardar CSV con histórico de noticias
df = pd.DataFrame(news_list)
csv_file = os.path.join(DATA_PATH, "news_historic.csv")
df.to_csv(csv_file, index=False)
print(f"Histórico de noticias guardado en {csv_file}, total: {len(news_list)} registros")
