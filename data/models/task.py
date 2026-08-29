import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    organization_id = Column(String, nullable=False)
    original_query = Column(String, nullable=False)
    status = Column(String, nullable=False, default="RECEIVED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="task", cascade="all, delete-orphan")

class TaskEvent(Base):
    __tablename__ = 'task_events'

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('tasks.task_id'), nullable=False)
    previous_state = Column(String, nullable=True)
    next_state = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="events")

class AgentExecution(Base):
    __tablename__ = 'agent_executions'

    execution_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('tasks.task_id'), nullable=False)
    agent_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    result_summary = Column(String, nullable=True)

    task = relationship("Task", back_populates="executions")
