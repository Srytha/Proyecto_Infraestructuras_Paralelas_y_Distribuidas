# Imagen base
FROM python:3.9-slim

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Comando para iniciar
CMD ["python", "main.py"]
