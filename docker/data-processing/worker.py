import gzip
import re
from warcio.archiveiterator import ArchiveIterator
import csv
import os

# Palabras clave para filtrar contenido económico/noticioso relevante
KEYWORDS_ECONOMIA = [
    "economía", "economia", "bolsa", "mercado", "inflación", "inflacion",
    "dólar", "dolar", "precio", "inversión", "inversion", "banco",
    "finanzas", "pib", "crecimiento", "exportación", "importación",
    "colcap", "empleo", "desempleo", "petróleo", "petroleo"
]

def extract_crawl_id(filename):
    """Extrae el crawl ID del nombre del archivo."""
    # Formato esperado: CC-MAIN-2024-10_file_000.warc.wet.gz
    match = re.match(r'(CC-MAIN-\d{4}-\d+)', filename)
    if match:
        return match.group(1)
    return "unknown"

def is_relevant_content(text):
    """Verifica si el contenido es relevante (contiene palabras clave económicas)."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS_ECONOMIA)

def process_wet_file(wet_path, output_dir):
    # Extraer crawl_id del nombre del archivo
    filename = os.path.basename(wet_path)
    crawl_id = extract_crawl_id(filename)
    
    # Create worker-specific CSV file to avoid race conditions
    worker_id = os.getpid()
    output_file = os.path.join(output_dir, f"news_worker_{worker_id}.csv")
    write_header = not os.path.exists(output_file)

    records_processed = 0
    records_saved = 0

    with gzip.open(wet_path, "rb") as stream, \
         open(output_file, "a", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        if write_header:
            writer.writerow(["date", "crawl", "text"])

        for record in ArchiveIterator(stream):
            if record.rec_type != "conversion":
                continue

            records_processed += 1
            date = record.rec_headers.get_header("WARC-Date")

            content = record.content_stream().read()
            if not content:
                continue

            text = content.decode("utf-8", errors="ignore").strip()

            # Filtro por longitud mínima
            if len(text) < 200:
                continue
            
            # Filtro por relevancia (opcional - descomentar para activar)
            # if not is_relevant_content(text):
            #     continue

            writer.writerow([date, crawl_id, text])
            records_saved += 1

    print(f"Procesamiento WET completado: {records_saved}/{records_processed} registros guardados (crawl: {crawl_id})")

if __name__ == "__main__":
    process_wet_file(
        "/data/raw/CC-MAIN-2024-10_file_000.warc.wet.gz",
        "/data/processed"
    )

