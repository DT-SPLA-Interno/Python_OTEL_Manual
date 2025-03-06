# Servicios Instrumentados Manual y Automatico Python

## Descripción

Este proyecto implementa una arquitectura de tres servicios que incluye:
- **user_interface**: Servicio de interfaz de usuario construido en Python con instrumentación automática.
- **api-inventario**: Servicio API de inventario construido en Python con instrumentación manual.
- **mysql-db**: Servicio de base de datos MySQL.

## user_interface
### Instrumentación Automática

Este proyecto utiliza OpenTelemetry para la instrumentación automática de los servicios. A continuación se describe cómo se configura y utiliza esta instrumentación:

#### Enriquecimiento con Dynatrace

El código lee archivos de metadatos de Dynatrace (`dt_metadata.json`) para enriquecer los atributos de los rastros (traces) con información específica del servicio, como el nombre y la versión de la aplicación.

#### Configuración de OpenTelemetry

Se configura OpenTelemetry con un `TracerProvider` y un exportador OTLP (`OTLPSpanExporter`). El exportador envía los rastros al colector de Dynatrace. Se crea un `BatchSpanProcessor` para procesar y exportar los rastros de manera eficiente.

#### Instrumentación de FastAPI y Requests

Se instrumenta la aplicación FastAPI y las solicitudes HTTP (Requests) para capturar automáticamente los rastros de las operaciones realizadas por estos componentes.

## api-inventario

### Enriquecimiento con Dynatrace

El código lee archivos de metadatos de Dynatrace (`dt_metadata.json`) para enriquecer los atributos de los rastros (traces) con información específica del servicio, como el nombre y la versión de la aplicación.

### Configuración de OpenTelemetry

Se configura OpenTelemetry con un `TracerProvider` y un exportador OTLP (`OTLPSpanExporter`). El exportador envía los rastros al colector de Dynatrace. Se crea un `BatchSpanProcessor` para procesar y exportar los rastros de manera eficiente.

### Obtener la Traza

Se obtiene un tracer de OpenTelemetry para el servicio `api-inventario` utilizando `trace.get_tracer_provider().get_tracer("api-inventario")`.

### Endpoints de FastAPI

Se definen varios endpoints en FastAPI para interactuar con el servicio de API de inventario. Los endpoints incluyen:
- `POST /items/add`: Agrega un ítem al inventario. Se inicia un span para rastrear la operación y se extrae el contexto de trazas de los encabezados HTTP.
- `GET /items/all`: Retorna todos los ítems del inventario. Se inicia un span para rastrear la operación, se extrae el contexto de trazas de los encabezados HTTP y se define un span hijo para la consulta a la base de datos.
