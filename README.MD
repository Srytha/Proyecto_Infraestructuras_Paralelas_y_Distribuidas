# Distributed News & Economic Data Analysis System

Este proyecto es una implementación de un sistema distribuido escalable diseñado para procesar grandes volúmenes de datos web (Common Crawl) y correlacionar tendencias noticiosas con indicadores económicos (COLCAP).

## Características Principales

*   **Ingesta de Datos Reales**: Descarga automatizada de archivos WET (texto plano) desde el dataset de diciembre 2025 de Common Crawl.
*   **Procesamiento Distribuido**: Arquitectura scalable con múltiples workers que procesan archivos en paralelo usando un mecanismo de bloqueo (move-to-process) seguro.
*   **Análisis Económico**: Obtención de datos históricos del índice COLCAP usando Yahoo Finance.
*   **Correlación**: Análisis estadístico para cruzar volumen de noticias diarias con el cierre del mercado.
*   **Infraestructura como Código**: Dockerfiles optimizados para cada microservicio y orquestación manual mediante volúmenes compartidos.

## Arquitectura

El sistema consta de 4 microservicios interconectados mediante un volumen compartido (`/data`):

1.  **Data Ingestion**: Descarga archivos `.wet.gz` de Common Crawl a `/data/raw`.
2.  **Data Processing**: Scaling workers (replicas) que toman archivos, los procesan y extraen noticias relevantes a `/data/processed`.
3.  **Economic Data**: Descarga y normaliza el historial del COLCAP a `/data/raw/colcap.csv`.
4.  **Correlation Service**: Lee los datos procesados y económicos, y genera el análisis final en `/data/results`.

## Requisitos Previos

*   Docker
*   (Opcional) Cluster de Kubernetes (Minikube, EKS, GKE) para despliegue en producción.

## Ejecución Manual con Docker

A continuación los pasos para construir y ejecutar cada servicio individualmente, simulando el entorno distribuido.

### 1. Preparación

Crear directorios de datos y limpiar entorno:
```bash
sudo rm -rf data/processed/* data/raw/* data/processing/*
mkdir -p data/raw data/processed data/processing data/results
```

### 2. Construcción de Imágenes

```bash
docker build -t data-ingestion:latest docker/data-ingestion
docker build -t data-processing:latest docker/data-processing
docker build -t economic-data:latest docker/economic-data
docker build -t correlation-service:latest docker/correlation-service
```

### 3. Ejecución de Servicios

Ejecutar en orden secuencial (o paralelo si se abren varias terminales), montando siempre el volumen local `./data` a `/data` en el contenedor.

**Paso A: Ingesta de Noticias (Common Crawl)**
```bash
docker run --rm -v $(pwd)/data:/data data-ingestion:latest
```
*Esto descargará los archivos WET a `data/raw`.*

**Paso B: Datos Económicos (COLCAP)**
```bash
docker run --rm -v $(pwd)/data:/data economic-data:latest
```
*Esto descargará el histórico de precios a `data/raw/colcap.csv`.*

**Paso C: Procesamiento (Ejecutar múltiples Workers)**
Para simular concurrencia, abre varias terminales y en cada una ejecuta:
```bash
docker run --rm -v $(pwd)/data:/data data-processing:latest
```
*Los workers tomarán archivos de `raw`, los moverán a `processing` y guardarán resultados en `processed`.*

**Paso D: Correlación Final**
Una vez terminados los pasos anteriores:
```bash
docker run --rm -v $(pwd)/data:/data correlation-service:latest
```

### 4. Verificar Resultados

```bash
cat data/results/correlation.csv
```

## Estructura del Proyecto

*   `docker/`: Código fuente y Dockerfiles de los 4 microservicios.
*   `kubernetes/`: Manifiestos YAML para despliegue (Deployments, PVC).
*   `docker-compose.yaml`: Orquestación local.
*   `data/`: Directorio de volumen compartido (se crea al ejecutar).
