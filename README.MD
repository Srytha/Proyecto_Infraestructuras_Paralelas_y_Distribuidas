Estructura 

# PROYECTO_IPYD - Infraestructuras Paralelas y Distribuidas

## Objetivo
Procesar noticias de Common Crawl (AWS S3) y correlacionar con índice COLCAP.

## Arquitectura
1. **data-ingestion**: Descarga datos de Common Crawl (S3 público)
2. **data-processing**: Procesamiento paralelo de noticias
3. **correlation-service**: Calcula correlaciones