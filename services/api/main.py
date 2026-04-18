import os
import asyncio
import logging
from datetime import datetime
from typing import Any

import clickhouse_connect
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CH_HOST  = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT  = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_DB    = os.getenv("CLICKHOUSE_DB", "skymap")
CH_USER  = os.getenv("CLICKHOUSE_USER", "skymap")
CH_PASS  = os.getenv("CLICKHOUSE_PASSWORD", "skymap123")

app = FastAPI(title="Skymap API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_ch():
    return clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT,
        database=CH_DB, username=CH_USER, password=CH_PASS
    )


def rows_to_dicts(result) -> list[dict]:
    cols = result.column_names
    return [dict(zip(cols, row)) for row in result.result_rows]


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/api/flights/live")
def flights_live(limit: int = Query(default=10000, le=20000)):
    """Devuelve el estado actual de todos los vuelos (tabla live)."""
    ch = get_ch()
    result = ch.query(f"""
        SELECT
            icao24, callsign, origin_country,
            longitude, latitude, baro_altitude,
            on_ground, velocity, true_track, vertical_rate,
            fetched_at
        FROM flights_live
        FINAL
        WHERE longitude != 0 AND latitude != 0
        LIMIT {limit}
    """)
    return {"count": len(result.result_rows), "flights": rows_to_dicts(result)}


@app.get("/api/stats/countries")
def stats_countries(limit: int = Query(default=20, le=100)):
    """Top países por número de vuelos en las últimas 2 horas."""
    ch = get_ch()
    result = ch.query(f"""
        SELECT origin_country, count() as vuelos
        FROM flights
        WHERE fetched_at >= now() - INTERVAL 2 HOUR
        GROUP BY origin_country
        ORDER BY vuelos DESC
        LIMIT {limit}
    """)
    return rows_to_dicts(result)


@app.get("/api/stats/summary")
def stats_summary():
    """Resumen global: totales, velocidad media, altitud media."""
    ch = get_ch()
    result = ch.query("""
        SELECT
            count()                              AS total_vuelos,
            countIf(on_ground = false)           AS en_vuelo,
            countIf(on_ground = true)            AS en_tierra,
            round(avg(velocity) * 3.6, 1)       AS vel_media_kmh,
            round(avg(baro_altitude), 0)         AS alt_media_m,
            round(max(velocity) * 3.6, 1)        AS vel_max_kmh,
            round(max(baro_altitude), 0)          AS alt_max_m
        FROM flights_live
        FINAL
        WHERE longitude != 0 AND latitude != 0
    """)
    return rows_to_dicts(result)[0]


@app.get("/api/flights/history/{icao24}")
def flight_history(icao24: str, hours: int = Query(default=2, le=24)):
    """Historial de posiciones de un vuelo concreto."""
    ch = get_ch()
    result = ch.query(f"""
        SELECT
            icao24, callsign, longitude, latitude,
            baro_altitude, velocity, true_track, fetched_at
        FROM flights
        WHERE icao24 = '{icao24}'
          AND fetched_at >= now() - INTERVAL {hours} HOUR
        ORDER BY fetched_at ASC
    """)
    return {"icao24": icao24, "points": rows_to_dicts(result)}


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        log.info("WebSocket conectado — clientes activos: %d", len(self.active))

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        log.info("WebSocket desconectado — clientes activos: %d", len(self.active))

    async def broadcast(self, data: Any):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


@app.websocket("/ws/flights")
async def ws_flights(websocket: WebSocket):
    """WebSocket que emite el estado live cada 10 segundos."""
    await manager.connect(websocket)
    try:
        while True:
            ch = get_ch()
            result = ch.query("""
                SELECT
                    icao24, callsign, origin_country,
                    longitude, latitude, baro_altitude,
                    on_ground, velocity, true_track, vertical_rate
                FROM flights_live
                FINAL
                WHERE longitude != 0 AND latitude != 0
                LIMIT 15000
            """)
            flights = rows_to_dicts(result)
            await websocket.send_json({
                "type": "flights_update",
                "count": len(flights),
                "timestamp": datetime.utcnow().isoformat(),
                "flights": flights,
            })
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        log.error("Error en WebSocket: %s", e)
        manager.disconnect(websocket)
