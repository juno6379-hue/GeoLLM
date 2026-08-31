import os
from dotenv import load_dotenv
load_dotenv()
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from shared.observability.logger import get_logger

logger = get_logger("data.database")

# 1. PostGIS 연결 설정
POSTGIS_URL = os.environ.get(
    "POSTGIS_URL", 
    "postgresql://postgres:postgres@localhost:5432/marine_geo?client_encoding=utf8"
)
postgis_engine = None
PostgisSessionLocal = None

# 2. Oracle (MDC DB) 연결 설정
ORACLE_URL = os.environ.get(
    "ORACLE_URL",
    ""
)
oracle_engine = None
OracleSessionLocal = None

# 3. GBENC (S-100/S-101 ENC DB) 연결 설정
def get_gbenc_url():
    host = os.environ.get("GBENC_DB_HOST", "")
    port = os.environ.get("GBENC_DB_PORT", "39101")
    name = os.environ.get("GBENC_DB_NAME", "gbenc")
    user = os.environ.get("GBENC_DB_USER", "postgres")
    password = os.environ.get("GBENC_DB_PASSWORD", "")
    # 특수문자 안전하게 인코딩 처리
    encoded_pw = quote_plus(password)
    return f"postgresql://{user}:{encoded_pw}@{host}:{port}/{name}"

GBENC_URL = get_gbenc_url()
enc_engine = None
EncSessionLocal = None

# S-101 v2 projection database. Credentials are supplied only through the
# runtime environment; no local password is embedded in the application.
S101_URL = os.environ.get("S101_DB_URL")
s101_engine = None
S101SessionLocal = None

Base = declarative_base()

def init_engines():
    global postgis_engine, PostgisSessionLocal
    global oracle_engine, OracleSessionLocal
    global enc_engine, EncSessionLocal
    global s101_engine, S101SessionLocal
    
    if postgis_engine is None:
        try:
            postgis_engine = create_engine(POSTGIS_URL, pool_pre_ping=True)
            PostgisSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgis_engine)
            logger.info("PostGIS engine initialized")
        except Exception as e:
            logger.error("Failed to initialize PostGIS engine", error=str(e))
            
    if oracle_engine is None and ORACLE_URL:
        try:
            oracle_engine = create_engine(ORACLE_URL, pool_pre_ping=True)
            OracleSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=oracle_engine)
            logger.info("Oracle engine initialized")
        except Exception as e:
            logger.error("Failed to initialize Oracle engine", error=str(e))
            
    if enc_engine is None:
        try:
            enc_engine = create_engine(GBENC_URL, pool_pre_ping=True)
            EncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=enc_engine)
            logger.info("GBENC engine initialized")
        except Exception as e:
            logger.error("Failed to initialize GBENC engine", error=str(e))

    if s101_engine is None and S101_URL:
        try:
            s101_engine = create_engine(S101_URL, pool_pre_ping=True)
            S101SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=s101_engine)
            logger.info("S-101 v2 engine initialized")
        except Exception as e:
            logger.error("Failed to initialize S-101 v2 engine", error=str(e))

def get_postgis_db():
    init_engines()
    if PostgisSessionLocal is None:
        yield None
        return
    db = PostgisSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_oracle_db():
    init_engines()
    if OracleSessionLocal is None:
        yield None
        return
    db = OracleSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_enc_db():
    init_engines()
    if EncSessionLocal is None:
        yield None
        return
    db = EncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_s101_db():
    """Yield the configured S-101 v2 database session."""
    init_engines()
    if S101SessionLocal is None:
        yield None
        return
    db = S101SessionLocal()
    try:
        yield db
    finally:
        db.close()
