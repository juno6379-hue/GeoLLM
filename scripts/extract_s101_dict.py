import os
import json
from sqlalchemy import create_engine, text
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.database import get_gbenc_url

def main():
    db_url = get_gbenc_url()
    engine = create_engine(db_url)
    
    smart_dict = {}
    
    # 하드코딩 예시와 같은 수동 매핑 추가 (복합 명사 등)
    smart_dict["위험객체"] = {
        "feature_candidates": ["Wreck", "Obstruction", "UnderwaterAwashRock"],
        "routing_hint": "spatial_feature_search",
        "confidence": 1.0,
        "needs_disambiguation": True
    }
    smart_dict["해양보호구역"] = {
        "feature_candidates": ["RestrictedArea", "MarineProtectedArea"],
        "routing_hint": "spatial_feature_search",
        "confidence": 0.95,
        "needs_disambiguation": False
    }
    
    with engine.connect() as conn:
        # 1. primitives 테이블에서 "객체_명_KR" 과 "FEATURE NAME_EN" 매핑
        sql_prim = text('''
            SELECT "객체_명_KR", "FEATURE NAME_EN" 
            FROM primitives 
            WHERE "객체_명_KR" IS NOT NULL AND "FEATURE NAME_EN" IS NOT NULL
        ''')
        
        result = conn.execute(sql_prim)
        for row in result:
            kr_name = row[0].strip()
            en_name = row[1].strip()
            
            # 쉼표나 특수문자 제거 후 공백 제거 (CamelCase 형태 유지)
            clean_en_name = en_name.replace(" ", "")
            
            if kr_name not in smart_dict:
                smart_dict[kr_name] = {
                    "feature_candidates": [],
                    "routing_hint": "spatial_feature_search",
                    "confidence": 0.90,
                    "needs_disambiguation": False
                }
                
            if clean_en_name not in smart_dict[kr_name]["feature_candidates"]:
                smart_dict[kr_name]["feature_candidates"].append(clean_en_name)
                
        # 2. codeinformation 에서 NFTC 코드를 보유한 객체 검증
        sql_code = text("SELECT code, name FROM codeinformation WHERE type = 0")
        result_code = conn.execute(sql_code)
        valid_features = {row[1].lower(): row[0] for row in result_code}
        
        # 3. 데이터 정제 및 confidence/disambiguation 업데이트
        for kr_name, data in list(smart_dict.items()):
            valid_cands = []
            for cand in data["feature_candidates"]:
                if cand.lower() in valid_features or kr_name in ["위험객체", "해양보호구역"]:
                    valid_cands.append(cand)
            
            # 매칭되는 NFTC가 없으면 제거 (또는 confidence 하향)
            if not valid_cands:
                del smart_dict[kr_name]
                continue
                
            smart_dict[kr_name]["feature_candidates"] = list(set(valid_cands))
            
            if len(smart_dict[kr_name]["feature_candidates"]) > 1:
                smart_dict[kr_name]["needs_disambiguation"] = True
                smart_dict[kr_name]["confidence"] = round(0.90 - (len(valid_cands)*0.05), 2)
            else:
                smart_dict[kr_name]["needs_disambiguation"] = False
                smart_dict[kr_name]["confidence"] = 0.98

    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "s101_smart_dictionary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(smart_dict, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully extracted {len(smart_dict)} items to {out_path}")

if __name__ == "__main__":
    main()
