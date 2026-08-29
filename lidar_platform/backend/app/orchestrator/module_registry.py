import abc
import logging
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ModuleStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class BaseAnalysisModule(abc.ABC):
    """
    Base class for all LiDAR/Spatial Analysis modules.
    Enforces a standard interface: input, parameters, execute(), etc.
    """
    name: str = "BaseModule"
    version: str = "1.0"
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = ModuleStatus.PENDING
        self.progress = 0.0
        self.output: Dict[str, Any] = {}
        self.logs: list[str] = []
        self.quality: Dict[str, Any] = {}
        
    def _log(self, msg: str):
        self.logs.append(msg)
        logger.info(f"[{self.name}][{self.job_id}] {msg}")

    @abc.abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data structure and required fields."""
        pass

    @abc.abstractmethod
    def execute(self, input_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Core execution logic. Should update self.progress and self.status."""
        pass

    @abc.abstractmethod
    def validate_output(self) -> bool:
        """Validate the generated output before completing the job."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Return module metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "output": self.output,
            "quality": self.quality,
            "logs": self.logs
        }


class ModuleRegistry:
    """
    Registry for dynamically registering and fetching analysis modules.
    """
    _modules: Dict[str, Type[BaseAnalysisModule]] = {}

    @classmethod
    def register(cls, name: str, version: str = "1.0"):
        """Decorator to register a module."""
        def decorator(module_cls: Type[BaseAnalysisModule]):
            module_cls.name = name
            module_cls.version = version
            cls._modules[name] = module_cls
            logger.info(f"Registered module: {name} (v{version})")
            return module_cls
        return decorator

    @classmethod
    def get_module(cls, name: str) -> Optional[Type[BaseAnalysisModule]]:
        """Fetch a module class by name."""
        return cls._modules.get(name)

    @classmethod
    def get_all_modules(cls) -> Dict[str, Type[BaseAnalysisModule]]:
        """Get all registered modules."""
        return cls._modules
