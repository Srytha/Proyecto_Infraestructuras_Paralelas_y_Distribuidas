Estructura 

# PROYECTO- Infraestructuras Paralelas y Distribuidas

## Tutorial: Preparación de Datos (data/raw)

Este tutorial te guiará para obtener y preparar los datos necesarios desde Common Crawl.

### Paso 1: Crear el directorio de datos

```bash
mkdir -p data/raw
```

### Paso 2: Descargar el índice de archivos WET

```bash
curl -L https://data.commoncrawl.org/crawl-data/CC-MAIN-2024-10/wet.paths.gz -o wet.paths.gz
```

### Paso 3: Verificar que el archivo se descargó correctamente

```bash
file wet.paths.gz
```

Deberías ver algo como: `wet.paths.gz: gzip compressed data`

### Paso 4: Extraer y visualizar las primeras rutas

Una vez que `wet.paths.gz` sea válido:

```bash
gunzip -c wet.paths.gz | head -n 3
```

### Paso 5: Descargar un archivo WET específico

Copia una línea real del paso anterior, por ejemplo:

```
crawl-data/CC-MAIN-2024-10/segments/.../wet/CC-MAIN-20240410123456-00000.warc.wet.gz
```

Y descárgala así:

```bash
curl -L https://data.commoncrawl.org/<RUTA_COPIADA> \
  -o data/raw/commoncrawl_news.warc.wet.gz
```

**Ejemplo completo:**
```bash
curl -L https://data.commoncrawl.org/crawl-data/CC-MAIN-2024-10/segments/1712296817038.34/wet/CC-MAIN-20240410123456-00000.warc.wet.gz \
  -o data/raw/commoncrawl_news.warc.wet.gz
```

### PASO 6: Verificar que el archivo es válido (⚠️ OBLIGATORIO)

Ejecuta:

```bash
gzip -t data/raw/commoncrawl_news.warc.wet.gz
```

✔ **Si NO muestra nada**, el archivo es correcto

❌ **Si muestra un error**, el archivo está corrupto y debes descargarlo nuevamente

### PASO 7: Confirmar que contiene texto real

```bash
gzip -dc data/raw/commoncrawl_news.warc.wet.gz | head -n 40
```

Debes ver algo como:

```
WARC/1.0
WARC-Type: warc
WARC-Date: 2024-02-20T21:11:02Z

This website uses cookies to ensure you get the best experience...
```

### PASO 8: Procesar los datos

Una vez que tengas el archivo WET, procesa los datos con el servicio de procesamiento:

```bash
# Construir la imagen Docker
docker build -t data-processing docker/data-processing

# Ejecutar el procesamiento
docker run --rm -v ${PWD}/data:/app/data data-processing
```

### PASO 9: Verificar el resultado

```bash
head data/processed/news.csv
```

Ahora DEBE verse algo así:

```csv
date,text
2024-02-20T21:11:02Z,this website uses cookies to ensure you get the best experience...
2024-02-20T21:11:05Z,breaking news from the financial markets today...
```

### PASO 10: Validar volumen (opcional pero recomendado)

```bash
wc -l data/processed/news.csv
```

✔ **Más de 10 líneas** → suficiente  
✔ **Más de 100** → excelente

---

