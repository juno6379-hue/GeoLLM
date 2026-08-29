from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from app.orchestrator.job_manager import CeleryJobManager
from app.orchestrator.module_registry import ModuleRegistry

router = APIRouter()

class JobRequest(BaseModel):
    input_data: Dict[str, Any]
    parameters: Dict[str, Any] = {}

@router.post("/ground-classification")
def run_ground_classification(request: JobRequest):
    module_name = "ground_classification"
    
    # Validate if module is registered
    module_cls = ModuleRegistry.get_module(module_name)
    if not module_cls:
        raise HTTPException(status_code=404, detail="Module not found")
        
    # Submit job
    job_id = CeleryJobManager.submit_job(
        module_name=module_name,
        input_data=request.input_data,
        parameters=request.parameters
    )
    
    return {"job_id": job_id, "status": "Job submitted successfully"}

@router.get("/status/{job_id}")
def get_status(job_id: str):
    status = CeleryJobManager.get_job_status(job_id)
    return status
