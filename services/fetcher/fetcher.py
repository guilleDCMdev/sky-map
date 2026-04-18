import os
import json
import time
import logging
import requests
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC        = os.getenv("KAFKA_TOPIC", "raw_flights")
INTERVAL     = int(os.getenv("FETCH_INTERVAL_SECONDS", "10"))
OPENSKY_URL  = "https://opensky-network.org/api/states/all"

FIELDS = [
    "icao24", "callsign", "origin_country", "time_position",
    "last_contact", "longitude", "latitude", "baro_altitude",
    "on_ground", "velocity", "true_track", "vertical_rate",
    "sensors", "geo_altitude", "squawk", "spi", "position_source"
]


def build_producer() -> KafkaProducer:
    """Intenta conectar a Kafka con reintentos."""
    for attempt in range(1, 11):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
            )
            log.info("Conectado a Kafka en %s", KAFKA_SERVERS)
            return producer
        except NoBrokersAvailable:
            log.warning("Kafka no disponible, reintento %d/10 en 5s...", attempt)
            time.sleep(5)
    raise RuntimeError("No se pudo conectar a Kafka tras 10 intentos")


def fetch_flights() -> list[dict]:
    """Descarga el estado actual de todos los vuelos de OpenSky."""
    try:
        resp = requests.get(OPENSKY_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        states = data.get("states") or []

        flights = []
        for state in states:
            # Filtrar vuelos sin coordenadas
            if state[5] is None or state[6] is None:
                continue
            flight = dict(zip(FIELDS, state))
            flight["fetched_at"] = datetime.utcnow().isoformat()
            flights.append(flight)

        log.info("Vuelos recibidos: %d (con coordenadas válidas)", len(flights))
        return flights

    except requests.RequestException as e:
        log.error("Error al llamar a OpenSky: %s", e)
        return []


def publish(producer: KafkaProducer, flights: list[dict]) -> None:
    """Publica cada vuelo como mensaje individual en Kafka."""
    for flight in flights:
        producer.send(TOPIC, value=flight)
    producer.flush()
    log.info("Publicados %d mensajes en topic '%s'", len(flights), TOPIC)


def main():
    log.info("Skymap Fetcher arrancando — intervalo: %ds", INTERVAL)
    producer = build_producer()

    while True:
        start = time.time()
        flights = fetch_flights()
        if flights:
            publish(producer, flights)
        elapsed = time.time() - start
        sleep_time = max(0, INTERVAL - elapsed)
        log.info("Ciclo completado en %.1fs, esperando %.1fs", elapsed, sleep_time)
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
