import os
import sys
from sqlalchemy import text

# Add the parent directory to sys.path so we can import from data.database
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data.database import get_postgis_db

def create_osm_cache():
    print("Starting OSM Cache table creation...")
    
    try:
        db = next(get_postgis_db())
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return
        
    try:
        # Create table for caching OSM API results
        print("Creating osm_geocoding_cache table...")
        db.execute(text("SET client_min_messages TO WARNING;"))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS osm_geocoding_cache (
                id SERIAL PRIMARY KEY,
                query_type VARCHAR(20) NOT NULL, -- 'forward' or 'reverse'
                query_key VARCHAR(255) NOT NULL, -- The search string or the coordinate
                result_wkt GEOMETRY(POINT, 4326), -- For forward geocoding
                result_text TEXT,                 -- For reverse geocoding
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes to speed up cache lookups
        print("Creating indexes on query_key...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_osm_cache_query_key ON osm_geocoding_cache (query_type, query_key);
        """))
        
        db.commit()
        print("OSM Cache table and indexes created successfully!")
        
    except Exception as e:
        print(f"Table creation failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_osm_cache()
