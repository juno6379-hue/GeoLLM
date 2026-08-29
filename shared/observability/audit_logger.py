import json
import logging
from datetime import datetime
from pathlib import Path

# 감사 로그 전용 로거 설정
audit_logger = logging.getLogger("marine_geo.audit")
audit_logger.setLevel(logging.INFO)

# 별도의 파일로 감사 로그 분리 저장
audit_log_path = Path("logs")
audit_log_path.mkdir(exist_ok=True)
fh = logging.FileHandler(audit_log_path / "audit.log", encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
fh.setFormatter(formatter)
audit_logger.addHandler(fh)

def log_data_access(user_id: str, action: str, target: str, clearance_level: str, status: str, details: str = ""):
    """
    사용자의 데이터 접근 시도 및 보안 필터링 결과를 기록하는 Audit Logger.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "action": action,
        "target": target,
        "user_clearance": clearance_level,
        "status": status, # 예: GRANTED, DENIED, FILTERED
        "details": details
    }
    audit_logger.info(json.dumps(log_entry, ensure_ascii=False))
