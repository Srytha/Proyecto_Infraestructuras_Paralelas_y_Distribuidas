import os
import logging
import requests
import gzip
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DATA_RAW = Path("/data/raw")
WET_PATHS_URL = "https://data.commoncrawl.org/crawl-data/CC-MAIN-2025-51/wet.paths.gz"
COMMON_CRAWL_BASE_URL = "https://data.commoncrawl.org/"
NUM_FILES_TO_DOWNLOAD = 20  # Aumentamos a 20 archivos para tener más datos

def download_file(url, output_path):
    """Descarga un archivo desde una URL."""
    logging.info(f"Descargando {url} -> {output_path}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info("Descarga completada.")
        return True
    except Exception as e:
        logging.error(f"Error descargando {url}: {e}")
        return False

def ingest_common_crawl():
    try:
        # Asegurar directorios
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        logging.info(f"Directorio {DATA_RAW} verificado")

        # 1. Descargar wet.paths.gz si no existe
        wet_paths_file = DATA_RAW / "wet.paths.gz"
        if not wet_paths_file.exists():
            if not download_file(WET_PATHS_URL, wet_paths_file):
                return

        # 2. Leer las primeras rutas de archivos WET
        wet_urls = []
        try:
            with gzip.open(wet_paths_file, "rt") as f:
                for _ in range(NUM_FILES_TO_DOWNLOAD):
                    line = f.readline().strip()
                    if line:
                        wet_urls.append(COMMON_CRAWL_BASE_URL + line)
        except Exception as e:
            logging.error(f"Error leyendo {wet_paths_file}: {e}")
            return

        # 3. Descargar los archivos WET
        for i, url in enumerate(wet_urls):
            filename = f"cc_news_{i:03d}.warc.wet.gz"
            output_path = DATA_RAW / filename
            
            if not output_path.exists():
                download_file(url, output_path)
            else:
                logging.info(f"El archivo {filename} ya existe, saltando.")

        logging.info(f"Ingesta completada: {len(wet_urls)} archivos procesados")

    except Exception as e:
        logging.error(f"Error crítico en ingesta: {e}")
        raise

if __name__ == "__main__":
    ingest_common_crawl()
