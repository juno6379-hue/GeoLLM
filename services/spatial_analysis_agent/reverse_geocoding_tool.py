from langchain_core.tools import tool
from sqlalchemy import text
from data.database import get_postgis_db
from shared.observability.logger import get_logger

logger = get_logger("spatial_analysis_agent.reverse_geocoding_tool")

@tool
def get_location_name_from_coordinates(wkt_point: str) -> str:
    """
    사용자가 입력한 혹은 에이전트가 도출한 WKT(Well-Known Text) 좌표를 바탕으로,
    가장 가까운 해양 지명이나 육상 주소를 사람의 언어로 변환해 주는 '역지오코딩' 도구입니다.
    (예: POINT(127.7 34.7) -> "여수 앞바다에서 약 2.5km 떨어진 해역")
    
    [핵심 로직]
    1. 1차 공간 검색: 자체 해양 지명사전(maritime_gazetteer)에서 가장 가까운 포인트 검색
       - 이때 공간 인덱스(GIST)의 `<->` 연산자를 활용하여 빛의 속도로 스캔합니다.
       - 또한 위경도(degree)를 미터(m) 단위로 정확히 계산하기 위해 `::geography` 타입 캐스팅을 수행합니다.
    2. 2차 검색(Fallback): 해양 지명에서 5km 이상 떨어져 있다면 내륙으로 간주하고 OSM API 호출
    3. 캐싱(Caching): OSM API 호출 결과를 DB에 저장하여 속도 최적화 및 Rate Limit 우회
    
    Args:
        wkt_point: 검색할 위치의 WKT 포인트 형태 (예: "POINT(127.7 34.7)")
        
    Returns:
        가장 가까운 장소의 이름과 거리가 포함된 사람이 읽기 편한 문자열
    """
    # Simple validation
    if not wkt_point or not wkt_point.upper().startswith("POINT"):
        return "ERROR: Invalid input. Must be a valid WKT POINT (e.g., POINT(127.7 34.7))."

    db = None
    try:
        db = next(get_postgis_db())
    except Exception as e:
        logger.warning(f"Failed to connect to PostGIS DB: {e}. Will proceed directly to OSM reverse fallback.")
        
    try:
        result = None
        if db is not None:
            # <-> 연산자: PostGIS의 공간 인덱스(GIST)를 타게 만들어주는 K-Nearest Neighbor (KNN) 거리 연산자입니다.
            # ::geography 캐스팅: geometry 상태에서 거리를 구하면 위도/경도의 "도(degree)" 단위 거리가 나오지만,
            # geography로 형변환 후 ST_Distance를 구하면 지구의 둥근 곡면을 반영한 정확한 "미터(m)" 단위 거리가 도출됩니다.
            sql = text("""
                SELECT name_kor, name_eng, 
                       ST_Distance(geom::geography, ST_SetSRID(ST_GeomFromText(:wkt), 4326)::geography) as dist_meters
                FROM maritime_gazetteer
                ORDER BY geom <-> ST_SetSRID(ST_GeomFromText(:wkt), 4326)
                LIMIT 1
            """)
            
            result = db.execute(sql, {"wkt": wkt_point}).mappings().first()
        
        if result:
            kor = result["name_kor"] or ""
            eng = result["name_eng"] or ""
            matched_name = kor if kor else eng
            distance = int(result["dist_meters"])
            
            # 가장 가까운 바다 지명과의 거리가 5000m (5km) 이상이라면,
            # 사용자가 찍은 좌표가 바다가 아니라 완전한 내륙(육상)일 확률이 높습니다.
            # 이 경우 해양 사전만으로는 "여수 앞바다에서 40km 떨어진 곳"처럼 어색한 답변이 나오므로 OSM으로 Fallback 합니다.
            if distance > 5000:
                logger.info(f"Maritime location too far ({distance}m). Falling back to OSM.")
                
                # [Caching] 1. OSM API 호출 전, 우리가 만든 자체 캐시(osm_geocoding_cache) 테이블을 조회합니다.
                if db is not None:
                    try:
                        cache_sql = text("SELECT result_text FROM osm_geocoding_cache WHERE query_type = 'reverse' AND query_key = :key LIMIT 1")
                        cache_hit = db.execute(cache_sql, {"key": wkt_point}).mappings().first()
                        if cache_hit and cache_hit["result_text"]:
                            logger.info(f"OSM Cache hit for reverse '{wkt_point}': {cache_hit['result_text']}")
                            return cache_hit["result_text"]
                    except Exception as ce:
                        logger.warning(f"Cache check failed: {ce}")
                        db.rollback()

                import requests
                import re
                try:
                    # Parse lat/lon from WKT POINT(lon lat)
                    match = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', wkt_point.upper())
                    if match:
                        lon, lat = match.groups()
                        headers = {'User-Agent': 'GeoLLM_Spatial_Agent/1.0'}
                        osm_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                        resp = requests.get(osm_url, headers=headers, timeout=5)
                        if resp.status_code == 200:
                            data = resp.json()
                            if 'display_name' in data:
                                address = data['display_name']
                                # 2차 OSM 검색이 성공하면, 해양 데이터(거리)와 육상 데이터(주소)를 융합하여 반환합니다.
                                result_desc = f"육상 주소: {address} (가장 가까운 해역 '{matched_name}'에서 {distance}m 떨어짐)"
                                
                                # [Caching] 2. 다시 호출하지 않도록 캐시 테이블에 결과를 저장(Cache Save)합니다.
                                try:
                                    insert_sql = text("INSERT INTO osm_geocoding_cache (query_type, query_key, result_text) VALUES ('reverse', :key, :text)")
                                    db.execute(insert_sql, {"key": wkt_point, "text": result_desc})
                                    db.commit()
                                except Exception as ce:
                                    logger.warning(f"Failed to save to OSM cache: {ce}")
                                    db.rollback()
                                    
                                return result_desc
                except Exception as osm_e:
                    logger.error(f"OSM reverse fallback failed: {osm_e}")
            
            # Format the output gracefully for maritime
            if distance < 50:
                desc = f"'{matched_name}' 바로 위 (또는 매우 인접한 해역)"
            else:
                desc = f"'{matched_name}'에서 약 {distance}m 떨어진 해역"
                
            logger.info(f"Reverse geocoding successful: {wkt_point} -> {desc}")
            return desc
        else:
            logger.warning(f"Reverse geocoding failed: No locations found near {wkt_point}. Falling back to OSM.")
            
            # DB가 없거나(result=None) 지명 사전에 없는 경우 OSM 직행
            import requests
            import re
            try:
                # Parse lat/lon from WKT POINT(lon lat)
                match = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', wkt_point.upper())
                if match:
                    lon, lat = match.groups()
                    headers = {'User-Agent': 'GeoLLM_Spatial_Agent/1.0'}
                    osm_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                    resp = requests.get(osm_url, headers=headers, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'display_name' in data:
                            address = data['display_name']
                            result_desc = f"육상 주소: {address}"
                            
                            if db is not None:
                                try:
                                    insert_sql = text("INSERT INTO osm_geocoding_cache (query_type, query_key, result_text) VALUES ('reverse', :key, :text)")
                                    db.execute(insert_sql, {"key": wkt_point, "text": result_desc})
                                    db.commit()
                                except Exception as ce:
                                    logger.warning(f"Failed to save to OSM cache: {ce}")
                                    db.rollback()
                                    
                            return result_desc
            except Exception as osm_e:
                logger.error(f"OSM reverse fallback failed: {osm_e}")
                
            return "근처에 등록된 해양 지명이나 객체가 없습니다."
            
    except Exception as e:
        logger.error(f"Reverse geocoding query failed: {e}")
        return f"ERROR: Failed to perform reverse geocoding: {e}"
    finally:
        if db is not None:
            db.close()
