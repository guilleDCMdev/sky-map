import os
import json
import time
import logging
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import clickhouse_connect

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

KAFKA_SERVERS  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC    = os.getenv("KAFKA_TOPIC", "raw_flights")
KAFKA_GROUP    = os.getenv("KAFKA_GROUP_ID", "processor-group")
CH_HOST        = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT        = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_DB          = os.getenv("CLICKHOUSE_DB", "skymap")
CH_USER        = os.getenv("CLICKHOUSE_USER", "skymap")
CH_PASS        = os.getenv("CLICKHOUSE_PASSWORD", "skymap123")
BATCH_SIZE     = int(os.getenv("BATCH_SIZE", "500"))


def build_consumer() -> KafkaConsumer:
    for attempt in range(1, 11):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_SERVERS,
                group_id=KAFKA_GROUP,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
                consumer_timeout_ms=5000,
            )
            log.info("Consumer conectado a Kafka")
            return consumer
        except NoBrokersAvailable:
            log.warning("Kafka no disponible, reintento %d/10 en 5s...", attempt)
            time.sleep(5)
    raise RuntimeError("No se pudo conectar a Kafka")


def build_clickhouse():
    for attempt in range(1, 11):
        try:
            client = clickhouse_connect.get_client(
                host=CH_HOST, port=CH_PORT,
                database=CH_DB, username=CH_USER, password=CH_PASS
            )
            client.ping()
            log.info("Conectado a ClickHouse en %s:%d", CH_HOST, CH_PORT)
            return client
        except Exception as e:
            log.warning("ClickHouse no disponible, reintento %d/10: %s", attempt, e)
            time.sleep(5)
    raise RuntimeError("No se pudo conectar a ClickHouse")


def parse_flight(raw: dict) -> list | None:
    try:
        fetched_at = datetime.fromisoformat(raw.get("fetched_at", datetime.utcnow().isoformat()))
        return [
            str(raw.get("icao24") or ""),
            str(raw.get("callsign") or "").strip(),
            str(raw.get("origin_country") or ""),
            float(raw.get("longitude") or 0),
            float(raw.get("latitude") or 0),
            float(raw.get("baro_altitude") or 0),
            float(raw.get("geo_altitude") or 0),
            bool(raw.get("on_ground", False)),
            float(raw.get("velocity") or 0),
            float(raw.get("true_track") or 0),
            float(raw.get("vertical_rate") or 0),
            fetched_at,
        ]
    except Exception as e:
        log.debug("Error parseando vuelo: %s", e)
        return None


def insert_batch(ch_client, batch: list[list]) -> None:
    cols = [
        "icao24", "callsign", "origin_country",
        "longitude", "latitude", "baro_altitude", "geo_altitude",
        "on_ground", "velocity", "true_track", "vertical_rate", "fetched_at"
    ]
    ch_client.insert("flights", batch, column_names=cols)

    live_cols = [
        "icao24", "callsign", "origin_country",
        "longitude", "latitude", "baro_altitude",
        "on_ground", "velocity", "true_track", "vertical_rate", "fetched_at"
    ]
    live_batch = [[r[0],r[1],r[2],r[3],r[4],r[5],r[7],r[8],r[9],r[10],r[11]] for r in batch]
    ch_client.insert("flights_live", live_batch, column_names=live_cols)


def main():
    log.info("Skymap Processor arrancando -- batch size: %d", BATCH_SIZE)
    consumer   = build_consumer()
    ch_client  = build_clickhouse()
    batch      = []
    total      = 0

    while True:
        try:
            for msg in consumer:
                row = parse_flight(msg.value)
                if row:
                    batch.append(row)

                if len(batch) >= BATCH_SIZE:
                    insert_batch(ch_client, batch)
                    total += len(batch)
                    log.info("Insertados %d filas (total acumulado: %d)", len(batch), total)
                    batch = []

        except Exception as e:
            log.error("Error en el loop principal: %s", e)
            if batch:
                try:
                    insert_batch(ch_client, batch)
                    total += len(batch)
                    batch = []
                except Exception:
                    pass
            time.sleep(3)


if __name__ == "__main__":
    main()
