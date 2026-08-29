from langchain_core.tools import tool
from typing import Dict, Any, Optional
from sqlalchemy import text
from data.database import get_postgis_db
from shared.observability.logger import get_logger

logger = get_logger("spatial_analysis_agent.geocoding_tool")

@tool
def get_maritime_coordinates(place_name: str) -> str:
    """
    사용자가 입력한 해양 및 육상 지명(예: "여수 앞바다", "제주공항")을 검색하여
    WKT(Well-Known Text) 형식의 공간 좌표(POINT)로 반환하는 지오코딩 도구입니다.
    
    [핵심 로직]
    1. 1차 검색: 자체 구축한 해양 지명사전(maritime_gazetteer) DB 조회
    2. 2차 검색(Fallback): 해양 사전에 없을 경우 OpenStreetMap(OSM) API 호출하여 육상 지명 검색
    3. 캐싱(Caching): OSM API 호출 속도 제한(Rate Limit)을 피하기 위해 결과를 DB에 저장 및 재사용
    
    Args:
        place_name: 검색할 장소 이름 (예: "여수 앞바다", "Busan Port", "제주공항")
        
    Returns:
        WKT 형식의 포인트 좌표 (예: "POINT(127.7 34.7)") 또는 실패 시 에러 메시지
    """
    
    clean_name = place_name.replace("앞바다", "").replace(" 앞바다", "").replace("인근", "").replace(" 인근", "").replace("주변", "").replace(" 주변", "").replace("근처", "").replace(" 근처", "").replace("입구", "").replace(" 입구", "").replace("출구", "").replace(" 출구", "").replace("해역", "").replace(" 해역", "").strip()

    db = None
    try:
        db = next(get_postgis_db())
    except Exception as e:
        logger.warning(f"Failed to connect to PostGIS DB: {e}. Will proceed directly to OSM fallback.")
        
    try:
        clean_name = place_name.replace("앞바다", "").replace(" 앞바다", "").replace("인근", "").replace(" 인근", "").replace("주변", "").replace(" 주변", "").replace("근처", "").replace(" 근처", "").replace("입구", "").replace(" 입구", "").replace("출구", "").replace(" 출구", "").replace("해역", "").replace(" 해역", "").strip()
        
        # 방어 로직: 면적(Polygon) 객체나 너무 일반적인 개념은 단일 점(Point) 좌표로 변환(Geocoding)하는 것을 기각함
        reject_list = ["해양보호구역", "정박지", "항로", "위험구역", "제한구역", "선박 충돌 위험구역", "장애물", "침선"]
        if any(reject_word in clean_name for reject_word in reject_list):
            logger.warning(f"Geocoding rejected for generic area/feature term: '{clean_name}'")
            return f"ERROR: '{clean_name}'은(는) 면적을 가지거나 추상적인 객체이므로 단일 좌표(위치)로 변환할 수 없습니다."
            
        result = None
        
        if db is not None:
            try:
                # ILIKE를 사용하여 대소문자 구분 없이 한글(name_kor) 및 영문(name_eng) 명칭을 모두 검색합니다.
                # 정확히 일치(exact match)하는 것을 최우선으로, 그 다음으로 '시작하는' 단어를 정렬하여 가져옵니다.
                sql = text("""
                    SELECT name_kor, name_eng, ST_AsText(geom) as wkt
                    FROM maritime_gazetteer
                    WHERE name_kor ILIKE :query OR name_eng ILIKE :query
                    ORDER BY 
                        CASE 
                            WHEN name_kor = :exact OR name_eng = :exact THEN 1
                            WHEN name_kor LIKE :starts OR name_eng LIKE :starts THEN 2
                            ELSE 3
                        END
                    LIMIT 1
                """)
                
                result = db.execute(sql, {
                    "query": f"%{clean_name}%",
                    "exact": clean_name,
                    "starts": f"{clean_name}%"
                }).mappings().first()
            except Exception as dbe:
                logger.warning(f"Gazetteer query failed (table might be missing): {dbe}")
                db.rollback()
                result = None
        
        if result:
            kor = result["name_kor"] or ""
            eng = result["name_eng"] or ""
            matched_name = kor if kor else eng
            logger.info(f"Geocoding successful: '{place_name}' -> '{matched_name}' ({result['wkt']})")
            return f"{result['wkt']}"
        else:
            # [Fallback] 해양 사전 검색 실패 시, 육상 랜드마크일 확률이 높으므로 OSM(OpenStreetMap) 검색을 시도합니다.
            
            # 1. API 밴(Ban) 방지를 위해 자체 DB의 캐시(osm_geocoding_cache) 테이블을 먼저 뒤져봅니다 (Cache Hit).
            if db is not None:
                try:
                    cache_sql = text("SELECT ST_AsText(result_wkt) as wkt FROM osm_geocoding_cache WHERE query_type = 'forward' AND query_key = :key LIMIT 1")
                    cache_hit = db.execute(cache_sql, {"key": clean_name}).mappings().first()
                    if cache_hit and cache_hit["wkt"]:
                        logger.info(f"OSM Cache hit for '{clean_name}': {cache_hit['wkt']}")
                        return cache_hit["wkt"]
                except Exception as ce:
                    logger.warning(f"Cache check failed: {ce}")
                    db.rollback()

            # 2. 캐시에 없다면, 외부 OSM API(Nominatim)를 실제로 호출합니다 (Cache Miss).
            import requests
            try:
                headers = {'User-Agent': 'GeoLLM_Spatial_Agent/1.0'}
                osm_url = f"https://nominatim.openstreetmap.org/search?q={clean_name}&format=json&limit=1"
                
                import time
                start_osm = time.time()
                resp = requests.get(osm_url, headers=headers, timeout=5)
                osm_latency = time.time() - start_osm
                logger.info(f"[LATENCY] OSM Nominatim API call took {osm_latency:.3f} seconds for '{clean_name}'")
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data and len(data) > 0:
                        lat = data[0]['lat']
                        lon = data[0]['lon']
                        wkt = f"POINT({lon} {lat})"
                        logger.info(f"OSM Geocoding successful: '{place_name}' -> {wkt}")
                        
                        # 3. 다음 검색 시 API 호출을 생략하기 위해 호출 결과를 DB에 즉시 저장합니다 (Cache Save).
                        if db is not None:
                            try:
                                insert_sql = text("INSERT INTO osm_geocoding_cache (query_type, query_key, result_wkt) VALUES ('forward', :key, ST_GeomFromText(:wkt, 4326))")
                                db.execute(insert_sql, {"key": clean_name, "wkt": wkt})
                                db.commit()
                            except Exception as ce:
                                logger.warning(f"Failed to save to OSM cache: {ce}")
                                db.rollback()
                            
                        return wkt
            except Exception as osm_e:
                logger.error(f"OSM fallback failed: {osm_e}")
                
            return f"ERROR: Location '{place_name}' not found in gazetteer or OSM. Please provide exact WKT coordinates or a different name."
            
    except Exception as e:
        logger.error(f"Geocoding query failed: {e}")
        return f"ERROR: Failed to search gazetteer: {e}"
    finally:
        if db is not None:
            db.close()

