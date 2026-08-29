import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from shared.observability.logger import get_logger

logger = get_logger('spatial_catalog_tool')

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'spatial_catalog.json')
CATALOG_DATA = []

def load_catalog():
    global CATALOG_DATA
    if not CATALOG_DATA and os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                CATALOG_DATA = json.load(f)
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            CATALOG_DATA = []
    return CATALOG_DATA

class CatalogSearchInput(BaseModel):
    query: str = Field(description="The keyword or query to search in the spatial catalog.")

@tool("lookup_spatial_catalog", args_schema=CatalogSearchInput)
def lookup_spatial_catalog(query: str) -> str:
    """
    Search the spatial data catalog to find matching layers or datasets.
    Returns the metadata of the matched layers, including the target_layer name.
    """
    cat = load_catalog()
    return json.dumps(cat, ensure_ascii=False)
