import json
import requests
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import set_tracer_provider
import uvicorn
import os

app = FastAPI(title="User Interface Microservice", version="1.0.0")

# ------------------------------------------------------------------------------
# 1. Enriquecimiento con Dynatrace (lectura de dt_metadata.json)
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
  "service.name": "user_interface", #TODO Replace with the name of your application
  "service.version": "1.5.0", #TODO Replace with the version of your application
})


resource = Resource.create(enrich_attrs)

# ------------------------------------------------------------------------------
# 2. Configurar OpenTelemetry con el TracerProvider y Exportador OTLP
#    Asegurarse de que el endpoint de OTLP apunte al Dynatrace Collector
# ------------------------------------------------------------------------------
tracer_provider = TracerProvider(resource=resource)
set_tracer_provider(tracer_provider)

otlp_exporter = OTLPSpanExporter(
    # Reemplaza "dynatrace-collector.dynatrace:4318" con la ruta/host real de tu Collector
    endpoint="http://Collector:4318/v1/traces" # Collector
)

span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Instrumentar FastAPI y Requests
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

# ------------------------------------------------------------------------------
# 3. Endpoints FastAPI
# ------------------------------------------------------------------------------
@app.get("/")
def read_root():
    """
    Endpoint raíz que confirma que el microservicio UI está funcionando.
    """
    return {"message": "Bienvenido al User Interface Microservice"}

@app.post("/add_item/")
def add_item(name: str, quantity: int):
    """
    Endpoint para agregar un item al inventario a través de la API de Inventario.
    """
    # Llamamos a la API de Inventario para agregar el item
    response = requests.post(
        "http://localhost:8001/items/add",
        json={"name": name, "quantity": quantity}
    )
    if response.status_code == 200:
        return {"message": "Item agregado correctamente", "data": response.json()}
    else:
        return {"error": "No se pudo agregar el item", "status": response.status_code}

@app.get("/items/")
def get_items():
    """
    Endpoint para obtener todos los items del inventario a través de la API de Inventario.
    """
    response = requests.get("http://localhost:8001/items/all")
    if response.status_code == 200:
        return {"items": response.json()}
    else:
        return {"error": "No se pudo obtener la lista de items", "status": response.status_code}

# ------------------------------------------------------------------------------
# 4. Ejecución con Uvicorn (opcional, en caso de correrlo localmente)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)