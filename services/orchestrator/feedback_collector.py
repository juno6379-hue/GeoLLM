import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from shared.observability.logger import get_logger

logger = get_logger("orchestrator.feedback_collector")

class FeedbackCollector:
    def __init__(self):
        self.feedback_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "feedback")
        self.feedback_file = os.path.join(self.feedback_dir, "routing_failures.json")
        self._ensure_directory()

    def _ensure_directory(self):
        if not os.path.exists(self.feedback_dir):
            os.makedirs(self.feedback_dir)
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def record_failure(
        self, 
        query: str, 
        predicted_agent: Optional[str] = None, 
        correct_agent: Optional[str] = None,
        failure_reason: str = "Unknown",
        fix: str = "TBD"
    ):
        """
        라우팅 실패 사례를 JSON 파일에 누적합니다.
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "predicted_agent": predicted_agent,
            "correct_agent": correct_agent,
            "failure_reason": failure_reason,
            "fix": fix,
            "status": "pending_review" # pending_review, applied
        }
        
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            data.append(record)
            
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info("Routing failure recorded successfully", query=query, reason=failure_reason)
            
        except Exception as e:
            logger.error("Failed to record routing failure", error=str(e))

    def record_context_feedback(
        self,
        query: str,
        predicted_context: str,
        user_selected_context: str,
        candidate_phrase: str
    ):
        """
        사용자 컨텍스트 수정 피드백을 기록하여 딕셔너리 확장(Dictionary Expansion)에 활용합니다.
        """
        record = {
            "query": query,
            "predicted_context": predicted_context,
            "user_selected_context": user_selected_context,
            "action": "add_to_candidate_dictionary",
            "candidate_phrase": candidate_phrase,
            "recommended_context": user_selected_context,
            "timestamp": datetime.now().isoformat()
        }
        
        context_feedback_file = os.path.join(self.feedback_dir, "context_candidates.jsonl")
        
        try:
            with open(context_feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                
            logger.info(f"Context feedback recorded: '{candidate_phrase}' -> {user_selected_context}")
        except Exception as e:
            logger.error("Failed to record context feedback", error=str(e))

collector = FeedbackCollector()
