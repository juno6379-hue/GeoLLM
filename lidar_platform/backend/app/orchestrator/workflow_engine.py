import logging
from typing import List, Dict, Any
from .module_registry import ModuleRegistry
from .job_manager import CeleryJobManager

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Orchestrates multiple analysis modules in a sequence or DAG.
    """
    
    @classmethod
    def execute_pipeline(cls, pipeline_id: str, modules_to_run: List[str], initial_input: Dict[str, Any]) -> str:
        """
        Executes a sequence of modules.
        For example: ['ingestion', 'preprocessing', 'classification']
        """
        logger.info(f"Starting pipeline {pipeline_id} with modules: {modules_to_run}")
        
        # Validate modules exist
        for mod_name in modules_to_run:
            if not ModuleRegistry.get_module(mod_name):
                raise ValueError(f"Module {mod_name} is not registered in ModuleRegistry.")
        
        # In a real workflow, this would chain Celery tasks.
        # For now, we simulate starting the first job.
        first_module = modules_to_run[0]
        job_id = CeleryJobManager.submit_job(first_module, initial_input, parameters={})
        return job_id
