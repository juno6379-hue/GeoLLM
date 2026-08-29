-- ==========================================
-- An_GeoLLM PostGIS Initialization Script
-- ==========================================

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Schemas
CREATE SCHEMA IF NOT EXISTS ocean_data;
CREATE SCHEMA IF NOT EXISTS system_auth;
CREATE SCHEMA IF NOT EXISTS audit;

-- ==========================================
-- 3. System Auth & Roles
-- ==========================================
CREATE TABLE system_auth.roles (
    role_id VARCHAR(50) PRIMARY KEY,
    description TEXT
);

CREATE TABLE system_auth.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    organization_id VARCHAR(100) NOT NULL,
    role_id VARCHAR(50) REFERENCES system_auth.roles(role_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO system_auth.roles (role_id, description) VALUES 
('PUBLIC', 'General Public Access'),
('NAVY', 'Navy / Military Restricted Access'),
('ADMIN', 'System Administrator');

INSERT INTO system_auth.users (username, organization_id, role_id) VALUES 
('test-user-1', 'navy', 'NAVY');

-- ==========================================
-- 4. Audit & Metadata
-- ==========================================
CREATE TABLE audit.access_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES system_auth.users(user_id),
    query_intent VARCHAR(255),
    accessed_tables TEXT[],
    execution_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ocean_data.dataset_metadata (
    dataset_id VARCHAR(100) PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    reference_time TIMESTAMP WITH TIME ZONE NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 5. Ocean Data (ENC Replaceable Architecture)
-- ==========================================

-- 5.1 ENC Features (Physical Table)
CREATE TABLE ocean_data.enc_features_v1 (
    feature_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_type VARCHAR(100) NOT NULL, -- e.g., 'WRECKS', 'RESTRN'
    properties JSONB DEFAULT '{}'::jsonb,
    geom geometry(Geometry, 4326)
);

CREATE INDEX idx_enc_features_v1_geom ON ocean_data.enc_features_v1 USING GIST (geom);

-- 5.2 ENC Features (View Routing for Application)
CREATE VIEW ocean_data.v_enc_features AS 
SELECT * FROM ocean_data.enc_features_v1;

-- 5.3 AIS Tracking (Partitioned by Range on Timestamp)
CREATE TABLE ocean_data.ais_tracking (
    mmsi VARCHAR(20) NOT NULL,
    ship_name VARCHAR(255),
    ship_type VARCHAR(100),
    speed_over_ground FLOAT,
    course_over_ground FLOAT,
    nav_status VARCHAR(50),
    geom geometry(Point, 4326),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
) PARTITION BY RANGE (timestamp);

CREATE INDEX idx_ais_tracking_geom ON ocean_data.ais_tracking USING GIST (geom);
CREATE INDEX idx_ais_tracking_time ON ocean_data.ais_tracking (timestamp);

-- Create initial partitions (Example: 2026-07)
CREATE TABLE ocean_data.ais_tracking_2026_07 PARTITION OF ocean_data.ais_tracking
    FOR VALUES FROM ('2026-07-01 00:00:00+09') TO ('2026-08-01 00:00:00+09');

-- ==========================================
-- 6. Sample Data Insertion
-- ==========================================
INSERT INTO ocean_data.dataset_metadata (dataset_id, version, reference_time, description)
VALUES ('ENC_KOREA', 'v1.0.0', '2026-07-01 00:00:00+09', 'Korea ENC Vector Base');

-- Sample Wreck (위험객체) in Busan
INSERT INTO ocean_data.enc_features_v1 (feature_type, properties, geom)
VALUES (
    'WRECKS', 
    '{"name": "Sunken Ship A", "depth": -15.5}', 
    ST_SetSRID(ST_MakePoint(129.07, 35.09), 4326)
);

-- Sample Restricted Zone (위험구역)
INSERT INTO ocean_data.enc_features_v1 (feature_type, properties, geom)
VALUES (
    'RESTRN', 
    '{"name": "Naval Firing Range", "restriction": "No Entry"}', 
    ST_SetSRID(ST_GeomFromText('POLYGON((129.05 35.10, 129.10 35.10, 129.10 35.05, 129.05 35.05, 129.05 35.10))'), 4326)
);
