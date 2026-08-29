import csv
import glob
from datetime import datetime

def parse_dms(dms_str):
    if not dms_str: return 'NULL'
    try:
        parts = [p.strip() for p in dms_str.split('|')]
        d = float(parts[0])
        m = float(parts[1]) if len(parts) > 1 else 0
        s = float(parts[2]) if len(parts) > 2 else 0
        return str(d + m/60.0 + s/3600.0)
    except:
        return 'NULL'

def to_int(val):
    try: return str(int(val))
    except: return '0'

def to_float(val):
    try: return str(float(val.replace(',', '')))
    except: return '0.0'

def escape_str(val):
    if not val: return 'NULL'
    return "'" + val.replace("'", "''") + "'"

files = glob.glob('D:/An_GeoLLM/*해상조난사고*.csv')
if not files:
    print('Error: Could not find the accident CSV file.')
    exit(1)

csv_path = files[0]
print('Found CSV:', csv_path)

out_path = 'D:/An_GeoLLM/data/migration/insert_accidents.sql'
count = 0

with open(csv_path, 'r', encoding='cp949', errors='replace') as f, open(out_path, 'w', encoding='utf-8') as out_f:
    reader = csv.reader(f)
    next(reader, None)  # header
    for row in reader:
        if len(row) < 18: continue
        lat = parse_dms(row[5])
        lon = parse_dms(row[6])
        if lat == 'NULL' or lon == 'NULL': continue
        
        try: occ_time = "'" + datetime.strptime(row[0].strip(), '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M:%S') + "'"
        except: occ_time = 'NULL'
        
        month = to_int(row[1])
        time_slot = to_int(row[2])
        jurisdiction = escape_str(row[3].strip())
        sea_area = escape_str(row[4].strip())
        weather = escape_str(row[7].strip())
        cause = escape_str(row[8].strip())
        accident_type = escape_str(row[9].strip())
        ship_count = to_int(row[10])
        people_count = to_int(row[11])
        rescued = to_int(row[12])
        injured = to_int(row[13])
        dead = to_int(row[14])
        missing = to_int(row[15])
        ship_type = escape_str(row[16].strip())
        tonnage = to_float(row[17])
        
        geom = f"ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)"
        
        sql = f"INSERT INTO marine_accidents (occurrence_time, month, time_slot, jurisdiction, sea_area, weather, cause, accident_type, ship_count, people_count, rescued, injured, dead, missing, ship_type, tonnage, geom) VALUES ({occ_time}, {month}, {time_slot}, {jurisdiction}, {sea_area}, {weather}, {cause}, {accident_type}, {ship_count}, {people_count}, {rescued}, {injured}, {dead}, {missing}, {ship_type}, {tonnage}, {geom});\n"
        out_f.write(sql)
        count += 1

print(f'Successfully generated {count} INSERT statements into {out_path}')
