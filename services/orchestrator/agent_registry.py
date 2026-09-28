import os
import json
import importlib
from typing import Dict, Any, List, Optional, Callable
from shared.observability.logger import get_logger

logger = get_logger("orchestrator.agent_registry")

class AgentRegistry:
    def __init__(self):
        self.registry_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent_registry.json")
        self.agents = self._load_registry()

    def _load_registry(self) -> List[Dict[str, Any]]:
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.error(f"Failed to load agent_registry.json: {e}")
        return []

    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        for agent in self.agents:
            if agent.get("agent_name") == agent_name:
                return agent
        return None

    def validate_agent(self, agent_name: str, user_clearance: int = 1) -> bool:
        """
        에이전트가 레지스트리에 존재하고, 사용자가 실행 권한을 가지는지 검증합니다.
        """
        agent = self.get_agent(agent_name)
        if not agent:
            logger.warning(f"Agent '{agent_name}' not found in registry.")
            return False
            
        required_clearance = agent.get("clearance_level", 1)
        if user_clearance < required_clearance:
            logger.warning(f"Access denied for '{agent_name}'. Required: {required_clearance}, User: {user_clearance}")
            return False
            
        return True

    def find_agent_by_intent(self, intent: str) -> Optional[str]:
        """
        특정 인텐트(의도)를 처리할 수 있는 에이전트의 이름을 반환합니다.
        """
        for agent in self.agents:
            capabilities = agent.get("capabilities", [])
            for cap in capabilities:
                if cap.get("intent") == intent:
                    return agent.get("agent_name")
        return None

    def get_execute_function(self, agent_name: str) -> Optional[Callable]:
        """
        에이전트 이름으로 entry_point를 찾아 동적으로 임포트하여 실행 함수를 반환합니다.
        """
        agent = self.get_agent(agent_name)
        from services.orchestrator.agent_execution_gate import validated_agent, blocked_agent_result
        from services.orchestrator.execution_validator import reject_agent_execution

        async def unavailable(request):
            context = reject_agent_execution(request, agent_name, "registered agent entry point is unavailable")
            return blocked_agent_result(request, agent_name, context)
        if not agent:
            logger.error(f"Agent '{agent_name}' not found for execution.")
            return unavailable
            
        entry_point = agent.get("entry_point")
        if not entry_point:
            logger.error(f"Agent '{agent_name}' has no entry_point defined.")
            return unavailable
            
        try:
            module_path, func_name = entry_point.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            if getattr(func, "__execution_contract_agent__", None) != agent_name:
                func = validated_agent(agent_name)(func)
            return func
        except Exception as e:
            logger.error(f"Failed to dynamically load agent '{agent_name}' at '{entry_point}': {e}")
            return unavailable

registry = AgentRegistry()
