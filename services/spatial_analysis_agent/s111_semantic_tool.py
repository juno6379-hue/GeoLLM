import os
import json
import numpy as np
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from shared.schemas.agent import ToolCallLog
from shared.schemas.map import MapLayerSpecification
import time

def fake_embed(text: str) -> list:
    if "위험" in text or "강한" in text or "거센" in text or "힘든" in text:
        return [1.0, 0.0, 0.0]
    elif "잔잔" in text or "안전" in text:
        return [0.0, 1.0, 0.0]
    else:
        return [0.0, 0.0, 1.0]

@tool
def search_s111_semantic(query: str) -> Dict[str, Any]:
    """
    S-111 (해수유동/조류/표층해류)에 대해 자연어로 묘사된 위험도나 상태(예: "작은 배가 지나가기 힘든 강한 조류", "조류가 거센 곳")를 검색하여 가장 적합한 해역의 공간 정보(GeoJSON)를 반환합니다.
    """
    start_time = time.time()
    
    db_path = os.path.join(os.path.dirname(__file__), 's111_vector_store.json')
    if not os.path.exists(db_path):
        return {"status": "FAILED", "errors": ["s111_vector_store.json not found. Please run mock db generator first."]}
        
    with open(db_path, "r", encoding="utf-8") as f:
        mock_db = json.load(f)
        
    # 질의 임베딩
    query_vector = np.array(fake_embed(query))
    
    best_match = None
    best_score = -1.0
    
    # 코사인 유사도 연산
    for item in mock_db:
        item_vector = np.array(item["embedding"])
        # 코사인 유사도 = dot(A,B) / (norm(A)*norm(B))
        score = np.dot(query_vector, item_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(item_vector))
        if score > best_score:
            best_score = score
            best_match = item
            
    if not best_match:
        return {"status": "FAILED", "errors": ["No matches found in S-111 mock database."]}
        
    # 결과를 GeoJSON Feature로 변환
    feature = {
        "type": "Feature",
        "properties": {
            "name": best_match["name"],
            "semantic_text": best_match["semantic_text"],
            "similarity_score": round(float(best_score), 4),
            "layer_type": "s111_surface_current",
            # UI 강조를 위한 속성
            "fillColor": "#ff0000" if "위험" in best_match["semantic_text"] else "#0000ff",
            "color": "#ff0000" if "위험" in best_match["semantic_text"] else "#0000ff"
        },
        "geometry": best_match["geom"]
    }
    
    # MapLayerSpecification 포맷을 위한 구조화
    return {
        "status": "SUCCESS",
        "tool_name": "search_s111_semantic",
        "execution_time": (time.time() - start_time) * 1000,
        "structured_result": {
            "count": 1,
            "map_spec": {
                "layer_id": f"layer_s111_{int(time.time())}",
                "title": f"S-111 Semantic Search: {best_match['name']}",
                "description": best_match["semantic_text"],
                "geometry_type": "GEOMETRY",
                "source_type": "GEOJSON",
                "inline_geojson": {"type": "FeatureCollection", "features": [feature]},
                "feature_count": 1
            }
        }
    }
