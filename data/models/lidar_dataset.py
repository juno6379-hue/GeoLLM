from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, func
from data.models.base import Base
import datetime

class LiDARDataset(Base):
    __tablename__ = 'lidar_datasets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(50), unique=True, index=True, nullable=False) # e.g. DS-2026-000001
    
    # Basic Info
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False) # MinIO or local path
    file_type = Column(String(20), nullable=False) # LAS, LAZ, TIF, etc.
    file_size_bytes = Column(Integer, nullable=True)
    
    # Metadata
    acquisition_date = Column(DateTime, nullable=True)
    drone_model = Column(String(100), nullable=True)
    sensor_model = Column(String(100), nullable=True)
    
    # Spatial Info
    crs = Column(String(100), nullable=True)
    epsg = Column(String(20), nullable=True)
    min_x = Column(Float, nullable=True)
    min_y = Column(Float, nullable=True)
    min_z = Column(Float, nullable=True)
    max_x = Column(Float, nullable=True)
    max_y = Column(Float, nullable=True)
    max_z = Column(Float, nullable=True)
    
    # LiDAR specific
    point_count = Column(Integer, nullable=True)
    point_format = Column(Integer, nullable=True)
    average_density = Column(Float, nullable=True) # pts/m2
    has_rgb = Column(Boolean, default=False)
    has_intensity = Column(Boolean, default=False)
    has_classification = Column(Boolean, default=False)
    
    # Project & Versioning
    source = Column(String(100), nullable=True)
    project_name = Column(String(255), nullable=True)
    version = Column(String(50), default="v1.0")
    
    # Status
    status = Column(String(50), default="UPLOADED") # UPLOADED, PROCESSING, READY, ERROR
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "dataset_id": self.dataset_id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "crs": self.crs,
            "epsg": self.epsg,
            "point_count": self.point_count,
            "status": self.status
        }
