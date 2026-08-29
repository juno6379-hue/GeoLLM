import json
with open('D:/An_GeoLLM/data/s101_smart_dictionary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
keywords = ['암', '부표', '방파제', '위험', '부이', '선', '해저', '장애물']
for k, v in data.items():
    if any(w in k for w in keywords):
        print(k, v.get('feature_candidates', []))
