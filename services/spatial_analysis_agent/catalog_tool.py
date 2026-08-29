import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from shared.observability.logger import get_logger

logger = get_logger("catalog_tool")

# Load catalog in memory
CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "s101_catalogue.json")
CATALOG_DATA = []

def load_catalog():
    global CATALOG_DATA
    if not CATALOG_DATA and os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                CATALOG_DATA = json.load(f)
        except Exception as e:
            logger.error("Failed to load S-101 catalog", error=str(e))

class CatalogSearchInput(BaseModel):
    query: str = Field(description="검색할 해양 용어 (예: 양식장, 침선, 항로, 위험객체)")

@tool("lookup_s101_catalog", args_schema=CatalogSearchInput)
def lookup_s101_catalog(query: str) -> str:
    """
    S-101 전자해도 객체 사전(카탈로그)을 검색하여 해양 용어에 대한 nftc 코드 및 설명을 반환합니다.
    사용자의 질의에서 S-101 객체(예: 부표, 어장, 해저케이블 등)가 포함된 경우 이 도구를 사용하여 정확한 nftc 코드를 파악하세요.
    """
    load_catalog()
    if not CATALOG_DATA:
        return "카탈로그 데이터를 불러올 수 없습니다."
        
    query = query.lower().strip()
    
    # Simple keyword matching
    matches = []
    for item in CATALOG_DATA:
        if query in item["name"].lower() or query in item["name_kr"].lower() or query in item["description"]:
            matches.append(item)
            
    if not matches:
        # Fallback to broader search
        for item in CATALOG_DATA:
            # If any character matches significantly or word splits
            if any(word in item["name_kr"] for word in query.split()):
                matches.append(item)
                
    if not matches:
        return f"'{query}'에 대한 S-101 객체를 찾을 수 없습니다. (제공 불가)"
        
    # Format response
    lines = []
    for m in matches[:5]: # Return top 5
        lines.append(f"- {m['name_kr']} ({m['name']}): nftc={m['nftc']}, 설명: {m['description']}")
        
    return "\n".join(lines)
