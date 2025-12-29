import gzip
import re
from warcio.archiveiterator import ArchiveIterator
import csv
import os
from io import BytesIO

# Palabras clave para filtrar contenido económico/noticioso relevante
KEYWORDS_ECONOMIA = [
    "economía", "economia", "bolsa", "mercado", "inflación", "inflacion",
    "dólar", "dolar", "precio", "inversión", "inversion", "banco",
    "finanzas", "pib", "crecimiento", "exportación", "importación",
    "colcap", "empleo", "desempleo", "petróleo", "petroleo",
    "gobierno", "ministerio", "reforma", "impuesto", "tributaria"
]

def extract_crawl_id(filename):
    """Extrae el crawl ID del nombre del archivo."""
    # Formatos esperados: 
    # CC-MAIN-2024-10_file_000.warc.wet.gz (formato antiguo)
    # CC-MAIN-2024-10_news_0001_12345.warc.gz (formato nuevo Index API)
    match = re.match(r'(CC-MAIN-\d{4}-\d+)', filename)
    if match:
        return match.group(1)
    return "unknown"

def is_relevant_content(text):
    """Verifica si el contenido es relevante (contiene palabras clave económicas)."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS_ECONOMIA)

def extract_text_from_html(html_content):
    """Extrae texto limpio de contenido HTML."""
    # Remover scripts y estilos
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remover tags HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    # Limpiar espacios múltiples
    text = re.sub(r'\s+', ' ', text).strip()
    # Decodificar entidades HTML básicas
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    return text

def process_warc_file(warc_path, output_dir):
    """
    Procesa un archivo WARC (segmento individual o archivo completo).
    Compatible tanto con segmentos del Index API como con archivos WET completos.
    """
    filename = os.path.basename(warc_path)
    crawl_id = extract_crawl_id(filename)
    
    # Create worker-specific CSV file to avoid race conditions
    worker_id = os.getpid()
    output_file = os.path.join(output_dir, f"news_worker_{worker_id}.csv")
    write_header = not os.path.exists(output_file)

    records_processed = 0
    records_saved = 0

    try:
        with gzip.open(warc_path, "rb") as stream, \
             open(output_file, "a", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)

            if write_header:
                writer.writerow(["date", "crawl", "text"])

            for record in ArchiveIterator(stream):
                records_processed += 1
                
                # Manejar tanto response (WARC) como conversion (WET)
                if record.rec_type == "response":
                    # Es un registro WARC con HTML
                    date = record.rec_headers.get_header("WARC-Date")
                    content = record.content_stream().read()
                    
                    if not content:
                        continue
                    
                    # Extraer texto del HTML
                    try:
                        html = content.decode("utf-8", errors="ignore")
                        text = extract_text_from_html(html)
                    except:
                        continue
                        
                elif record.rec_type == "conversion":
                    # Es un registro WET (texto plano)
                    date = record.rec_headers.get_header("WARC-Date")
                    content = record.content_stream().read()
                    
                    if not content:
                        continue
                    
                    text = content.decode("utf-8", errors="ignore").strip()
                else:
                    continue

                # Filtro por longitud mínima
                if len(text) < 200:
                    continue
                
                # NOTA: El filtro de keywords está desactivado porque la ingesta
                # via CC Index API ya filtra por secciones económicas (/economia/, etc.)
                # Si deseas filtrado adicional, descomenta las siguientes líneas:
                # if not is_relevant_content(text):
                #     continue

                writer.writerow([date, crawl_id, text])
                records_saved += 1

    except Exception as e:
        print(f"Error procesando {filename}: {e}")
        return {"saved": 0, "processed": 0, "crawl": crawl_id, "error": True}

    print(f"[{crawl_id}] {records_saved}/{records_processed} registros guardados")
    return {"saved": records_saved, "processed": records_processed, "crawl": crawl_id, "error": False}


def process_wet_file(wet_path, output_dir):
    """Wrapper para compatibilidad con el main.py existente."""
    return process_warc_file(wet_path, output_dir)


if __name__ == "__main__":
    # Test con archivo de ejemplo
    import sys
    if len(sys.argv) > 1:
        process_warc_file(sys.argv[1], "/data/processed")
    else:
        print("Uso: python worker.py <archivo.warc.gz>")
