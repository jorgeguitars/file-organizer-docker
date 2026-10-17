FROM python:3.11-slim

WORKDIR /app

# Copiamos e instalamos las dependencias desde requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente
COPY main.py .

# Creamos el directorio target
RUN mkdir -p /app/target

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]