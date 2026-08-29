from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProcessor(ABC):
    """Base class for all feature-specific post processors."""
    
    @abstractmethod
    def process(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the properties of a feature and return the enriched properties.
        
        Args:
            properties (Dict[str, Any]): The original GeoJSON properties.
            
        Returns:
            Dict[str, Any]: The processed GeoJSON properties.
        """
        pass
