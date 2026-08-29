import os
import json
import random
import uuid

def generate_spatial_dataset(count=100):
    targets = ["정박지", "항로", "해상풍력 후보지", "보호구역", "제한구역", "해양시설", "장애물", "위험객체", "등대", "부표", "해저케이블", "가공선", "암초", "난파선", "방파제", "부두"]
    locations = ["부산항 입구", "인천대교 주변", "울산 앞바다", "목포항", "제주항", "해운대", "광안대교", "통영", "여수항", "군산항"]
    distances = [1, 3, 5, 10, 50, 100, 500, 1000, 2000, 3000, 5000]
    units = ["km", "m"]

    dataset = []

    templates = [
        # Proximity (50%)
        {
            "query": "{location} {distance}{unit} 이내 {target} 찾아줘",
            "intent": "spatial_proximity_search",
            "slots": lambda args: {"location": args["location"], "distance_m": args["distance"] if args["unit"]=="m" else args["distance"]*1000, "target_object": args["target"]}
        },
        {
            "query": "{location} 반경 {distance}{unit} 내의 {target} 분석해봐",
            "intent": "spatial_proximity_search",
            "slots": lambda args: {"location": args["location"], "distance_m": args["distance"] if args["unit"]=="m" else args["distance"]*1000, "target_object": args["target"]}
        },
        {
            "query": "{location} 주변 {distance}{unit} 안에 있는 {target} 표시해줘",
            "intent": "spatial_proximity_search",
            "slots": lambda args: {"location": args["location"], "distance_m": args["distance"] if args["unit"]=="m" else args["distance"]*1000, "target_object": args["target"]}
        },
        # Overlay (30%)
        {
            "query": "{target1}와(과) {target2}가 중첩되는 구간 보여줘",
            "intent": "spatial_overlay_intersection",
            "slots": lambda args: {"target_object_1": args["target1"], "target_object_2": args["target2"]}
        },
        {
            "query": "{target1}이 {target2}와 겹치는 곳을 분석해",
            "intent": "spatial_overlay_intersection",
            "slots": lambda args: {"target_object_1": args["target1"], "target_object_2": args["target2"]}
        },
        # Containment (20%)
        {
            "query": "{location} 안에 있는 {target} 찾아줘",
            "intent": "spatial_containment",
            "slots": lambda args: {"base_area": args["location"], "target_object": args["target"]}
        },
        {
            "query": "{target1} 내부에 위치한 {target2} 모두 표시해봐",
            "intent": "spatial_containment",
            "slots": lambda args: {"base_area": args["target1"], "target_object": args["target2"]}
        }
    ]

    for i in range(count):
        template = random.choice(templates)
        args = {
            "target": random.choice(targets),
            "target1": random.choice(targets),
            "target2": random.choice(targets),
            "location": random.choice(locations),
            "distance": random.choice(distances),
            "unit": random.choice(units)
        }
        
        # Avoid same target for target1 and target2
        while args["target1"] == args["target2"]:
            args["target2"] = random.choice(targets)
            
        # Format query and clean up particles
        query = template["query"].format(**args)
        query = query.replace("와(과)", "와" if args["target1"][-1] in "가구류지대부표로선" else "과")
        query = query.replace("이(가)", "가" if args["target2"][-1] in "가구류지대부표로선" else "이")
        
        slots = template["slots"](args)
        
        item = {
            "query_id": f"Q-SPATIAL-AUTO-{uuid.uuid4().hex[:8].upper()}",
            "query": query,
            "category": "SPATIAL_SEARCH",
            "intent": template["intent"],
            "primary_agent": "Spatial Analysis Agent",
            "secondary_agents": ["Map Agent"],
            "required_tools": ["postgis.dwithin"] if template["intent"] == "spatial_proximity_search" else ["postgis.intersection"] if template["intent"] == "spatial_overlay_intersection" else ["postgis.within"],
            "required_data": ["GBENC feature"],
            "slots": slots,
            "expected_outputs": ["geojson", "map_layer"],
            "difficulty": "medium"
        }
        dataset.append(item)
        
    return dataset

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "intent_dataset.json")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    new_data = generate_spatial_dataset(100)
    data.extend(new_data)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Added {len(new_data)} items. Total items: {len(data)}")
