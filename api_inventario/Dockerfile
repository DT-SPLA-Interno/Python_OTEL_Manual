# Usa una imagen base de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo main.py
COPY main.py /app/

# Instala dependencias
RUN pip install --no-cache-dir fastapi uvicorn \
    mysql-connector-python \
    opentelemetry-sdk \
    opentelemetry-api \
    opentelemetry-exporter-otlp \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-mysql 

# Exponer el puerto 8001
EXPOSE 8001

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]