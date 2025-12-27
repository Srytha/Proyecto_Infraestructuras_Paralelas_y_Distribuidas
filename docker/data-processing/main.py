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
    
    logging.info("Worker iniciado. Esperando archivos...")

    while not shutdown_requested:
        try:
            # 1. Listar archivos disponibles en RAW
            files = [f for f in os.listdir(DATA_RAW) if f.endswith(".wet.gz")]
            
            if not files:
                # Check for shutdown before sleeping
                if shutdown_requested:
                    break
                # Esperar un poco antes de volver a verificar para no saturar CPU
                time.sleep(5)
                continue

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
                process_wet_file(str(target_file), str(DATA_PROCESSED))
                logging.info(f"Procesado exitosamente: {target_file.name}")
                
                # 4. Eliminar el archivo temporal procesado (para no ocupar espacio)
                os.remove(target_file)
                
            except Exception as e:
                logging.error(f"Error procesando {target_file.name}: {e}")
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
