import json
import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
import mysql.connector
import uvicorn
import time
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import extract
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.trace import set_tracer_provider, get_tracer_provider, Status, StatusCode, SpanKind
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

app = FastAPI(title="API Inventario", version="1.0.0")
# ------------------------------------------------------------------------------
# 1. Enriquecimiento con Dynatrace
# ------------------------------------------------------------------------------
enrich_attrs = {}
dt_metadata_files = [
    "dt_metadata.json",
    "/var/lib/dynatrace/enrichment/dt_metadata.json"
]

for file_path in dt_metadata_files:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                enrich_attrs.update(data)
        except Exception as e:
            print(f"Error leyendo archivo de metadatos Dynatrace: {e}")



enrich_attrs.update({
  "service.name": "api-inventario", #TODO Replace with the name of your application
  "service.version": "1.0.0", #TODO Replace with the version of your application
})

resource = Resource.create(enrich_attrs)

# ------------------------------------------------------------------------------
# 2. Configurar OpenTelemetry
# ------------------------------------------------------------------------------
tracer_provider = TracerProvider(resource=resource)
#set_tracer_provider(tracer_provider)
trace.set_tracer_provider(tracer_provider)

otlp_exporter = OTLPSpanExporter(
    endpoint="http://collector:4318/v1/traces" 
)

span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)


# ------------------------------------------------------------------------------
# 3. Funciones de conexión MySQL
# ------------------------------------------------------------------------------
def get_db_connection():
    """
    Retorna la conexión a la base de datos MySQL del inventario.
    Ajusta parámetros si es necesario (host, user, password, database).
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "BASE DE DATOS"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "######"),
        database=os.getenv("DB_DATABASE", "inventario")
    )
  
# ------------------------------------------------------------------------------
# 4. Obtener la traza
# ------------------------------------------------------------------------------

tracer = trace.get_tracer_provider().get_tracer("api-inventario")

# ------------------------------------------------------------------------------
# 5. Endpoints
# ------------------------------------------------------------------------------

@app.post("/items/add")
def add_item(request: Request, data: Dict[str, Any]):
    """
    Agrega un ítem al inventario: { "name": "...", "quantity": ... }

    Iniciamos un span
    """
    # Extraer el contexto de trazas de los encabezados HTTP
    context = extract(request.headers)
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("Post /items/add", context=context) as span:
        name = data.get("name")
        quantity = data.get("quantity")

        if not name or quantity is None:
            raise HTTPException(status_code=400, detail="Datos inválidos para agregar item")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items (name, quantity) VALUES (%s, %s)", (name, quantity))
            span.set_attribute("BIND", "INSERT INTO items (name, quantity) VALUES (, )")
            span.set_attribute("ITEM", name)
            span.set_attribute("QUANTITY", quantity)
            conn.commit()
            cursor.close()
            conn.close()
            span.add_event(f"Item {name} agregado con cantidad {quantity}")
            return {"message": f"Item '{name}' agregado con cantidad {quantity}"}
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
            raise HTTPException(status_code=500, detail="Error interno al agregar item")

@app.get("/items/all")
def get_all_items(request: Request):
    """
    Retorna todos los ítems del inventario.

    Iniciamos un span
    """
    # Extraer el contexto de trazas de los encabezados HTTP
    context = extract(request.headers)
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("Get /items/all", context=context) as span:
        # ------------------------------------------------------------------------------
        # Definimos un span child
        # ------------------------------------------------------------------------------
        time.sleep(1)
        with tracer.start_as_current_span("Consulta DB") as child:
            try:
                
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                current_span = trace.get_current_span()

                
                cursor.execute("SELECT id, name, quantity FROM items")
                child.set_attribute("BIND", "SELECT id, name, quantity FROM items")
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return rows
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                raise HTTPException(status_code=500, detail="Error al obtener los ítems del inventario")

# ------------------------------------------------------------------------------
# 5. Ejecución con Uvicorn (para desarrollo local)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
