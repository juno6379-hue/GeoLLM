import os
import glob
import json
from typing import List
from shared.security.context import ClearanceLevel
from shared.schemas.agent import DatasetVersion

class DatasetCatalogEntry:
    def __init__(self, dataset_id: str, version: str, logical_name: str, security_level: str, keywords: List[str], is_external_api: bool = False, api_endpoint: str = ""):
        self.dataset_id = dataset_id
        self.version = version
        self.logical_name = logical_name
        self.security_level = security_level
        self.keywords = keywords
        self.is_external_api = is_external_api
        self.api_endpoint = api_endpoint

def build_live_catalog(base_path: str = "D:/rag_sources") -> List[DatasetCatalogEntry]:
    catalog = [
        DatasetCatalogEntry(
            dataset_id="enc-busan-001",
            version="v1.0",
            logical_name="부산항 ENC 위험객체",
            security_level=ClearanceLevel.PUBLIC,
            keywords=["부산항", "위험객체", "ENC", "S-101"],
        ),
        DatasetCatalogEntry(
            dataset_id="ais-busan-2026",
            version="v1.0",
            logical_name="부산항 AIS 항적",
            security_level=ClearanceLevel.RESTRICTED,
            keywords=["부산항", "AIS", "선박", "항적"],
        ),
        DatasetCatalogEntry(
            dataset_id="mil-zone-001",
            version="v1.0",
            logical_name="부산항 제한구역",
            security_level=ClearanceLevel.SECRET,
            keywords=["부산항", "제한구역", "통제구역"],
        ),
    ]
    
    # 1. External APIs (Configured from external JSON)
    api_catalog_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "external_api_catalog.json")
    if os.path.exists(api_catalog_path):
        try:
            with open(api_catalog_path, "r", encoding="utf-8") as f:
                apis = json.load(f)
                for api in apis:
                    catalog.append(DatasetCatalogEntry(
                        dataset_id=api.get("dataset_id", ""),
                        version=api.get("version", "v1.0"),
                        logical_name=api.get("logical_name", ""),
                        security_level=ClearanceLevel(api.get("security_level", "PUBLIC")),
                        keywords=api.get("keywords", []),
                        is_external_api=api.get("is_external_api", True),
                        api_endpoint=api.get("api_endpoint", "")
                    ))
        except Exception as e:
            print(f"Error loading external API catalog: {e}")
    
    # 2. Dynamic Filesystem Scanning for Datasets (CSV only, documents go to Vector DB)
    if not os.path.exists(base_path):
        return catalog
        
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file).replace("\\", "/")
                dataset_id = f"local-ds-{len(catalog)}"
                logical_name = os.path.splitext(file)[0]
                
                # Auto-generate keywords from filename
                keywords = ["데이터", "csv", "통계"]
                for chunk in logical_name.split("_"):
                    if chunk:
                        keywords.append(chunk)
                
                catalog.append(DatasetCatalogEntry(
                    dataset_id=dataset_id,
                    version="v1.0",
                    logical_name=logical_name,
                    security_level=ClearanceLevel.PUBLIC,
                    keywords=keywords,
                    is_external_api=False,
                    api_endpoint=file_path
                ))
                
    return catalog
