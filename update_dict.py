# -*- coding: utf-8 -*-
import json

file_path = 'D:/An_GeoLLM/data/s101_smart_dictionary.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

if "위험객체" in data:
    # Add new codes
    current = data["위험객체"].get("feature_candidates", [])
    new_features = ["BuoyCardinal", "BuoyLateral", "BuoySpecialPurpose", "BeaconCardinal", "BeaconLateral", "BeaconSpecialPurpose", "ShorelineConstruction", "MarineFarmCulture", "FoulGround"]
    for f in new_features:
        if f not in current:
            current.append(f)
    data["위험객체"]["feature_candidates"] = current

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated s101_smart_dictionary.json")
