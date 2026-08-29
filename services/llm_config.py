import os


PLACEHOLDER_API_KEYS = {"", "ollama", "dummy", "none", "null", "test"}


def llm_api_enabled() -> bool:
    if os.environ.get("DISABLE_LLM_API", "").lower() in {"1", "true", "yes", "on"}:
        return False

    base_url = os.environ.get("OPENAI_BASE_URL", "").lower()
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434").lower()
    # OPENAI_* is retained only for clients speaking Ollama's local compatibility API.
    return "11434" in base_url or "11434" in ollama_url


def ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/")
