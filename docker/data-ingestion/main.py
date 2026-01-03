import os
import logging
import requests
import gzip
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DATA_RAW = Path("/data/raw")
COMMON_CRAWL_BASE_URL = "https://data.commoncrawl.org/"
CC_INDEX_SERVER = "https://index.commoncrawl.org"

# Configuración de todos los crawls de 2024 para máxima cobertura temporal
CRAWLS_CONFIG = [
    {"id": "CC-MAIN-2024-10", "period": "Feb-Mar 2024"},
    {"id": "CC-MAIN-2024-18", "period": "Apr 2024"},
    {"id": "CC-MAIN-2024-22", "period": "May-Jun 2024"},
    {"id": "CC-MAIN-2024-26", "period": "Jun-Jul 2024"},
    {"id": "CC-MAIN-2024-30", "period": "Jul 2024"},
    {"id": "CC-MAIN-2024-33", "period": "Aug 2024"},
    {"id": "CC-MAIN-2024-38", "period": "Sep 2024"},
    {"id": "CC-MAIN-2024-42", "period": "Oct 2024"},
    {"id": "CC-MAIN-2024-46", "period": "Nov 2024"},
    {"id": "CC-MAIN-2024-51", "period": "Dec 2024"},
]

# Dominios de noticias colombianas relevantes para correlación económica
DOMINIOS_NOTICIAS = [
    "eltiempo.com",
    "elespectador.com",
    "portafolio.co",
    "larepublica.co",
    "dinero.com",
    "semana.com",
    "elcolombiano.com",
    "elnuevosiglo.com.co",
    "valoraanalitik.com",   # Muy relevante para mercados/COLCAP
    "dataifx.com",          # Noticias financieras
    "forbes.co",            # Economía
    "bloomberglinea.com",   # Economía (filtrar por /colombia si es posible, o por keywords)
    "elheraldo.co",         # Regional importante
    "elpais.com.co",        # Regional importante
    "vanguardia.com",       # Regional importante
    "eluniversal.com.co",   # Regional importante
    "bluradio.com",         # Radio/Noticias
    "rcnradio.com",         # Radio/Noticias
]

# Secciones de interés (filtro adicional por URL)
SECCIONES_RELEVANTES = [
    "/economia/", "/negocios/", "/finanzas/", "/mercados/",
    "/empresas/", "/politica/", "/business/", "/money/",
    "/inversion/", "/mis-finanzas/", "/ahorro/",
    "/internacional/", "/mundo/", "/globoeconomia/", # Contexto externo (Dólar, FED)
    "/opinion/", "/analisis/", "/editorial/",        # Sentimiento de mercado
    "/energia/", "/petroleo/", "/minas/",            # Ecopetrol y mineras (clave en COLCAP)
    "/infraestructura/", "/vivienda/",               # Construcción (Argos, etc.)
    "/agro/", "/campo/",                             # Sector agrario
    "/tecnologia/", "/emprendimiento/",              # Nuevos sectores
    "/legal/", "/juridica/",                         # Cambios regulatorios
]

# Límites por crawl para balancear la carga
MAX_RECORDS_PER_DOMAIN = 200  # Reducido para evitar timeouts
MAX_PARALLEL_DOWNLOADS = 4
MAX_RETRIES = 3  # Reintentos ante errores


def query_cc_index(crawl_id, domain, max_records=200):
    """
    Consulta el Common Crawl Index API para obtener registros de un dominio específico.
    Incluye reintentos con backoff exponencial para manejar errores 504.
    """
    import time
    
    index_url = f"{CC_INDEX_SERVER}/{crawl_id}-index"
    
    # Query URL con wildcard para capturar subdominios
    query_url = f"*.{domain}/*"
    
    params = {
        "url": query_url,
        "output": "json",
        "limit": max_records
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                wait_time = 2 ** attempt  # 2, 4, 8 segundos
                logging.info(f"[{crawl_id}] Reintento {attempt + 1}/{MAX_RETRIES} para {domain} (esperando {wait_time}s)...")
                time.sleep(wait_time)
            
            logging.info(f"[{crawl_id}] Consultando índice para {domain}...")
            response = requests.get(index_url, params=params, timeout=90)
            
            if response.status_code == 404:
                logging.warning(f"[{crawl_id}] Índice no encontrado para {domain}")
                return []
            
            if response.status_code == 504:
                logging.warning(f"[{crawl_id}] Timeout del servidor para {domain}, reintentando...")
                continue
            
            response.raise_for_status()
            
            # El API retorna JSON lines (un JSON por línea)
            records = []
            for line in response.text.strip().split('\n'):
                if line:
                    try:
                        record = json.loads(line)
                        # Filtrar por secciones relevantes
                        url = record.get('url', '')
                        if any(seccion in url.lower() for seccion in SECCIONES_RELEVANTES):
                            records.append(record)
                    except json.JSONDecodeError:
                        continue
            
            logging.info(f"[{crawl_id}] Encontrados {len(records)} registros relevantes para {domain}")
            return records
            
        except requests.exceptions.Timeout:
            logging.warning(f"[{crawl_id}] Timeout consultando {domain}")
            continue
        except Exception as e:
            logging.error(f"[{crawl_id}] Error consultando índice para {domain}: {e}")
            if attempt < MAX_RETRIES - 1:
                continue
            return []
    
    logging.warning(f"[{crawl_id}] Agotados reintentos para {domain}")
    return []


def download_warc_segment(args):
    """
    Descarga un segmento específico de un archivo WARC usando Range Request.
    Esto es mucho más eficiente que descargar archivos completos.
    """
    record, output_path, crawl_id = args
    
    if output_path.exists():
        return True, output_path.name, "cached"
    
    try:
        filename = record.get('filename')
        offset = int(record.get('offset', 0))
        length = int(record.get('length', 0))
        
        if not filename or length == 0:
            return False, "", "invalid_record"
        
        url = f"{COMMON_CRAWL_BASE_URL}{filename}"
        
        # Usar Range Request para descargar solo el segmento necesario
        headers = {
            'Range': f'bytes={offset}-{offset + length - 1}'
        }
        
        response = requests.get(url, headers=headers, timeout=120)
        
        if response.status_code in [200, 206]:
            # Guardar el segmento comprimido
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            logging.debug(f"[{crawl_id}] Descargado: {output_path.name} ({size_kb:.1f} KB)")
            return True, output_path.name, "downloaded"
        else:
            return False, output_path.name, f"http_{response.status_code}"
            
    except Exception as e:
        logging.error(f"[{crawl_id}] Error descargando segmento: {e}")
        return False, output_path.name, str(e)


def ingest_from_index():
    """
    Proceso principal de ingesta usando Common Crawl Index API.
    Busca contenido económico de noticias colombianas en múltiples crawls.
    """
    start_time = datetime.now()
    
    try:
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        logging.info(f"Directorio {DATA_RAW} verificado")
        
        stats = {"downloaded": 0, "cached": 0, "failed": 0, "total_records": 0}
        all_download_tasks = []
        
        for crawl in CRAWLS_CONFIG:
            crawl_id = crawl["id"]
            period = crawl["period"]
            
            logging.info(f"{'='*60}")
            logging.info(f"Procesando {crawl_id} ({period})")
            logging.info(f"{'='*60}")
            
            crawl_records = []
            
            # Consultar cada dominio de noticias
            for domain in DOMINIOS_NOTICIAS:
                records = query_cc_index(crawl_id, domain, MAX_RECORDS_PER_DOMAIN)
                crawl_records.extend(records)
            
            logging.info(f"[{crawl_id}] Total registros encontrados: {len(crawl_records)}")
            stats["total_records"] += len(crawl_records)
            
            # Preparar tareas de descarga
            for i, record in enumerate(crawl_records):
                # Crear nombre único basado en hash del URL
                url_hash = hash(record.get('url', '')) % 100000
                filename = f"{crawl_id}_news_{i:04d}_{url_hash}.warc.gz"
                output_path = DATA_RAW / filename
                all_download_tasks.append((record, output_path, crawl_id))
        
        logging.info(f"\nTotal de segmentos a descargar: {len(all_download_tasks)}")
        
        # Ejecutar descargas en paralelo
        if all_download_tasks:
            with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
                futures = {executor.submit(download_warc_segment, task): task 
                          for task in all_download_tasks}
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    success, filename, status = future.result()
                    
                    if success:
                        if status == "cached":
                            stats["cached"] += 1
                        else:
                            stats["downloaded"] += 1
                    else:
                        stats["failed"] += 1
                    
                    # Progress log cada 50 archivos
                    if completed % 50 == 0:
                        logging.info(f"Progreso: {completed}/{len(all_download_tasks)} segmentos")
        
        # Calcular tamaño total
        total_size_mb = sum(f.stat().st_size for f in DATA_RAW.glob("*.warc.gz")) / (1024 * 1024)
        
        # Resumen final
        elapsed = (datetime.now() - start_time).total_seconds()
        logging.info("=" * 60)
        logging.info("RESUMEN DE INGESTA (Common Crawl Index API)")
        logging.info("=" * 60)
        logging.info(f"Crawls procesados: {len(CRAWLS_CONFIG)}")
        logging.info(f"Dominios consultados: {len(DOMINIOS_NOTICIAS)}")
        logging.info(f"Registros encontrados en índice: {stats['total_records']}")
        logging.info(f"Segmentos descargados: {stats['downloaded']}")
        logging.info(f"Segmentos en caché: {stats['cached']}")
        logging.info(f"Segmentos fallidos: {stats['failed']}")
        logging.info(f"Tamaño total: {total_size_mb:.1f} MB")
        logging.info(f"Tiempo total: {elapsed:.1f} segundos")
        logging.info("=" * 60)
        
        # Crear archivo de señal
        flag_file = DATA_RAW / ".ingestion_complete"
        flag_file.write_text(
            f"Completed at {datetime.now().isoformat()}\n"
            f"Records: {stats['downloaded'] + stats['cached']}\n"
            f"Method: CC Index API\n"
            f"Domains: {', '.join(DOMINIOS_NOTICIAS)}"
        )
        logging.info(f"Señal de completado creada: {flag_file}")
        
    except Exception as e:
        logging.error(f"Error crítico en ingesta: {e}")
        raise


if __name__ == "__main__":
    # Eliminar flag de ejecuciones anteriores
    flag_file = DATA_RAW / ".ingestion_complete"
    if flag_file.exists():
        flag_file.unlink()
    
    ingest_from_index()
