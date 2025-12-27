FROM python:3.9-slim

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 pandas numpy

# Copiar TODO el código del servicio
COPY . .

CMD ["python", "analysis.py"]
