from typing import List, Optional
from shared.schemas.tool import ToolMetadata

# Dummy MVP data for Registry Service
MOCK_TOOLS = [
    ToolMetadata(
        tool_name="postgis.dwithin",
        tool_version="1.0.0",
        capability="Find features within distance",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        security_scope="spatial_read",
        owner="spatial_team",
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z"
    )
]

def get_tools(scope: Optional[str] = None) -> List[ToolMetadata]:
    if scope:
        return [t for t in MOCK_TOOLS if t.security_scope == scope]
    return MOCK_TOOLS

def get_tool_by_name(name: str) -> Optional[ToolMetadata]:
    for t in MOCK_TOOLS:
        if t.tool_name == name:
            return t
    return None
