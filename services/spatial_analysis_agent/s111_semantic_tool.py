"""S-111 semantic capability requires a verified index with observation provenance."""
from langchain_core.tools import tool

@tool
def search_s111_semantic(query: str) -> dict:
    """Report availability of source-grounded S-111 semantic current search."""
    return {"status": "BLOCKED", "error_code": "S111_SEMANTIC_INDEX_UNAVAILABLE",
            "errors": ["A verified S-111 semantic index with observation time and provenance is not registered."],
            "structured_result": {"data_available": False}}
