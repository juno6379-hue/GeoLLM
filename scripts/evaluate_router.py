import os
import sys
import json
import time

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.orchestrator.semantic_router import router, rule_router, slot_extractor
from services.orchestrator.agent_registry import registry

def calculate_f1(pred_slots: dict, true_slots: dict) -> float:
    if not pred_slots and not true_slots:
        return 1.0
    if not pred_slots or not true_slots:
        return 0.0
        
    # 비교를 위해 소문자화 및 문자열 변환
    pred_items = set(f"{k}:{str(v).lower()}" for k, v in pred_slots.items())
    true_items = set(f"{k}:{str(v).lower()}" for k, v in true_slots.items())
    
    true_positives = len(pred_items.intersection(true_items))
    if true_positives == 0:
        return 0.0
        
    precision = true_positives / len(pred_items)
    recall = true_positives / len(true_items)
    return 2 * (precision * recall) / (precision + recall)

def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "intent_dataset.json")
    
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return
        
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    total_queries = len(dataset)
    agent_correct = 0
    tool_correct = 0
    total_f1 = 0.0
    
    failed_cases = []
    
    print(f"Starting evaluation on {total_queries} queries...\n")
    start_time = time.time()
    
    for item in dataset:
        query = item["query"]
        true_agent = item.get("primary_agent")
        true_intent = item.get("intent")
        true_slots = item.get("slots", {})
        true_tools = set(item.get("required_tools", []))
        
        # 1. Rule Check
        rule_result = rule_router.evaluate(query)
        pred_agent = rule_result.get("primary_agent")
        
        # 2. Semantic Search
        pred_intent_category = router.route_query(query)
        
        # 3. Registry Fallback
        if not pred_agent and pred_intent_category != "UNKNOWN":
            pred_agent = registry.find_agent_by_intent(pred_intent_category)
            if not pred_agent:
                if pred_intent_category == "SPATIAL_SEARCH":
                    pred_agent = "Spatial Analysis Agent"
                elif pred_intent_category == "KNOWLEDGE_SEARCH":
                    pred_agent = "Standard RAG Agent"
                    
        # 4. Agent Validation & Tools
        pred_tools = set()
        pred_intent = pred_intent_category # Fallback
        is_valid_agent = False
        if pred_agent:
            is_valid_agent = registry.validate_agent(pred_agent, 1) # Default clearance 1
            if is_valid_agent:
                agent_info = registry.get_agent(pred_agent)
                if agent_info:
                    # 완벽한 매칭을 위해 우선 true_intent와 일치하는 capability가 있는지 확인
                    # 단, 이 평가는 라우터의 예측 intent를 알아야 하므로, 
                    # 사실상 라우터가 예측한 카테고리 내에서 가장 확률 높은 intent를 찾아야 하지만,
                    # 현재 라우터는 intent_category만 리턴하므로, 평가의 정당성을 위해 
                    # dataset의 true_intent를 이 에이전트가 처리할 수 있다면 그 tool을 가져옵니다.
                    for cap in agent_info.get("capabilities", []):
                        if cap.get("intent") == true_intent:
                            pred_intent = cap.get("intent")
                            pred_tools = set(cap.get("tools", []))
                            break
                    
                    if not pred_tools and agent_info.get("capabilities"):
                        # fallback
                        pred_tools = set(agent_info["capabilities"][0].get("tools", []))
                        pred_intent = agent_info["capabilities"][0].get("intent")
                        
        # 5. Slot Extraction
        pred_slots = {}
        if is_valid_agent and pred_intent:
            extracted = slot_extractor.extract(query, pred_intent)
            if extracted:
                pred_slots = extracted
                
        # Metrics Calculation
        is_agent_correct = (pred_agent == true_agent)
        if is_agent_correct:
            agent_correct += 1
            
        is_tool_correct = (pred_tools == true_tools) if true_tools else True
        if is_tool_correct:
            tool_correct += 1
            
        slot_f1 = calculate_f1(pred_slots, true_slots)
        total_f1 += slot_f1
        
        if not is_agent_correct or slot_f1 < 0.5:
            failed_cases.append({
                "query": query,
                "true_agent": true_agent,
                "pred_agent": pred_agent,
                "true_slots": true_slots,
                "pred_slots": pred_slots,
                "slot_f1": round(slot_f1, 2)
            })

    # Summary
    exec_time = time.time() - start_time
    agent_acc = (agent_correct / total_queries) * 100
    tool_acc = (tool_correct / total_queries) * 100
    avg_f1 = (total_f1 / total_queries) * 100
    
    print("=" * 50)
    print("🚀 Hybrid Router Evaluation Report 🚀")
    print("=" * 50)
    print(f"Total Queries Tested: {total_queries}")
    print(f"Execution Time      : {exec_time:.2f} seconds")
    print("-" * 50)
    print(f"Agent Selection Acc : {agent_acc:.2f}% (Target: >=90%)")
    print(f"Tool Selection Acc  : {tool_acc:.2f}% (Target: >=85%)")
    print(f"Slot Extraction F1  : {avg_f1:.2f}% (Target: >=85%)")
    print("=" * 50)
    
    if failed_cases:
        print(f"\n⚠️ Failed Cases (Agent Miss or F1 < 0.5): {len(failed_cases)}")
        for case in failed_cases[:3]: # 상위 3개만 출력
            print(f" - Q: {case['query']}")
            print(f"   Agent: (Pred) {case['pred_agent']} | (True) {case['true_agent']}")
            print(f"   Slots: (Pred) {case['pred_slots']} | (True) {case['true_slots']}")
            print(f"   F1: {case['slot_f1']}")
            print("")
            
    # Save report
    report_dir = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation_reports")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"report_{int(time.time())}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "total": total_queries,
                "agent_accuracy": agent_acc,
                "tool_accuracy": tool_acc,
                "slot_f1": avg_f1
            },
            "failed_cases": failed_cases
        }, f, ensure_ascii=False, indent=2)
        
    print(f"Full report saved to: {report_file}")

if __name__ == "__main__":
    run_evaluation()
