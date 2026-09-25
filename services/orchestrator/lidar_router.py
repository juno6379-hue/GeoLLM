from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from data.database import get_postgis_db
from data.models.lidar_dataset import LiDARDataset
from services.drone_analysis_agent.data_ingestion import process_ingestion
from services.drone_analysis_agent.module02_preprocessing import run_preprocessing
import os
import shutil

router = APIRouter(prefix="/lidar", tags=["LiDAR Ingestion"])

@router.get("/test_hello")
async def test_hello():
    return {"message": "hello"}

# Ensure temp directory exists
UPLOAD_DIR = os.path.join(os.getcwd(), "geollm_results", "lidar_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _dataset_from_metadata(metadata):
    fields = ("dataset_id", "file_name", "file_path", "file_type", "file_size_bytes",
              "point_count", "point_format", "crs", "min_x", "min_y", "min_z",
              "max_x", "max_y", "max_z", "average_density", "has_rgb", "has_intensity",
              "source", "project_name")
    return LiDARDataset(**{key: metadata[key] for key in fields if key in metadata})


class FolderRegisterRequest(BaseModel):
    folder_path: str
    source: str = "LOCAL_SCAN"
    project_name: str | None = None

@router.post("/register_folder")
def register_local_folder(req: FolderRegisterRequest, db: Session = Depends(get_postgis_db)):
    """
    Scans a local directory on the server, extracts metadata for LiDAR files,
    saves them to the database, and finds 3D tiles for visualization.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="LiDAR dataset database is unavailable")
    folder = req.folder_path
    if not os.path.isdir(folder):
        raise HTTPException(status_code=400, detail=f"Directory not found: {folder}")
        
    extracted_datasets = []
    failures = []
    
    viz_data = {
        "ortho": None,
        "pointcloud": None,
        "dsm": None,
        "min_z": None
    }

    # Recursive scan (depth limited to 3 to prevent infinite crawls)
    for root, dirs, files in os.walk(folder):
        depth = root[len(folder):].count(os.sep)
        if depth > 3:
            dirs.clear()
            continue
            
        # 1. Look for 3D visualization assets
        if "terra_dom" in dirs and not viz_data["ortho"]:
            viz_data["ortho"] = os.path.join(root, "terra_dom").replace("\\", "/")
            
        if "terra_pnts" in dirs and not viz_data["pointcloud"]:
            ts_path = os.path.join(root, "terra_pnts", "tileset.json")
            if os.path.isfile(ts_path):
                viz_data["pointcloud"] = ts_path.replace("\\", "/")
                
        if "terra_dsm" in dirs and not viz_data["dsm"]:
            ts_path = os.path.join(root, "terra_dsm", "tileset.json")
            if os.path.isfile(ts_path):
                viz_data["dsm"] = ts_path.replace("\\", "/")

        # 2. Look for raw LiDAR files to extract metadata
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.las', '.laz']:
                file_path = os.path.join(root, file)
                try:
                    user_metadata = {
                        "source": req.source,
                        "project_name": req.project_name
                    }
                    metadata = process_ingestion(file_path, user_metadata)
                    
                    if db is not None:
                        # Check if already exists to prevent duplicates based on path
                        existing = db.query(LiDARDataset).filter(LiDARDataset.file_path == file_path).first()
                        if not existing:
                            new_dataset = _dataset_from_metadata(metadata)
                            db.add(new_dataset)
                            db.commit()
                            db.refresh(new_dataset)
                        else:
                            metadata["dataset_id"] = existing.dataset_id
                            
                    extracted_datasets.append(metadata)
                except Exception as e:
                    db.rollback()
                    failures.append({"file": file_path, "error": str(e)})

    # Extract min_z from tileset if possible
    import json
    try:
        tileset_to_check = viz_data["dsm"] if viz_data["dsm"] else viz_data["pointcloud"]
        if tileset_to_check and os.path.isfile(tileset_to_check):
            with open(tileset_to_check, "r", encoding="utf-8") as f:
                ts_data = json.load(f)
                region = ts_data.get("root", {}).get("boundingVolume", {}).get("region", [])
                if len(region) == 6:
                    viz_data["min_z"] = region[4]
    except Exception as e:
        print("Error reading min_z:", e)

    return {
        "status": "PARTIAL" if failures else "COMPLETED",
        "errors": failures,
        "message": f"Registered {len(extracted_datasets)} datasets; {len(failures)} failures",
        "datasets": extracted_datasets,
        "visualization": viz_data
    }

@router.post("/upload")
async def upload_lidar_dataset(
    file: UploadFile = File(...),
    source: str = Form(None),
    project_name: str = Form(None),
    db: Session = Depends(get_postgis_db)
):
    if db is None:
        raise HTTPException(status_code=503, detail="LiDAR dataset database is unavailable")
    import uuid
    filename = os.path.basename((file.filename or "").replace("\\", "/"))
    if os.path.splitext(filename)[1].lower() not in {".las", ".laz"}:
        raise HTTPException(status_code=422, detail="Only LAS/LAZ point clouds are supported")
    try:
        file_path = os.path.join(UPLOAD_DIR, uuid.uuid4().hex + "_" + filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        user_metadata = {
            "source": source,
            "project_name": project_name
        }
        metadata = process_ingestion(file_path, user_metadata)
        
        if db is not None:
            new_dataset = _dataset_from_metadata(metadata)
            db.add(new_dataset)
            db.commit()
            
        return {"message": "Upload successful", "dataset": metadata}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Dataset registration failed") from e

class PreprocessRequest(BaseModel):
    dataset_id: str
    sor_mean_k: int = Field(default=50, ge=2, le=10000)
    sor_std_dev_mul: float = Field(default=1.0, gt=0, allow_inf_nan=False)

@router.post("/preprocess")
async def preprocess_lidar(req: PreprocessRequest, db: Session = Depends(get_postgis_db)):
    """
    Module 02: 점군 노이즈 제거 (Statistical Outlier Removal)
    """
    if db is None:
        raise HTTPException(status_code=503, detail="LiDAR dataset database is unavailable")
    try:
        dataset = db.query(LiDARDataset).filter(LiDARDataset.dataset_id == req.dataset_id).first()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="LiDAR dataset database is unavailable") from exc
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        import asyncio
        result = await asyncio.to_thread(run_preprocessing, req.dataset_id, dataset.file_path,
                                         req.sor_mean_k, req.sor_std_dev_mul)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="LiDAR processing failed; no successful output is available") from exc
    return {"status": "SUCCESS", "result": result}

class ClassifyRequest(BaseModel):
    dataset_id: str
    cloth_resolution: float = Field(default=0.5, gt=0, allow_inf_nan=False)
    class_threshold: float = Field(default=0.5, gt=0, allow_inf_nan=False)

@router.post("/classify")
async def classify_lidar(req: ClassifyRequest, db: Session = Depends(get_postgis_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="LiDAR dataset database is unavailable")
    try:
        dataset = db.query(LiDARDataset).filter(LiDARDataset.dataset_id == req.dataset_id).first()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="LiDAR dataset database is unavailable") from exc
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    raise HTTPException(status_code=501, detail="Classification and DEM generation are not implemented; no job was started")
