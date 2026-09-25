"""Create the LiDAR registry schema without inserting demonstration records.

Run: python -m scripts.initialize_lidar_registry
Existing tables are preserved; schema migrations remain explicit operations.
"""
import os
from sqlalchemy import create_engine, inspect
from data.models.lidar_dataset import LiDARDataset


def initialize():
    url = os.environ.get("POSTGIS_URL")
    if not url:
        raise RuntimeError("POSTGIS_URL is required")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        LiDARDataset.__table__.create(engine, checkfirst=True)
        actual = {column["name"] for column in inspect(engine).get_columns("lidar_datasets")}
        missing = set(LiDARDataset.__table__.columns.keys()) - actual
        if missing:
            raise RuntimeError("LiDAR registry migration required: " + ", ".join(sorted(missing)))
        print("LiDAR registry schema ready; no sample records inserted.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    initialize()
