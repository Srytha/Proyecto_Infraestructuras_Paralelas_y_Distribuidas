import os
import pandas as pd
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count

DATA_PATH = os.getenv("DATA_PATH", "./data")
INPUT_CSV = os.path.join(DATA_PATH, "news_historic.csv")
OUTPUT_CSV = os.path.join(DATA_PATH, "news_clean.csv")

df = pd.read_csv(INPUT_CSV)

# Cambiado: ahora recibe directamente el nombre de archivo
def process_file(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            title = soup.title.string if soup.title else ""
            text = soup.get_text(separator=" ", strip=True)
        return title, text
    except:
        return "", ""

# Lista de archivos
files = df["file"].tolist()

# Paralelismo
with Pool(cpu_count()) as pool:
    results = pool.map(process_file, files)

# Separar resultados
titles, texts = zip(*results)
df["title"] = titles
df["text"] = texts

df.to_csv(OUTPUT_CSV, index=False)
print(f"Datos procesados guardados en {OUTPUT_CSV}")
