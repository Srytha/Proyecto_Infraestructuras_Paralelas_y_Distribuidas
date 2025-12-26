import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ingest_news():
    try:
        # Crear directorio si no existe
        os.makedirs("/data/raw", exist_ok=True)
        logging.info("Directorio /data/raw verificado")
        
        # Simulación (reemplazable por Common Crawl)
        news = [
            {"date": "2024-01-10", "text": "Mercados reaccionan a anuncio del banco central"},
            {"date": "2024-01-12", "text": "Sube el COLCAP tras datos económicos positivos"}
        ]

        with open("/data/raw/news.json", "w") as f:
            json.dump(news, f)

        logging.info(f"Ingesta completada: {len(news)} registros")
        
    except OSError as e:
        logging.error(f"Error al crear directorio: {e}")
        raise
    except Exception as e:
        logging.error(f"Error durante la ingesta: {e}")
        raise

if __name__ == "__main__":
    ingest_news()
