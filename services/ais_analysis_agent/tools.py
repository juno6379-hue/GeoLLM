import os
import glob
import pandas as pd
from typing import Dict, Any, List, Optional
from shared.observability.logger import get_logger

logger = get_logger("ais_analysis_agent.tools")

def get_ais_data_paths() -> Dict[str, str]:
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "rag_sources", "pdfs")
    
    # 2024 재난체계 정보 (정적/동적 혼합, 선박명, IMO 등)
    # 2022 선박 동적정보 (MMSI 기반 트랙)
    paths = {
        "dynamic_2022": os.path.join(base_dir, "해양수산부_선박 AIS 동적정보_20220101.csv"),
        "static_2024": os.path.join(base_dir, "해양수산부_지능형해양수산재난정보체계_AIS정보_20240220.csv")
    }
    return paths

def search_ais_track(mmsi_or_name: str) -> Dict[str, Any]:
    """
    선박명이나 MMSI를 받아서 해당하는 AIS 항적과 통계를 추출합니다.
    """
    paths = get_ais_data_paths()
    static_path = paths["static_2024"]
    dynamic_path = paths["dynamic_2022"]
    
    mmsi_target = None
    ship_name_target = None
    
    # 숫자형(MMSI)인지 텍스트(선박명)인지 대략적 확인
    if mmsi_or_name.isdigit():
        mmsi_target = mmsi_or_name
    else:
        ship_name_target = mmsi_or_name
        
    try:
        # 1. 선박명으로 검색한 경우 정적 데이터에서 MMSI(선박번호) 찾기
        if ship_name_target and os.path.exists(static_path):
            df_static = pd.read_csv(static_path, encoding='cp949')
            # '선박명' 컬럼에서 찾기
            if '선박명' in df_static.columns:
                matched = df_static[df_static['선박명'].astype(str).str.contains(ship_name_target, na=False)]
                if not matched.empty:
                    mmsi_target = str(matched.iloc[0]['선박번호'])
                    ship_name_target = str(matched.iloc[0]['선박명'])
                    logger.info(f"Resolved ship name '{ship_name_target}' to MMSI '{mmsi_target}'")
        
        # 만약 MMSI를 찾지 못했고 숫자가 아니라면 fallback으로 선박명 자체를 MMSI 자리에 넣어봄
        if not mmsi_target:
            mmsi_target = mmsi_or_name
            
        # 2. 동적 데이터(2022)에서 항적 추출
        if not os.path.exists(dynamic_path):
            return {"error": f"동적 데이터 파일을 찾을 수 없습니다: {dynamic_path}"}
            
        # 성능을 위해 chunk 단위로 읽어서 필터링 (메모리 절약)
        chunksize = 10000
        track_points = []
        
        for chunk in pd.read_csv(dynamic_path, encoding='utf-8', chunksize=chunksize):
            if 'MMSI' in chunk.columns:
                filtered = chunk[chunk['MMSI'].astype(str) == mmsi_target]
                if not filtered.empty:
                    track_points.append(filtered)
                    
        if not track_points:
            # 2022에 없으면 2024에도 있는지 확인 (fallback)
            for chunk in pd.read_csv(static_path, encoding='cp949', chunksize=chunksize):
                if '선박번호' in chunk.columns:
                    filtered = chunk[chunk['선박번호'].astype(str) == mmsi_target]
                    if not filtered.empty:
                        # 컬럼 매핑 맞추기
                        filtered = filtered.rename(columns={'선박번호': 'MMSI', '수신시각': '수신시간', '속도': 'SOG', '선수방위': 'COG'})
                        track_points.append(filtered)
                        
            if not track_points:
                return {"error": f"선박({mmsi_or_name})에 대한 항적 데이터를 찾을 수 없습니다."}
                
        df_track = pd.concat(track_points)
        
        # 수신시간 정렬
        if '수신시간' in df_track.columns:
            df_track = df_track.sort_values(by='수신시간')
            
        # 통계 추출
        stats = {}
        if 'SOG' in df_track.columns:
            stats['avg_speed'] = float(df_track['SOG'].mean())
            stats['max_speed'] = float(df_track['SOG'].max())
            
        # GeoJSON LineString 생성
        # 필수 컬럼: 위도, 경도
        lon_col = '경도'
        lat_col = '위도'
        if '선박길이_좌' in df_track.columns and lon_col not in df_track.columns:
            # 좌표가 없는 경우 처리 불가
            pass
            
        coordinates = []
        if lon_col in df_track.columns and lat_col in df_track.columns:
            for _, row in df_track.iterrows():
                try:
                    lon = float(row[lon_col])
                    lat = float(row[lat_col])
                    coordinates.append([lon, lat])
                except Exception:
                    pass
                    
        geojson = None
        if len(coordinates) >= 2:
            geojson = {
                "type": "Feature",
                "properties": {
                    "mmsi": mmsi_target,
                    "ship_name": ship_name_target or mmsi_target,
                    "avg_speed": stats.get('avg_speed')
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            }
        elif len(coordinates) == 1:
            geojson = {
                "type": "Feature",
                "properties": {
                    "mmsi": mmsi_target,
                    "ship_name": ship_name_target or mmsi_target
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": coordinates[0]
                }
            }
            
        # 상위 100개 포인트를 테이블로 반환 (문맥 제공용)
        df_subset = df_track.head(100)
        table_data = df_subset.to_dict(orient='records')
        
        return {
            "mmsi": mmsi_target,
            "ship_name": ship_name_target,
            "stats": stats,
            "geojson": geojson,
            "point_count": len(df_track),
            "table": table_data
        }
        
    except Exception as e:
        logger.error(f"Failed to process AIS data: {e}", exc_info=True)
        return {"error": f"데이터 분석 중 오류 발생: {str(e)}"}
