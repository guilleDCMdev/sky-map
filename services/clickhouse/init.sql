CREATE DATABASE IF NOT EXISTS skymap;

CREATE TABLE IF NOT EXISTS skymap.flights (
    icao24          String,
    callsign        String,
    origin_country  String,
    longitude       Float64,
    latitude        Float64,
    baro_altitude   Float64,
    geo_altitude    Float64,
    on_ground       Bool,
    velocity        Float64,
    true_track      Float64,
    vertical_rate   Float64,
    fetched_at      DateTime,
    inserted_at     DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(fetched_at)
ORDER BY (fetched_at, icao24)
TTL fetched_at + INTERVAL 7 DAY;

CREATE TABLE IF NOT EXISTS skymap.flights_live (
    icao24          String,
    callsign        String,
    origin_country  String,
    longitude       Float64,
    latitude        Float64,
    baro_altitude   Float64,
    on_ground       Bool,
    velocity        Float64,
    true_track      Float64,
    vertical_rate   Float64,
    fetched_at      DateTime
)
ENGINE = ReplacingMergeTree(fetched_at)
ORDER BY icao24;
