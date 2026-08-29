from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from pydantic import BaseModel
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

class FolderRegisterRequest(BaseModel):
    folder_path: str
    source: str = "LOCAL_SCAN"
    project_name: str = "부산항 시범구역"

@router.post("/register_folder")
def register_local_folder(req: FolderRegisterRequest, db: Session = Depends(get_postgis_db)):
    """
    Scans a local directory on the server, extracts metadata for LiDAR files,
    saves them to the database, and finds 3D tiles for visualization.
    """
    folder = req.folder_path
    if not os.path.isdir(folder):
        raise HTTPException(status_code=400, detail=f"Directory not found: {folder}")
        
    extracted_datasets = []
    
    viz_data = {
        "ortho": None,
        "pointcloud": None,
        "dsm": None,
        "min_z": 0.0
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
                            new_dataset = LiDARDataset(
                                dataset_id=metadata["dataset_id"],
                                file_name=metadata["file_name"],
                                file_path=metadata["file_path"],
                                file_type=metadata["file_type"],
                                file_size_bytes=metadata["file_size_bytes"],
                                point_count=metadata.get("point_count"),
                                point_format=metadata.get("point_format"),
                                min_x=metadata.get("min_x"),
                                min_y=metadata.get("min_y"),
                                min_z=metadata.get("min_z"),
                                max_x=metadata.get("max_x"),
                                max_y=metadata.get("max_y"),
                                max_z=metadata.get("max_z"),
                                average_density=metadata.get("average_density"),
                                has_rgb=metadata.get("has_rgb", False),
                                has_intensity=metadata.get("has_intensity", False),
                                source=metadata.get("source"),
                                project_name=metadata.get("project_name")
                            )
                            db.add(new_dataset)
                            db.commit()
                            db.refresh(new_dataset)
                            
                    extracted_datasets.append(metadata)
                except Exception as e:
                    print(f"Failed to parse {file_path}: {e}")

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
        "message": f"Successfully scanned folder: {folder}",
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
    # Kept for backward compatibility if manual upload is ever needed
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        user_metadata = {
            "source": source,
            "project_name": project_name
        }
        metadata = process_ingestion(file_path, user_metadata)
        
        if db is not None:
            new_dataset = LiDARDataset(
                dataset_id=metadata["dataset_id"],
                file_name=metadata["file_name"],
                file_path=metadata["file_path"],
                file_type=metadata["file_type"],
                file_size_bytes=metadata["file_size_bytes"],
                point_count=metadata.get("point_count")
            )
            db.add(new_dataset)
            db.commit()
            
        return {"message": "Upload successful", "dataset": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PreprocessRequest(BaseModel):
    dataset_id: str
    sor_mean_k: int = 50
    sor_std_dev_mul: float = 1.0

@router.post("/preprocess")
async def preprocess_lidar(req: PreprocessRequest, db: Session = Depends(get_postgis_db)):
    """
    Module 02: 점군 노이즈 제거 (Statistical Outlier Removal)
    """
    try:
        # 1. DB에서 dataset 조회
        if req.dataset_id == 'demo_dataset_001':
            # UI 데모용 가짜 데이터셋 생성
            class MockDataset:
                file_path = "D:/dummy_pointcloud.laz"
            dataset = MockDataset()
        else:
            dataset = db.query(LiDARDataset).filter(LiDARDataset.dataset_id == req.dataset_id).first()
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
        
        # 실제 Python/C++ 기반 전처리 에이전트(Module 02) 호출 로직 연동
        result = run_preprocessing(
            dataset_id=req.dataset_id,
            input_path=dataset.file_path,
            mean_k=req.sor_mean_k,
            std_dev_mul=req.sor_std_dev_mul
        )
        
        return {
            "message": "Preprocessing finished successfully.",
            "status": "SUCCESS",
            "job_id": f"job-prep-{req.dataset_id}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ClassifyRequest(BaseModel):
    dataset_id: str
    cloth_resolution: float = 0.5
    class_threshold: float = 0.5

@router.post("/classify")
async def classify_lidar(req: ClassifyRequest, db: Session = Depends(get_postgis_db)):
    """
    Module 03: 지상/비지상 분류 및 DEM 생성 (Cloth Simulation Filter)
    """
    try:
        if req.dataset_id == 'demo_dataset_001':
            pass # UI 데모용 가짜 데이터셋 바이패스
        else:
            dataset = db.query(LiDARDataset).filter(LiDARDataset.dataset_id == req.dataset_id).first()
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # TODO: 실제 분류 에이전트(Module 03) 호출 로직 연동
    
    return {
        "message": "Classification and DEM generation started.",
        "status": "RUNNING",
        "job_id": f"job-cls-{req.dataset_id}",
        "parameters": {
            "cloth_resolution": req.cloth_resolution,
            "class_threshold": req.class_threshold
        }
    }
