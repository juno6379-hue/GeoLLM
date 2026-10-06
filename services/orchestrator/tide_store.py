"""Persistent KHOA response snapshots and station/time observation history."""
import json
import os
import uuid
from functools import lru_cache
from sqlalchemy import create_engine, text


@lru_cache(maxsize=1)
def engine():
    return create_engine(os.environ['S101_DB_URL'], pool_pre_ping=True)


def initialize():
    with engine().begin() as conn:
        conn.execute(text('CREATE SCHEMA IF NOT EXISTS serving'))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS serving.khoa_tide_fetches (
            fetch_id uuid PRIMARY KEY, station_code text NOT NULL, requested_date text NOT NULL,
            fetched_at timestamptz NOT NULL, source_url text NOT NULL, payload jsonb NOT NULL)'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS serving.khoa_tide_observations (
            fetch_id uuid NOT NULL REFERENCES serving.khoa_tide_fetches(fetch_id),
            row_no integer NOT NULL, station_code text NOT NULL, station_name text,
            observed_at text, observed_level double precision, predicted_level double precision,
            latitude double precision, longitude double precision,
            PRIMARY KEY(fetch_id,row_no))'''))
        conn.execute(text('''CREATE INDEX IF NOT EXISTS khoa_tide_station_time
            ON serving.khoa_tide_observations(station_code, observed_at)'''))
        conn.execute(text('''CREATE INDEX IF NOT EXISTS khoa_tide_fetch_station_date
            ON serving.khoa_tide_fetches(station_code, requested_date, fetched_at DESC)'''))


def save(result):
    fetch_id = str(uuid.uuid4())
    with engine().begin() as conn:
        conn.execute(text('''INSERT INTO serving.khoa_tide_fetches
            VALUES (CAST(:id AS uuid),:station,:date,:fetched,:source,CAST(:payload AS jsonb))'''),
            dict(id=fetch_id, station=result['station_code'], date=result['requested_date'],
                 fetched=result['fetched_at'], source=result['source'],
                 payload=json.dumps(result, ensure_ascii=False)))
        for index, row in enumerate(result['rows']):
            conn.execute(text('''INSERT INTO serving.khoa_tide_observations VALUES
                (CAST(:id AS uuid),:n,:station,:station_name,:observed_at,:observed_level,
                 :predicted_level,:latitude,:longitude)'''),
                dict(id=fetch_id,n=index,station=result['station_code'],**row))
    return dict(status='STORED', fetch_id=fetch_id, rows=len(result['rows']),
                database='gbhd_s101', table='serving.khoa_tide_observations')


def history(station, date, limit):
    with engine().connect() as conn:
        rows = conn.execute(text('''SELECT o.*, f.fetched_at, f.source_url
            FROM serving.khoa_tide_observations o JOIN serving.khoa_tide_fetches f USING(fetch_id)
            WHERE o.station_code=:station AND f.requested_date=:date
            ORDER BY f.fetched_at DESC, o.row_no LIMIT :limit'''),
            dict(station=station,date=date,limit=limit)).mappings().all()
    return [dict(row) for row in rows]
