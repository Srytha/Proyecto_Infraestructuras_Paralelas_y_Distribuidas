# Distributed News & Economic Data Analysis System

Este proyecto es una implementación de un sistema distribuido escalable diseñado para procesar grandes volúmenes de datos web (Common Crawl) y correlacionar tendencias noticiosas con indicadores económicos (COLCAP).

## Características Principales

*   **Ingesta Multi-Crawl**: Descarga automatizada de archivos WET desde **4 crawls diferentes de 2024** para análisis temporal diverso:
    *   `CC-MAIN-2024-10` (Feb-Mar 2024)
    *   `CC-MAIN-2024-22` (May-Jun 2024)
    *   `CC-MAIN-2024-33` (Aug 2024)
    *   `CC-MAIN-2024-46` (Nov 2024)
*   **Optimización de Memoria**: El servicio de correlación implementa una carga selectiva de columnas (ignorando textos largos) para procesar cientos de miles de noticias sin saturar la RAM.
*   **Descargas Paralelas**: Uso de `ThreadPoolExecutor` para descargar hasta 4 archivos simultáneamente.
*   **Procesamiento Distribuido**: Arquitectura escalable con múltiples workers que procesan archivos en paralelo usando un mecanismo de bloqueo (move-to-process) seguro.
*   **Análisis Económico**: Obtención de datos históricos del índice COLCAP usando Yahoo Finance.
*   **Correlación Temporal**: Análisis estadístico cruzando volumen de noticias diarias con el cierre del mercado, con datos de múltiples períodos.
*   **Infraestructura como Código**: Dockerfiles optimizados para cada microservicio y orquestación con Kubernetes.


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

Crear directorios de datos y limpiar resultados anteriores (borrando también descargas y `colcap.csv` generado, pero manteniendo CSVs manuales):
```bash
sudo rm -rf data/processed/* data/processing/* data/results/* data/raw/colcap.csv data/raw/*.gz
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

El sistema requiere archivos históricos del índice COLCAP para funcionar.
1.  **Coloca tus archivos CSV** en la carpeta `data/raw/` **ANTES** de ejecutar el contenedor.
2.  **Formato soportado**:
    *   Nombre de archivo sugerido: `YYYY-MM-DD--YYYY-MM-DD.csv` (e.g., `2024-02-01--2024-05-01.csv`).
    *   Separador: `;` (Punto y coma) o `,` (Coma).
    *   Columnas requeridas: `Fecha` y `Valor hoy` (o `Date` y `Close`).
    *   Ejemplo de contenido:
        ```csv
        Fecha;Valor hoy;Apertura;...
        01/02/2024;1.285,45;1.280,10;...
        ```
3.  **Ejecutar el servicio de consolidación**:
    Este servicio buscará *todos* los CSVs en `data/raw`, los unirá y generará un archivo maestro `colcap.csv` estandarizado.

```bash
docker run --rm -v $(pwd)/data:/data economic-data:latest
```
*Esto generará `data/raw/colcap.csv` listo para el análisis.*

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
*   `data/`: Directorio de volumen compartido (se crea al ejecutar).
