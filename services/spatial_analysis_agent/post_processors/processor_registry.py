from .base_processor import BaseProcessor
from .depth_area_risk_classifier import DepthAreaRiskClassifier
from .light_attribute_interpreter import LightAttributeInterpreter
from .wreck_risk_classifier import WreckRiskClassifier

# Registry mapping the post_processor string name from yaml to the actual instance
PROCESSOR_REGISTRY = {
    "depth_area_risk_classifier": DepthAreaRiskClassifier(),
    "light_attribute_interpreter": LightAttributeInterpreter(),
    "wreck_risk_classifier": WreckRiskClassifier(),
}

def get_processor(name: str) -> BaseProcessor:
    """Retrieve a processor by name."""
    return PROCESSOR_REGISTRY.get(name)
