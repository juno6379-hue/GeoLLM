from typing import List, Dict, Any

# MVP를 위한 임시 문서 Chunk 데이터베이스
# 향후 PostgreSQL + pgvector 로 교체됩니다.

MOCK_DOCUMENTS = [
    {
        "doc_id": "doc-s101-001",
        "title": "S-101 Electronic Navigational Chart (ENC) Product Specification",
        "version": "1.2.0",
        "content": "위험객체(Hazard) 중 침선(Wreck)은 해상 운항에 중대한 위협이 되므로 수심 20m 미만 지역에서 반드시 표시되어야 한다.",
        "section": "12.3 Wrecks",
        "page": "p.45",
        "source": "IHO (International Hydrographic Organization)",
        "keywords": ["위험객체", "침선", "s101", "수심"]
    },
    {
        "doc_id": "doc-law-001",
        "title": "해양환경관리법",
        "version": "2025.01",
        "content": "해상풍력 단지 개발 시 후보지는 지정된 해양보호구역에서 최소 2km 이상 이격되어야 한다.",
        "section": "제 15조 2항",
        "page": "N/A",
        "source": "해양수산부",
        "keywords": ["해상풍력", "보호구역", "거리", "이격"]
    },
    {
        "doc_id": "doc-imo-001",
        "title": "IMO COLREGs",
        "version": "1972",
        "content": "통항분리수역(TSS) 내에서 선박은 정해진 방향으로만 항해해야 하며, 횡단 시에는 기항 방향에 대해 직각으로 횡단해야 한다.",
        "section": "Rule 10",
        "page": "p.12",
        "source": "IMO (International Maritime Organization)",
        "keywords": ["통항분리수역", "항해", "선박", "tss"]
    }
]

def search_mock_vdb(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """
    쿼리와 문서의 키워드를 단순 매칭하여 반환합니다.
    (실제로는 임베딩 모델 기반 코사인 유사도 검색을 수행합니다.)
    """
    results = []
    query_lower = query.lower()
    
    for doc in MOCK_DOCUMENTS:
        score = 0
        for kw in doc["keywords"]:
            if kw in query_lower:
                score += 1
        
        # 단순 점수화
        if score > 0:
            results.append({"doc": doc, "score": score})
            
    # score 기준 내림차순 정렬 후 top_k 반환
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return [r["doc"] for r in results[:top_k]]
