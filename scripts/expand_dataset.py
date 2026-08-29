import os
import json
import random
import uuid

def generate_s101_dataset(count=100):
    kor_names = ["등대", "부표", "정박지", "해저케이블", "해상풍력", "가공선", "항로", "제한구역", "암초", "난파선", "방파제", "항만", "부두", "양식장", "어장"]
    eng_names = ["Light", "Buoy", "AnchorageArea", "CableSubmarine", "OffshorePlatform", "OverheadCable", "NavigationLine", "RestrictedArea", "UnderwaterAwashRock", "Wreck", "Breakwater", "HarbourFacility", "Berth", "MarineFarm", "FishingGround"]
    locations = ["부산항", "인천항", "울산항", "목포항", "제주항", "해양보호구역", "군사제한구역", "정박구역", "여객터미널"]
    distances = [1, 3, 5, 10, 50, 100, 500, 1000]
    units = ["km", "m"]

    dataset = []

    templates = [
        # Knowledge - Feature Mapping (20%)
        {
            "query": "{kor_name}이 S-101에서 무슨 객체야?",
            "intent": "s101_feature_mapping",
            "category": "KNOWLEDGE_SEARCH",
            "slots": lambda args: {"target_term": args["kor_name"]},
            "agent": "Standard RAG Agent"
        },
        {
            "query": "S-101에서 {kor_name}은 어떻게 표기해?",
            "intent": "s101_feature_mapping",
            "category": "KNOWLEDGE_SEARCH",
            "slots": lambda args: {"target_term": args["kor_name"]},
            "agent": "Standard RAG Agent"
        },
        # Knowledge - Rendering Rule (20%)
        {
            "query": "{eng_name}의 렌더링 규칙 설명해줘",
            "intent": "s101_rendering_rule",
            "category": "KNOWLEDGE_SEARCH",
            "slots": lambda args: {"target_feature": args["eng_name"]},
            "agent": "Standard RAG Agent"
        },
        {
            "query": "{eng_name} 객체는 지도에서 어떻게 그려져?",
            "intent": "s101_rendering_rule",
            "category": "KNOWLEDGE_SEARCH",
            "slots": lambda args: {"target_feature": args["eng_name"]},
            "agent": "Standard RAG Agent"
        },
        # Spatial - Proximity (40%)
        {
            "query": "{location} 주변 {distance}{unit} 이내에 있는 {kor_name} 찾아줘",
            "intent": "spatial_proximity_search",
            "category": "SPATIAL_SEARCH",
            "slots": lambda args: {"location": args["location"], "distance_m": args["distance"] if args["unit"]=="m" else args["distance"]*1000, "target_object": args["kor_name"]},
            "agent": "Spatial Analysis Agent"
        },
        {
            "query": "{location} 반경 {distance}{unit} 내의 {eng_name} 분석해봐",
            "intent": "spatial_proximity_search",
            "category": "SPATIAL_SEARCH",
            "slots": lambda args: {"location": args["location"], "distance_m": args["distance"] if args["unit"]=="m" else args["distance"]*1000, "target_object": args["eng_name"]},
            "agent": "Spatial Analysis Agent"
        },
        # Spatial - Overlay (20%)
        {
            "query": "{kor_name}와 {location}이 겹치는 구간 보여줘",
            "intent": "spatial_overlay_intersection",
            "category": "SPATIAL_SEARCH",
            "slots": lambda args: {"target_object_1": args["kor_name"], "target_object_2": args["location"]},
            "agent": "Spatial Analysis Agent"
        },
        {
            "query": "{kor_name}가 {location}과 중첩되는 곳을 분석해",
            "intent": "spatial_overlay_intersection",
            "category": "SPATIAL_SEARCH",
            "slots": lambda args: {"target_object_1": args["kor_name"], "target_object_2": args["location"]},
            "agent": "Spatial Analysis Agent"
        }
    ]

    for i in range(count):
        template = random.choice(templates)
        args = {
            "kor_name": random.choice(kor_names),
            "eng_name": random.choice(eng_names),
            "location": random.choice(locations),
            "distance": random.choice(distances),
            "unit": random.choice(units)
        }
        
        query = template["query"].format(**args)
        slots = template["slots"](args)
        
        item = {
            "query_id": f"Q-AUTO-{uuid.uuid4().hex[:8].upper()}",
            "query": query,
            "category": template["category"],
            "intent": template["intent"],
            "primary_agent": template["agent"],
            "secondary_agents": ["Map Agent"] if template["agent"] == "Spatial Analysis Agent" else [],
            "required_tools": ["postgis.dwithin"] if template["category"] == "SPATIAL_SEARCH" else ["rag.s101_dictionary_search"],
            "required_data": ["GBENC feature"] if template["category"] == "SPATIAL_SEARCH" else ["s101_catalogue"],
            "slots": slots,
            "expected_outputs": ["geojson"] if template["category"] == "SPATIAL_SEARCH" else ["text_summary"],
            "difficulty": "medium"
        }
        dataset.append(item)
        
    return dataset

if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "intent_dataset.json")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    new_data = generate_s101_dataset(100)
    data.extend(new_data)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Added {len(new_data)} items. Total items: {len(data)}")
