FROM python:3.9-slim

WORKDIR /app

# Copiar solo dependencias primero (cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar solo el código necesario
COPY main.py .
COPY worker.py .

CMD ["python", "main.py"]
