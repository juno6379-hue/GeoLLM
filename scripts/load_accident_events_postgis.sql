-- Load standardized accident events into PostGIS.
-- Run with psql after copying accident_events_coastguard_2025.csv to /tmp.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS serving;

CREATE TABLE IF NOT EXISTS serving.accident_events (
    event_id text PRIMARY KEY,
    source_row_number integer NOT NULL,
    occurred_at timestamp,
    month integer,
    time_slot integer,
    authority text,
    sea_area text,
    latitude double precision,
    longitude double precision,
    source_latitude_dms text,
    source_longitude_dms text,
    geocode_status text NOT NULL,
    crs text NOT NULL DEFAULT 'EPSG:4326',
    weather text,
    cause text,
    accident_type text,
    vessel_count integer,
    people_count integer,
    rescued integer,
    injured integer,
    dead integer,
    missing integer,
    vessel_type text,
    tonnage double precision,
    geom geometry(Point, 4326),
    standardized_at timestamptz NOT NULL DEFAULT now()
);

CREATE TEMP TABLE accident_events_load (
    event_id text,
    source_row_number integer,
    occurred_at timestamp,
    month integer,
    time_slot integer,
    authority text,
    sea_area text,
    latitude double precision,
    longitude double precision,
    source_latitude_dms text,
    source_longitude_dms text,
    geocode_status text,
    crs text,
    weather text,
    cause text,
    accident_type text,
    vessel_count integer,
    people_count integer,
    rescued integer,
    injured integer,
    dead integer,
    missing integer,
    vessel_type text,
    tonnage double precision
);

\copy accident_events_load FROM '/tmp/accident_events_coastguard_2025.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

INSERT INTO serving.accident_events (
    event_id, source_row_number, occurred_at, month, time_slot, authority,
    sea_area, latitude, longitude, source_latitude_dms, source_longitude_dms,
    geocode_status, crs, weather, cause, accident_type, vessel_count,
    people_count, rescued, injured, dead, missing, vessel_type, tonnage, geom,
    standardized_at
)
SELECT event_id,
       source_row_number,
       occurred_at,
       month,
       time_slot,
       authority,
       sea_area,
       latitude,
       longitude,
       source_latitude_dms,
       source_longitude_dms,
       geocode_status,
       COALESCE(NULLIF(crs, ''), 'EPSG:4326'),
       weather,
       cause,
       accident_type,
       vessel_count,
       people_count,
       rescued,
       injured,
       dead,
       missing,
       vessel_type,
       tonnage,
       CASE
           WHEN geocode_status = 'GEOCODED_FROM_SOURCE_DMS'
            AND latitude BETWEEN -90 AND 90
            AND longitude BETWEEN -180 AND 180
           THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
           ELSE NULL
       END,
       now()
FROM accident_events_load
ON CONFLICT (event_id) DO UPDATE SET
    source_row_number = EXCLUDED.source_row_number,
    occurred_at = EXCLUDED.occurred_at,
    month = EXCLUDED.month,
    time_slot = EXCLUDED.time_slot,
    authority = EXCLUDED.authority,
    sea_area = EXCLUDED.sea_area,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    source_latitude_dms = EXCLUDED.source_latitude_dms,
    source_longitude_dms = EXCLUDED.source_longitude_dms,
    geocode_status = EXCLUDED.geocode_status,
    crs = EXCLUDED.crs,
    weather = EXCLUDED.weather,
    cause = EXCLUDED.cause,
    accident_type = EXCLUDED.accident_type,
    vessel_count = EXCLUDED.vessel_count,
    people_count = EXCLUDED.people_count,
    rescued = EXCLUDED.rescued,
    injured = EXCLUDED.injured,
    dead = EXCLUDED.dead,
    missing = EXCLUDED.missing,
    vessel_type = EXCLUDED.vessel_type,
    tonnage = EXCLUDED.tonnage,
    geom = EXCLUDED.geom,
    standardized_at = EXCLUDED.standardized_at;

CREATE INDEX IF NOT EXISTS idx_accident_events_geom
    ON serving.accident_events
    USING gist (geom)
    WHERE geom IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_accident_events_geography
    ON serving.accident_events
    USING gist ((geom::geography))
    WHERE geom IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_accident_events_occurred_at
    ON serving.accident_events (occurred_at);

CREATE INDEX IF NOT EXISTS idx_accident_events_type
    ON serving.accident_events (accident_type);

CREATE INDEX IF NOT EXISTS idx_accident_events_authority
    ON serving.accident_events (authority);

ANALYZE serving.accident_events;
