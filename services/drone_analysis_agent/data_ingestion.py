import os
import laspy
from datetime import datetime
import uuid

def parse_las_header(file_path: str) -> dict:
    """
    Parses the header of a LAS/LAZ file and extracts required metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        # Open file using laspy
        with laspy.open(file_path) as fh:
            header = fh.header
            
            metadata = {
                "point_count": int(header.point_count),
                "has_rgb": all(name in header.point_format.dimension_names for name in ("red", "green", "blue")),
                "has_intensity": "intensity" in header.point_format.dimension_names,
                "point_format": header.point_format.id,
                "min_x": header.x_min,
                "max_x": header.x_max,
                "min_y": header.y_min,
                "max_y": header.y_max,
                "min_z": header.z_min,
                "max_z": header.z_max,
                "version": f"{header.version.major}.{header.version.minor}",
                "system_id": header.system_id,
                "generating_software": header.generating_software,
                "creation_date": None
            }
            
            try:
                # LAS creation date is stored as day of year and year
                if header.creation_date:
                    metadata["creation_date"] = header.creation_date.isoformat()
            except:
                pass
                
            # Additional VLR (Variable Length Records) parsing for CRS/EPSG could be added here
            # For this MVP, we extract the basic bounding box and point count.
            
            # Simple volume estimation for average density
            dx = metadata["max_x"] - metadata["min_x"]
            dy = metadata["max_y"] - metadata["min_y"]
            area = dx * dy
            crs = header.parse_crs()
            metadata["crs"] = crs.to_string() if crs else None
            metric_crs = crs is not None and crs.is_projected and all(axis.unit_name == "metre" for axis in crs.axis_info[:2])
            metadata["average_density"] = metadata["point_count"] / area if metric_crs and area > 0 else None
            
            return metadata
            
    except Exception as e:
        raise RuntimeError(f"Failed to parse LAS/LAZ header: {str(e)}")

def process_ingestion(file_path: str, user_metadata: dict = None) -> dict:
    """
    Process the uploaded file, extract metadata, and prepare it for the dataset registry.
    """
    if user_metadata is None:
        user_metadata = {}
        
    ext = os.path.splitext(file_path)[1].lower()
    
    extracted_metadata = {}
    if ext in ['.las', '.laz']:
        extracted_metadata = parse_las_header(file_path)
    else:
        raise ValueError("Only LAS/LAZ ingestion is implemented")

    # Generate Dataset ID
    now = datetime.now()
    unique_short_id = str(uuid.uuid4().hex)[:6].upper()
    dataset_id = f"DS-{now.year}-{unique_short_id}"
    
    # Merge extracted and user provided metadata
    final_metadata = {
        "dataset_id": dataset_id,
        "file_name": os.path.basename(file_path),
        "file_path": file_path,
        "file_type": ext.strip('.').upper(),
        "file_size_bytes": os.path.getsize(file_path),
        **extracted_metadata,
        **user_metadata
    }
    
    return final_metadata
