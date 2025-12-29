import os
import shutil
import time
import logging
import signal
import sys
from pathlib import Path
from worker import process_wet_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATA_RAW = Path("/data/raw")
DATA_PROCESSING = Path("/data/processing")
DATA_PROCESSED = Path("/data/processed")

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    global shutdown_requested
    signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logging.info(f"Recibida señal {signal_name}, terminando gracefully...")
    shutdown_requested = True


def main():
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Asegurar directorios
    DATA_PROCESSING.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    # Esperar a que la ingesta termine (buscar archivo de señal)
    flag_file = DATA_RAW / ".ingestion_complete"
    logging.info("Worker iniciado. Esperando señal de ingesta completada...")
    
    wait_count = 0
    while not flag_file.exists() and not shutdown_requested:
        wait_count += 1
        if wait_count % 6 == 0:  # Log cada 30 segundos
            logging.info("Aún esperando señal de ingesta...")
        time.sleep(5)
    
    if shutdown_requested:
        logging.info("Worker terminado antes de iniciar procesamiento")
        return
    
    logging.info("Señal de ingesta detectada. Iniciando procesamiento...")
    
    # Counter for empty wait cycles (to detect when processing is complete)
    empty_wait_cycles = 0
    MAX_EMPTY_CYCLES = 6  # Exit after 30 seconds of no files (6 * 5 sec)
    files_processed_total = 0
    
    # Statistics collection
    from collections import defaultdict
    from datetime import datetime
    start_time = datetime.now()
    stats_by_crawl = defaultdict(lambda: {"files": 0, "records_processed": 0, "records_saved": 0})
    total_errors = 0

    while not shutdown_requested:
        try:
            # 1. Listar archivos disponibles en RAW (soporta WET y WARC)
            files = [f for f in os.listdir(DATA_RAW) 
                     if f.endswith(".wet.gz") or f.endswith(".warc.gz")]
            
            if not files:
                empty_wait_cycles += 1
                if empty_wait_cycles >= MAX_EMPTY_CYCLES:
                    # Print summary
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logging.info("=" * 60)
                    logging.info("RESUMEN DE PROCESAMIENTO")
                    logging.info("=" * 60)
                    logging.info(f"Tiempo total: {elapsed:.1f} segundos")
                    logging.info(f"Archivos procesados: {files_processed_total}")
                    logging.info(f"Errores: {total_errors}")
                    logging.info("-" * 40)
                    logging.info("Distribución por crawl:")
                    total_saved = 0
                    total_processed = 0
                    for crawl_id, data in sorted(stats_by_crawl.items()):
                        logging.info(f"  {crawl_id}:")
                        logging.info(f"    Archivos: {data['files']}")
                        logging.info(f"    Registros: {data['records_saved']}/{data['records_processed']} guardados")
                        total_saved += data['records_saved']
                        total_processed += data['records_processed']
                    logging.info("-" * 40)
                    logging.info(f"TOTAL: {total_saved} noticias guardadas de {total_processed} registros")
                    logging.info("=" * 60)
                    break
                # Check for shutdown before sleeping
                if shutdown_requested:
                    break
                # Esperar un poco antes de volver a verificar
                time.sleep(5)
                continue
            
            # Reset counter when files are found
            empty_wait_cycles = 0

            # 2. Intentar "reservar" un archivo moviéndolo
            # Debido a la concurrencia, varios workers pueden ver el mismo archivo,
            # pero solo el rename atómico tendrá éxito.
            target_file = None
            for f in files:
                if shutdown_requested:
                    break
                src = DATA_RAW / f
                dst = DATA_PROCESSING / f
                try:
                    # Rename es atómico en POSIX (si está en el mismo volumen)
                    os.rename(src, dst)
                    target_file = dst
                    logging.info(f"Reservado archivo: {f}")
                    break
                except OSError:
                    # Si falla (ej. otro worker ya lo movió), intentar con el siguiente
                    continue
            
            if not target_file:
                time.sleep(1)
                continue

            # 3. Procesar el archivo reservado
            try:
                result = process_wet_file(str(target_file), str(DATA_PROCESSED))
                
                # Acumular estadísticas
                if isinstance(result, dict):
                    crawl = result.get("crawl", "unknown")
                    stats_by_crawl[crawl]["files"] += 1
                    stats_by_crawl[crawl]["records_processed"] += result.get("processed", 0)
                    stats_by_crawl[crawl]["records_saved"] += result.get("saved", 0)
                    if result.get("error"):
                        total_errors += 1
                
                logging.info(f"Procesado: {target_file.name}")
                files_processed_total += 1
                
                # 4. Eliminar el archivo temporal procesado (para no ocupar espacio)
                os.remove(target_file)
                
            except Exception as e:
                logging.error(f"Error procesando {target_file.name}: {e}")
                total_errors += 1
                # Opcional: Mover a una carpeta 'failed' o devolver a 'raw'
                # Por ahora, simplemente lo renombramos con .err para análisis
                error_path = target_file.with_suffix(target_file.suffix + ".err")
                os.rename(target_file, error_path)

        except Exception as e:
            logging.error(f"Error en el ciclo principal: {e}")
            time.sleep(5)
    
    logging.info("Worker terminado gracefully")


if __name__ == "__main__":
    main()
