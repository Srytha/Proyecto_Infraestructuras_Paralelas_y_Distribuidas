import os
import logging
import requests
import gzip
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DATA_RAW = Path("/data/raw")
COMMON_CRAWL_BASE_URL = "https://data.commoncrawl.org/"

# Configuración de múltiples crawls para diversidad temporal
# Cada crawl corresponde a un período diferente de 2024
CRAWLS_CONFIG = [
    {"id": "CC-MAIN-2024-10", "files": 4, "period": "Feb-Mar 2024"},
    {"id": "CC-MAIN-2024-22", "files": 4, "period": "May-Jun 2024"},
    {"id": "CC-MAIN-2024-33", "files": 4, "period": "Aug 2024"},
    {"id": "CC-MAIN-2024-46", "files": 4, "period": "Nov 2024"},
]

# Número máximo de descargas paralelas
MAX_PARALLEL_DOWNLOADS = 4


def download_file(args):
    """Descarga un archivo desde una URL (diseñado para uso concurrente)."""
    url, output_path, crawl_id = args
    
    if output_path.exists():
        logging.info(f"[{crawl_id}] Archivo ya existe: {output_path.name}")
        return True, output_path.name, "cached"
    
    logging.info(f"[{crawl_id}] Descargando: {output_path.name}...")
    try:
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            # Descargar a archivo temporal primero
            temp_path = output_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):  # 64KB chunks
                    f.write(chunk)
            # Renombrar atómicamente
            temp_path.rename(output_path)
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logging.info(f"[{crawl_id}] Completado: {output_path.name} ({size_mb:.1f} MB)")
        return True, output_path.name, "downloaded"
    except Exception as e:
        logging.error(f"[{crawl_id}] Error descargando {url}: {e}")
        return False, output_path.name, str(e)


def get_wet_paths_for_crawl(crawl_id, num_files):
    """Obtiene las rutas de archivos WET para un crawl específico."""
    wet_paths_url = f"{COMMON_CRAWL_BASE_URL}crawl-data/{crawl_id}/wet.paths.gz"
    wet_paths_file = DATA_RAW / f"wet.paths.{crawl_id}.gz"
    
    # Descargar índice si no existe
    if not wet_paths_file.exists():
        logging.info(f"Descargando índice de {crawl_id}...")
        try:
            with requests.get(wet_paths_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(wet_paths_file, 'wb') as f:
                    f.write(r.content)
        except Exception as e:
            logging.error(f"Error descargando índice de {crawl_id}: {e}")
            return []
    
    # Leer las primeras N rutas
    wet_urls = []
    try:
        with gzip.open(wet_paths_file, "rt") as f:
            for i, line in enumerate(f):
                if i >= num_files:
                    break
                line = line.strip()
                if line:
                    wet_urls.append(COMMON_CRAWL_BASE_URL + line)
    except Exception as e:
        logging.error(f"Error leyendo índice de {crawl_id}: {e}")
    
    return wet_urls


def ingest_common_crawl():
    """Proceso principal de ingesta multi-crawl con descargas paralelas."""
    start_time = datetime.now()
    
    try:
        # Asegurar directorios
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        logging.info(f"Directorio {DATA_RAW} verificado")
        
        # Estadísticas
        stats = {"downloaded": 0, "cached": 0, "failed": 0, "total_size_mb": 0}
        
        # Recolectar todas las tareas de descarga
        download_tasks = []
        
        for crawl in CRAWLS_CONFIG:
            crawl_id = crawl["id"]
            num_files = crawl["files"]
            period = crawl["period"]
            
            logging.info(f"=== Procesando {crawl_id} ({period}) - {num_files} archivos ===")
            
            wet_urls = get_wet_paths_for_crawl(crawl_id, num_files)
            
            if not wet_urls:
                logging.warning(f"No se encontraron URLs para {crawl_id}")
                continue
            
            for i, url in enumerate(wet_urls):
                # Nombre de archivo incluye el crawl ID para identificación
                filename = f"{crawl_id}_file_{i:03d}.warc.wet.gz"
                output_path = DATA_RAW / filename
                download_tasks.append((url, output_path, crawl_id))
        
        logging.info(f"Total de archivos a procesar: {len(download_tasks)}")
        
        # Ejecutar descargas en paralelo
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
            futures = {executor.submit(download_file, task): task for task in download_tasks}
            
            for future in as_completed(futures):
                success, filename, status = future.result()
                if success:
                    if status == "cached":
                        stats["cached"] += 1
                    else:
                        stats["downloaded"] += 1
                else:
                    stats["failed"] += 1
        
        # Calcular tamaño total
        for f in DATA_RAW.glob("*.warc.wet.gz"):
            stats["total_size_mb"] += f.stat().st_size / (1024 * 1024)
        
        # Resumen final
        elapsed = (datetime.now() - start_time).total_seconds()
        logging.info("=" * 60)
        logging.info("RESUMEN DE INGESTA MULTI-CRAWL")
        logging.info("=" * 60)
        logging.info(f"Crawls procesados: {len(CRAWLS_CONFIG)}")
        logging.info(f"Archivos descargados: {stats['downloaded']}")
        logging.info(f"Archivos en caché: {stats['cached']}")
        logging.info(f"Archivos fallidos: {stats['failed']}")
        logging.info(f"Tamaño total: {stats['total_size_mb']:.1f} MB")
        logging.info(f"Tiempo total: {elapsed:.1f} segundos")
        logging.info("=" * 60)
        
        # Crear archivo de señal para indicar que la ingesta terminó
        flag_file = DATA_RAW / ".ingestion_complete"
        flag_file.write_text(f"Completed at {datetime.now().isoformat()}\nFiles: {stats['downloaded'] + stats['cached']}")
        logging.info(f"Señal de completado creada: {flag_file}")

    except Exception as e:
        logging.error(f"Error crítico en ingesta: {e}")
        raise


if __name__ == "__main__":
    # Eliminar flag de ejecuciones anteriores al iniciar
    flag_file = DATA_RAW / ".ingestion_complete"
    if flag_file.exists():
        flag_file.unlink()
    ingest_common_crawl()

