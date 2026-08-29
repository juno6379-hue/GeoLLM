import uuid
from sqlalchemy import Column, String, JSON, DateTime, Integer
from geoalchemy2 import Geometry
from .base import Base
from datetime import datetime

class AgentRegistry(Base):
    __tablename__ = 'agent_registry'

    agent_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    version = Column(String, nullable=False)
    endpoint = Column(String, nullable=True)
    health_status = Column(String, nullable=False, default="HEALTHY")
    created_at = Column(DateTime, default=datetime.utcnow)

class ToolRegistry(Base):
    __tablename__ = 'tool_registry'

    tool_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    version = Column(String, nullable=False)
    input_schema = Column(JSON, nullable=False)
    output_schema = Column(JSON, nullable=False)
    security_scope = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelRegistry(Base):
    __tablename__ = 'model_registry'

    model_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatasetCatalog(Base):
    __tablename__ = 'dataset_catalog'

    dataset_id = Column(String, primary_key=True)
    logical_name = Column(String, nullable=False)
    physical_location = Column(String, nullable=False)
    spatial_extent = Column(Geometry('POLYGON', srid=4326), nullable=True)
    # Using String for temporal extent simply for MVP instead of PostgreSQL specific Tstzrange
    temporal_extent_start = Column(DateTime, nullable=True)
    temporal_extent_end = Column(DateTime, nullable=True)
    security_level = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
