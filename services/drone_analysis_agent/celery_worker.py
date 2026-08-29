import os
from celery import Celery
from services.drone_analysis_agent.agent import DroneLiDARAnalysisAgent
from shared.schemas.agent import AgentRequest

# Redis를 브로커(Broker)와 백엔드(Backend)로 사용하는 Celery 설정
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "drone_lidar_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=2, # 대용량 3D 처리이므로 동시성 제한
)

agent_instance = DroneLiDARAnalysisAgent()

@celery_app.task(bind=True, name="process_drone_lidar_task")
def process_drone_lidar_task(self, request_dict: dict) -> dict:
    """
    비동기로 실행되는 Drone LiDAR 처리 태스크.
    FastAPI(Orchestrator)에서 이 태스크를 호출(.delay() 또는 .apply_async())합니다.
    """
    request = AgentRequest(**request_dict)
    
    # Celery 태스크 상태를 EXECUTING으로 업데이트
    self.update_state(state='EXECUTING', meta={'task_id': request.task_id})
    
    # 1. 에이전트 핵심 로직 실행 (PDAL, AI 등)
    result = agent_instance.process(request)
    
    # 2. Pydantic 모델을 dict로 직렬화하여 반환 (Celery 호환성)
    return result.model_dump(mode="json")
