import os
import json
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

def fake_embed(text: str) -> list:
    # MVP 데모용 가짜 임베딩 (OpenAI 크레딧 부족 우회)
    # 키워드에 따라 3차원 직교 벡터 반환
    if "위험" in text or "강한" in text:
        return [1.0, 0.0, 0.0]
    elif "잔잔" in text or "안전" in text:
        return [0.0, 1.0, 0.0]
    else:
        return [0.0, 0.0, 1.0]

def create_mock_s111_db():
    # 3개의 가상 S-111 해역 폴리곤(GeoJSON) 및 시맨틱 묘사
    s111_data = [
        {
            "id": "s111_zone_a",
            "name": "부산 북항 진입로",
            "semantic_text": "2026년 7월 19일 14:00, 부산 북항 진입로 해역은 남동쪽으로 3.5노트의 매우 강한 해수유동이 발생합니다. 측면 조류가 강해 소형 선박이 휩쓸리거나 조종 불능에 빠질 수 있는 위험 구역입니다.",
            "geom": {
                "type": "Polygon",
                "coordinates": [[[129.05, 35.10], [129.07, 35.10], [129.07, 35.12], [129.05, 35.12], [129.05, 35.10]]]
            }
        },
        {
            "id": "s111_zone_b",
            "name": "오륙도 인근 해역",
            "semantic_text": "2026년 7월 19일 14:00, 오륙도 인근 해역은 유속이 0.5노트 미만으로 매우 잔잔하며 조류의 영향이 거의 없습니다. 소형 선박을 포함한 모든 선박이 안전하게 대기하거나 운항할 수 있는 최적의 구역입니다.",
            "geom": {
                "type": "Polygon",
                "coordinates": [[[129.07, 35.08], [129.09, 35.08], [129.09, 35.10], [129.07, 35.10], [129.07, 35.08]]]
            }
        },
        {
            "id": "s111_zone_c",
            "name": "부산 남항 앞바다",
            "semantic_text": "2026년 7월 19일 14:00, 부산 남항 인근은 서쪽으로 1.5노트의 중간 세기 조류가 흐르고 있습니다. 항만 진입 시 측면으로 밀릴 수 있으므로 주의가 필요합니다.",
            "geom": {
                "type": "Polygon",
                "coordinates": [[[129.03, 35.07], [129.05, 35.07], [129.05, 35.09], [129.03, 35.09], [129.03, 35.07]]]
            }
        }
    ]

    db_path = os.path.join(os.path.dirname(__file__), 's111_vector_store.json')
    print("Generating mock embeddings...")
    
    for item in s111_data:
        vector = fake_embed(item["semantic_text"])
        item["embedding"] = vector
        
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(s111_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated and saved embeddings to {db_path}!")

if __name__ == "__main__":
    create_mock_s111_db()
