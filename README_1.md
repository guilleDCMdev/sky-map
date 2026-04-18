# ✈️ Skymap

Mapa global de vuelos en tiempo real. Más de 11.000 vuelos activos visualizados sobre un globo 3D interactivo, con pipeline de datos completo desde la ingesta hasta el frontend.

![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat&logo=apachekafka&logoColor=white)
![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?style=flat&logo=clickhouse&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

## Demo

- Globo 3D interactivo con todos los vuelos en tiempo real
- Click en cualquier avión para ver sus datos e historial de posiciones
- Estadísticas globales: velocidad media, altitud, vuelos por país
- Actualización automática cada 10 segundos vía WebSocket

## Arquitectura

```
OpenSky Network API
        ↓
   Python Fetcher        → cada 10s descarga ~11.000 vuelos
        ↓
     Apache Kafka        → topic: raw_flights
        ↓
  Python Processor       → consume, limpia e inserta en lotes
        ↓
    ClickHouse           → serie temporal + estado live
        ↓
  FastAPI + WebSocket    → REST API + stream en tiempo real
        ↓
  React + Globe.gl       → globo 3D WebGL en el navegador
```

## Stack

| Capa | Tecnología |
|---|---|
| Ingesta | Python + requests |
| Mensajería | Apache Kafka + Zookeeper |
| Almacenamiento | ClickHouse (MergeTree + ReplacingMergeTree) |
| Backend | FastAPI + WebSockets |
| Frontend | React + Vite + Globe.gl |
| Infraestructura | Docker Compose |
| Monitorización Kafka | Kafdrop |

## Requisitos

- Docker Desktop
- Node.js 18+
- npm 9+

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/skymap.git
cd skymap

# 2. Levantar el backend completo
docker compose up

# 3. En otra terminal, arrancar el frontend
cd frontend
npm install
npm run dev
```

## URLs

| Servicio | URL |
|---|---|
| 🌍 Globo 3D | http://localhost:3000 |
| 📡 API REST | http://localhost:8000/docs |
| 📊 Kafdrop (Kafka UI) | http://localhost:9000 |

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | /api/flights/live | Estado actual de todos los vuelos |
| GET | /api/stats/summary | Estadísticas globales |
| GET | /api/stats/countries | Top países por tráfico |
| GET | /api/flights/history/{id} | Historial de posiciones de un vuelo |
| WS | /ws/flights | Stream en tiempo real |

## Estructura del proyecto

```
skymap/
├── docker-compose.yml
├── services/
│   ├── fetcher/          # Descarga datos de OpenSky
│   ├── processor/        # Consume Kafka e inserta en ClickHouse
│   ├── api/              # FastAPI REST + WebSocket
│   └── clickhouse/       # Schema SQL inicial
└── frontend/             # React + Globe.gl
```

## Datos

Los datos provienen de [OpenSky Network](https://opensky-network.org/), una red colaborativa y gratuita de receptores ADS-B. Se actualizan cada 10 segundos e incluyen posición, altitud, velocidad, rumbo y país de origen de cada aeronave.

## Licencia

MIT
