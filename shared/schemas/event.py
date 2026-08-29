from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_id: str
    event_type: str
    task_id: str
    trace_id: str
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload_reference: Optional[str] = None
    status: str = "SUCCESS"

class TaskEvent(BaseEvent):
    pass

class AgentEvent(BaseEvent):
    pass

class ToolEvent(BaseEvent):
    pass

class OutputEvent(BaseEvent):
    pass
