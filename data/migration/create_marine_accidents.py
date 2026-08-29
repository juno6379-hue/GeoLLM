import os
import csv
import glob
from sqlalchemy import text
from datetime import datetime
import sys

# Add the parent directory to sys.path so we can import from data.database
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data.database import get_postgis_db

def parse_dms(dms_str):
    """
    해양경찰청 CSV 파일에 들어있는 도분초(DMS) 형식의 문자열(예: '34 | 48 | 9')을 
    컴퓨터가 이해할 수 있는 십진수(DD, Decimal Degrees)로 변환합니다.
    """
    if not dms_str:
        return None
    try:
        parts = [p.strip() for p in dms_str.split('|')]
        d = float(parts[0])
        m = float(parts[1]) if len(parts) > 1 else 0
        s = float(parts[2]) if len(parts) > 2 else 0
        return d + m/60.0 + s/3600.0
    except:
        return None

def migrate_accidents():
    print("Starting marine accidents data migration...")
    files = glob.glob('D:/An_GeoLLM/*해상조난사고*.csv')
    if not files:
        print("Error: Could not find the accident CSV file.")
        return
        
    csv_path = files[0]
    print(f"Found CSV: {csv_path}")
    
    db = next(get_postgis_db())
    
    # 해상조난사고 데이터를 저장할 테이블은 이미 생성되었습니다.
    # 데이터 삽입 시작
    
    insert_sql = text("""
        INSERT INTO marine_accidents (
            occurrence_time, month, time_slot, jurisdiction, sea_area, weather,
            cause, accident_type, ship_count, people_count, rescued, injured,
            dead, missing, ship_type, tonnage, geom
        ) VALUES (
            :occurrence_time, :month, :time_slot, :jurisdiction, :sea_area, :weather,
            :cause, :accident_type, :ship_count, :people_count, :rescued, :injured,
            :dead, :missing, :ship_type, :tonnage,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        )
    """)
    
    count = 0
    skipped = 0
    with open(csv_path, 'r', encoding='cp949', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header
        
        for row in reader:
            if len(row) < 18:
                continue
                
            # Parse coordinates
            lat_dms = row[5]
            lon_dms = row[6]
            lat = parse_dms(lat_dms)
            lon = parse_dms(lon_dms)
            
            if lat is None or lon is None:
                skipped += 1
                continue
                
            # Parse time
            try:
                occ_time = datetime.strptime(row[0].strip(), "%Y-%m-%d %H:%M")
            except:
                occ_time = None
                
            def to_int(val):
                try: return int(val)
                except: return 0
                
            def to_float(val):
                try: return float(val.replace(',', ''))
                except: return 0.0
    
            params = {
                "occurrence_time": occ_time,
                "month": to_int(row[1]),
                "time_slot": to_int(row[2]),
                "jurisdiction": row[3].strip(),
                "sea_area": row[4].strip(),
                "weather": row[7].strip(),
                "cause": row[8].strip(),
                "accident_type": row[9].strip(),
                "ship_count": to_int(row[10]),
                "people_count": to_int(row[11]),
                "rescued": to_int(row[12]),
                "injured": to_int(row[13]),
                "dead": to_int(row[14]),
                "missing": to_int(row[15]),
                "ship_type": row[16].strip(),
                "tonnage": to_float(row[17]),
                "lon": lon,
                "lat": lat
            }
            
            db.execute(insert_sql, params)
            count += 1
            
            if count % 1000 == 0:
                db.commit()
                print(f"Inserted {count} records...")
                
    db.commit()
    
    # 공간 인덱스(GIST) 생성은 psql로 완료함
    
    print(f"Migration completed successfully! Inserted {count} records (Skipped {skipped} missing coordinates).")
    
    db.close()

if __name__ == "__main__":
    migrate_accidents()
