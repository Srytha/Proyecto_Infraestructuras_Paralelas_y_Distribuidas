import os
from worker import process_wet_file

DATA_RAW = "/app/data/raw"
DATA_PROCESSED = "/app/data/processed"

def main():
    os.makedirs(DATA_PROCESSED, exist_ok=True)

    wet_files = [
        f for f in os.listdir(DATA_RAW)
        if f.endswith(".wet.gz")
    ]

    if not wet_files:
        raise FileNotFoundError("No se encontraron archivos .wet.gz en data/raw")

    for wet_file in wet_files:
        process_wet_file(
            os.path.join(DATA_RAW, wet_file),
            DATA_PROCESSED
        )

    print("Procesamiento completado")

if __name__ == "__main__":
    main()
