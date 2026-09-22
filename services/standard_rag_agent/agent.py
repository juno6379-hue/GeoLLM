from datetime import datetime
import os
import json
import urllib.request
import yaml
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus
from services.standard_rag_agent.vdb import search_vdb
from services.orchestrator.graph_rag_retriever import GraphRAGRetriever
from services.orchestrator.evidence_builder import build_evidence_bundle
from shared.observability.logger import get_logger
from services.llm_config import llm_api_enabled, ollama_base_url

logger = get_logger("standard_rag_agent")
ROOT = Path(__file__).resolve().parents[2]
S101_DCEG_CHUNKS_PATH = ROOT / "outputs" / "rag" / "s101_dceg_chunks.jsonl"
MARINE_TERM_DICTIONARY_PATH = ROOT / "outputs" / "dictionaries" / "marine_term_dictionary.yaml"
S101_FEATURE_QUERY_ALIASES = {
    "AnchorageArea": ["정박지", "정박구역", "투묘지", "anchorage"],
}


def _ollama_fast_response_enabled() -> bool:
    raw = os.environ.get("RAG_FAST_OLLAMA_RESPONSE")
    if raw is not None:
        return raw.lower() in {"1", "true", "yes", "on"}
    return os.environ.get("RAG_SUMMARY_MODE", "deterministic").lower() == "ollama"


def _build_document_outputs(retrieved_docs):
    from services.standard_rag_agent.schemas import StandardDocumentOutput

    docs = []
    for doc in retrieved_docs:
        docs.append(StandardDocumentOutput(
            document_id=doc.get("doc_id", doc.get("chunk_id", "N/A")),
            title=doc.get("title", "N/A"),
            version=doc.get("version", "N/A"),
            section=doc.get("section", "N/A"),
            page=str(doc.get("page", "N/A")),
            source=doc.get("source", doc.get("source_id", doc.get("title", "N/A"))),
            excerpt_reference=doc.get("content", "N/A"),
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            relevance_score=float(doc.get("similarity") or doc.get("score") or 0.0),
        ))
    return docs


@lru_cache(maxsize=1)
def _load_marine_terms() -> dict[str, dict[str, Any]]:
    if not MARINE_TERM_DICTIONARY_PATH.exists():
        return {}
    try:
        data = yaml.safe_load(MARINE_TERM_DICTIONARY_PATH.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        logger.warning("Failed to load marine term dictionary", error=str(exc))
        return {}
    terms = data.get("terms", data) if isinstance(data, dict) else {}
    return {str(key): value for key, value in terms.items() if isinstance(value, dict)}


def _exact_marine_term_docs(search_query: str) -> list[dict[str, Any]]:
    compact_query = "".join(str(search_query or "").split()).rstrip("?")
    for suffix in ("이란", "란", "의뜻", "뜻", "의미", "정의"):
        if compact_query.endswith(suffix):
            compact_query = compact_query[:-len(suffix)]
            break
    if not compact_query:
        return []

    for key, item in _load_marine_terms().items():
        canonical = str(item.get("canonical_term") or key).strip()
        aliases = [str(alias).strip() for alias in item.get("aliases") or []]
        candidates = {"".join(value.split()).lower() for value in [key, canonical, *aliases] if value}
        if compact_query.lower() not in candidates:
            continue
        definitions = [str(value).strip() for value in item.get("definitions") or [] if str(value).strip()]
        if not definitions:
            return []
        definition = definitions[0]
        provenance = item.get("provenance") or {}
        source_path = provenance.get("source_path") or "Dataset/용어사전.xls"
        return [{
            "doc_id": f"marine_term:{canonical}",
            "chunk_id": f"marine_term:{canonical}",
            "title": "해양수산 용어사전",
            "version": "local",
            "content": definition,
            "section": f"용어:{canonical}",
            "page": "N/A",
            "source": source_path,
            "source_id": f"marine_term:{canonical}",
            "similarity": 1.0,
            "metadata": {
                "document_type": "marine_term_dictionary",
                "source_file": source_path,
                "canonical_term": canonical,
                "aliases": aliases,
                "retrieval_method": "exact_marine_term_lookup",
            },
        }]
    return []


@lru_cache(maxsize=1)
def _load_s101_catalogue_features() -> tuple[dict[str, Any], ...]:
    path = ROOT / "data" / "s101_catalogue.json"
    if not path.exists():
        return ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load S-101 catalogue exact lookup", error=str(exc))
        return ()
    values = data.get("features") if isinstance(data, dict) else data
    if not isinstance(values, list):
        values = data.get("feature_types") or data.get("items") or [] if isinstance(data, dict) else []
    return tuple(item for item in values if isinstance(item, dict) and item.get("code"))


@lru_cache(maxsize=1)
def _load_s101_dceg_chunks() -> tuple[dict[str, Any], ...]:
    if not S101_DCEG_CHUNKS_PATH.exists():
        return ()
    rows: list[dict[str, Any]] = []
    try:
        with S101_DCEG_CHUNKS_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception as exc:
        logger.warning("Failed to load S-101 DCEG chunks", error=str(exc))
        return ()
    return tuple(rows)


def _is_s101_dceg_2_0_chunk(row: dict[str, Any]) -> bool:
    metadata = row.get("metadata") or {}
    title = str(metadata.get("title") or "")
    source_file = str(metadata.get("source_file") or "")
    return (
        metadata.get("product_id") == "S-101"
        and metadata.get("document_type") == "dceg"
        and metadata.get("version") == "2.0.0"
        and ("DCEG" in title or "DCEG" in source_file)
    )


def _score_s101_dceg_chunk(row: dict[str, Any], feature: dict[str, Any]) -> int:
    metadata = row.get("metadata") or {}
    text = str(row.get("text") or "")
    lowered = text.lower()
    code = str(feature.get("code") or "")
    name = str(feature.get("name") or code)
    aliases = [str(alias) for alias in feature.get("aliases") or []]
    score = 0
    target_feature_phrase = f"s-101 geo feature: {name.lower()}"
    has_any_geo_feature_table = "s-101 geo feature:" in lowered
    has_target_instruction = (
        "if it is required to encode an anchorage" in lowered
        or f"using the feature {name.lower()}" in lowered
        or f"using an {name.lower()} feature" in lowered
    )
    for term in [code, name, *aliases]:
        if term and term.lower() in lowered:
            score += 20
    related = {str(item).lower() for item in metadata.get("related_features") or []}
    if name.lower() in related or code.lower() in related:
        score += 30
    if target_feature_phrase in lowered:
        score += 200
    elif has_any_geo_feature_table:
        score -= 120
    if "iho definition:" in lowered and target_feature_phrase in lowered:
        score += 60
    if "allowable encoding value" in lowered:
        score += 25
    if "if it is required to encode" in lowered or "remarks:" in lowered:
        score += 60
    if not target_feature_phrase in lowered and not has_target_instruction:
        score -= 80
    if "associated to:" in lowered or "role type role associated with" in lowered:
        score -= 100
    if "................................" in text:
        score -= 40
    return score


def _s101_dceg_docs_for_feature(feature: dict[str, Any], limit: int = 2) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for row in _load_s101_dceg_chunks():
        if not _is_s101_dceg_2_0_chunk(row):
            continue
        score = _score_s101_dceg_chunk(row, feature)
        if score > 0:
            candidates.append((score, row))

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, row in sorted(candidates, key=lambda item: item[0], reverse=True):
        chunk_id = str(row.get("chunk_id") or "")
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        metadata = row.get("metadata") or {}
        selected.append({
            "doc_id": chunk_id,
            "chunk_id": chunk_id,
            "title": metadata.get("title") or "S-101 Annex A DCEG Ed. 2.0.0",
            "version": metadata.get("version") or "2.0.0",
            "content": str(row.get("text") or ""),
            "section": metadata.get("section"),
            "page": metadata.get("page_no"),
            "source": metadata.get("source_id") or "s101_dceg_2_0_0",
            "source_id": metadata.get("source_id"),
            "source_sha256": metadata.get("source_sha256"),
            "similarity": 1.0,
            "metadata": {
                **metadata,
                "document_type": "dceg",
                "standard_type": "S-101",
                "product_id": "S-101",
                "retrieval_method": "exact_dceg_lookup",
            },
        })
        if len(selected) >= limit:
            break
    return selected


def _exact_s101_feature_docs(search_query: str) -> list[dict[str, Any]]:
    query_lower = search_query.lower()
    if "s-101" not in query_lower and "s101" not in query_lower and "feature catalogue" not in query_lower:
        return []
    if not any(term in query_lower for term in ("definition", "encoding", "dceg", "instruction", "guidance", "정의", "설명", "인코딩", "지침", "근거", "feature catalogue")):
        return []

    docs: list[dict[str, Any]] = []
    for feature in _load_s101_catalogue_features():
        code = str(feature.get("code") or "")
        name = str(feature.get("name") or code)
        aliases = [str(alias) for alias in feature.get("aliases") or []]
        query_aliases = S101_FEATURE_QUERY_ALIASES.get(code, [])
        needles = [code.lower(), name.lower(), *[alias.lower() for alias in aliases]]
        needles.extend(str(alias).lower() for alias in query_aliases)
        if not any(needle and needle in query_lower for needle in needles):
            continue

        primitives = feature.get("primitives") or feature.get("permitted_primitives") or []
        definition = str(feature.get("definition") or "").strip()
        content = (
            f"S-101 Feature Catalogue feature definition. "
            f"Feature code: {code}. Feature name: {name}. "
            f"Definition: {definition}. "
            f"Aliases: {', '.join(aliases) if aliases else 'N/A'}. "
            f"Permitted primitives: {', '.join(str(item) for item in primitives) if primitives else 'N/A'}."
        )
        docs.append({
            "doc_id": f"s101_feature_exact_{code.lower()}",
            "title": "S-101 Feature Catalogue 2.0.0",
            "version": "2.0.0",
            "content": content,
            "section": f"feature:{code}",
            "source": "s101_feature_catalogue_v2_xml",
            "source_id": "s101_feature_catalogue_v2_xml",
            "source_sha256": None,
            "similarity": 1.0,
            "metadata": {
                "title": "S-101 Feature Catalogue 2.0.0",
                "version": "2.0.0",
                "section": f"feature:{code}",
                "source_id": "s101_feature_catalogue_v2_xml",
                "source_file": feature.get("source"),
                "document_type": "feature_catalogue",
                "standard_type": "S-101",
                "product_id": "S-101",
                "feature_code": code,
                "feature_name": name,
                "aliases": aliases,
                "permitted_primitives": primitives,
                "retrieval_method": "exact_catalogue_lookup",
            },
        })
        docs.extend(_s101_dceg_docs_for_feature(feature))
    return docs[: int(os.environ.get("RAG_EXACT_LOOKUP_TOP_K", "3"))]


def _deterministic_s101_feature_summary(search_query: str, retrieved_docs) -> str | None:
    feature_doc = next((doc for doc in retrieved_docs if (doc.get("metadata") or {}).get("document_type") == "feature_catalogue"), None)
    dceg_docs = [doc for doc in retrieved_docs if (doc.get("metadata") or {}).get("document_type") == "dceg"]
    if not feature_doc:
        return None
    metadata = feature_doc.get("metadata") or {}
    content = str(feature_doc.get("content") or "")
    definition = ""
    if "Definition: " in content:
        definition = content.split("Definition: ", 1)[1].split(". Aliases:", 1)[0].strip()
    feature_name = metadata.get("feature_name") or metadata.get("feature_code") or "해당 객체"
    summary = (
        f"S-101 Feature Catalogue 2.0.0 기준 {feature_name}의 정의는 \"{definition}\"입니다. "
        f"근거는 Feature Catalogue의 {feature_doc.get('section')} 항목입니다."
    )
    if dceg_docs:
        refs = ", ".join(
            f"{doc.get('title')} / {doc.get('section')}"
            for doc in dceg_docs
            if doc.get("title") and doc.get("section")
        )
        summary += (
            f" 인코딩 지침 근거는 S-101 Annex A DCEG Ed. 2.0.0의 객체별 본문 청크이며, "
            f"참조 위치는 {refs}입니다."
        )
    return summary


def _deterministic_rag_summary(search_query: str, retrieved_docs) -> str:
    if not retrieved_docs:
        return "관련 표준 문서 근거를 찾지 못했습니다. 임의의 정의나 기준은 생성하지 않았습니다."

    exact_summary = _deterministic_s101_feature_summary(search_query, retrieved_docs)
    if exact_summary:
        return exact_summary

    doc = retrieved_docs[0]
    title = doc.get("title") or doc.get("source") or "검색 문서"
    section = doc.get("section") or "section N/A"
    content = " ".join(str(doc.get("content") or "").split())
    if len(content) > 220:
        content = content[:220].rstrip() + "..."
    return (
        f"검색 질의와 관련된 근거 문서 {len(retrieved_docs)}건을 찾았습니다. "
        f"대표 근거는 {title} / {section}이며, 내용 요지는 다음과 같습니다: {content}"
    )


async def _generate_fast_ollama_summary(search_query: str, evidences) -> str:
    model_name = os.environ.get("LLM_MODEL", "gemma2")
    timeout = int(os.environ.get("RAG_FAST_TIMEOUT_SEC", "5"))
    max_tokens = int(os.environ.get("RAG_FAST_MAX_TOKENS", "48"))
    max_chars = int(os.environ.get("RAG_FAST_EVIDENCE_CHARS", "900"))
    context = "\n---\n".join(evidences[: int(os.environ.get("RAG_FAST_CONTEXT_DOCS", "2"))])[:max_chars]
    prompt = (
        "You are a marine standards RAG answer assistant.\n"
        "Use only the evidence below. Answer in Korean in 2 short sentences or less.\n"
        "Do not invent sections, page numbers, or citations.\n\n"
        f"Question: {search_query}\n"
        f"Evidence:\n{context}\n\n"
        "Answer:"
    )
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": max_tokens,
            "num_ctx": int(os.environ.get("RAG_FAST_NUM_CTX", "2048")),
        },
    }
    endpoint = f"{ollama_base_url()}/api/generate"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    return (result.get("response") or "").strip()


def _citation_for_doc(doc: Dict[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
    metadata = doc.get("metadata") or {}
    return {
        "document_id": doc.get("doc_id", doc.get("document_id", "N/A")),
        "source": doc.get("source", doc.get("title", "N/A")),
        "source_id": doc.get("source_id"),
        "source_file": metadata.get("source_file") or metadata.get("source_path"),
        "section": doc.get("section"),
        "document_type": metadata.get("document_type"),
        "chunk_id": doc.get("doc_id", doc.get("chunk_id")),
        "similarity": doc.get("similarity"),
        "provenance": provenance,
    }


def _deterministic_s101_feature_summary(search_query: str, retrieved_docs) -> str | None:
    feature_doc = next((doc for doc in retrieved_docs if (doc.get("metadata") or {}).get("document_type") == "feature_catalogue"), None)
    dceg_docs = [doc for doc in retrieved_docs if (doc.get("metadata") or {}).get("document_type") == "dceg"]
    if not feature_doc:
        return None

    metadata = feature_doc.get("metadata") or {}
    content = str(feature_doc.get("content") or "")
    definition = ""
    if "Definition: " in content:
        definition = content.split("Definition: ", 1)[1].split(". Aliases:", 1)[0].strip()

    feature_name = metadata.get("feature_name") or metadata.get("feature_code") or "해당 객체"
    summary = (
        f"S-101 Feature Catalogue 2.0.0 기준 {feature_name}의 정의는 \"{definition}\"입니다. "
        f"근거는 Feature Catalogue의 {feature_doc.get('section')} 항목입니다."
    )
    if dceg_docs:
        refs = ", ".join(
            f"{doc.get('title')} / {doc.get('section')} / page {doc.get('page') or 'N/A'}"
            for doc in dceg_docs
            if doc.get("title") and doc.get("section")
        )
        summary += (
            f" 인코딩 지침 근거는 S-101 Annex A DCEG Ed. 2.0.0의 객체별 본문 청크에서 확인했으며, "
            f"참조 위치는 {refs}입니다. 긴 원문은 상세정보에서 확인할 수 있습니다."
        )
    return summary


def _deterministic_rag_summary(search_query: str, retrieved_docs) -> str:
    if not retrieved_docs:
        return "관련 표준/문서 근거를 찾지 못했습니다. 확정 근거 없이 조항, 날짜, feature 정의를 생성하지 않습니다."

    exact_summary = _deterministic_s101_feature_summary(search_query, retrieved_docs)
    if exact_summary:
        return exact_summary

    doc = retrieved_docs[0]
    title = doc.get("title") or doc.get("source") or "검색 문서"
    section = doc.get("section") or "section N/A"
    content = " ".join(str(doc.get("content") or doc.get("excerpt_reference") or "").split())
    if len(content) > 220:
        content = content[:220].rstrip() + "..."
    return (
        f"질의와 관련된 근거 문서 {len(retrieved_docs)}건을 찾았습니다. "
        f"대표 근거는 {title} / {section}이며, 내용 요지는 다음과 같습니다: {content}"
    )


def _citation_for_doc(doc: Dict[str, Any], provenance: Dict[str, Any]) -> Dict[str, Any]:
    metadata = doc.get("metadata") or {}
    title = doc.get("title") or doc.get("source") or "검색 문서"
    section = doc.get("section") or metadata.get("section") or "section N/A"
    content = str(doc.get("content") or doc.get("excerpt_reference") or "").strip()
    short_content = " ".join(content.split())
    if len(short_content) > 160:
        short_content = short_content[:160].rstrip() + "..."
    return {
        "document_id": doc.get("doc_id", doc.get("document_id", "N/A")),
        "source": doc.get("source", doc.get("title", "N/A")),
        "source_id": doc.get("source_id"),
        "source_file": metadata.get("source_file") or metadata.get("source_path"),
        "section": doc.get("section"),
        "page": doc.get("page") or metadata.get("page_no"),
        "document_type": metadata.get("document_type") or doc.get("document_type"),
        "chunk_id": doc.get("doc_id", doc.get("chunk_id")),
        "similarity": doc.get("similarity") or doc.get("relevance_score"),
        "summary_ko": f"{title} / {section}: {short_content}" if short_content else f"{title} / {section}",
        "detail_label": "상세정보",
        "detail_text": content,
        "provenance": provenance,
    }


def _apply_compact_evidence_fields(structured_result: Dict[str, Any], graph_result: Dict[str, Any]) -> None:
    evidence_candidates = graph_result.get("evidence_candidates") or {}
    structured_result["evidence_candidate_summary"] = {
        key: len(value) for key, value in evidence_candidates.items() if isinstance(value, list)
    }
    structured_result["kg_provenance_candidates"] = []
    structured_result["rag_evidence_candidates"] = []
    structured_result["regulatory_evidence_candidates"] = []
    structured_result["graph_supported"] = graph_result["graph_supported"]
    structured_result["graph_paths"] = graph_result["graph_paths"][: int(os.environ.get("RAG_GRAPH_PATH_LIMIT", "3"))]
    structured_result["provenance"] = graph_result["provenance"]
    structured_result["rag_filters"] = graph_result["rag_filters"]


def _build_fast_rag_result(
    *,
    request: AgentRequest,
    retrieved_docs,
    evidences,
    graph_result: Dict[str, Any],
    summary: str,
    llm_mode: str,
) -> AgentResult:
    from services.standard_rag_agent.schemas import RagAgentResponse

    fast_docs = _build_document_outputs(retrieved_docs)
    structured_result = RagAgentResponse(
        documents=fast_docs,
        summary=summary,
    ).model_dump()
    structured_result["retrieved_count"] = len(retrieved_docs)
    structured_result["rag_results"] = retrieved_docs
    structured_result["citations"] = [
        _citation_for_doc(doc, graph_result["provenance"])
        for doc in retrieved_docs
    ]
    structured_result["rag_evidence"] = structured_result["citations"]
    structured_result["kg_provenance"] = graph_result["provenance"]
    _apply_compact_evidence_fields(structured_result, graph_result)
    evidence_bundle = build_evidence_bundle(
        graph_context=graph_result,
        structured_result=structured_result,
        task_id=request.task_id,
    )

    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="standard-rag-agent",
        agent_version="2.1.0-fast-rag",
        status=AgentStatus.COMPLETED,
        summary=summary,
        answer_text=summary,
        structured_result=structured_result,
        evidence=evidences[: int(os.environ.get("RAG_RESPONSE_EVIDENCE_LIMIT", "2"))],
        evidence_bundle=evidence_bundle,
        provenance={"search_method": "graph_scoped_vector_search", "top_k": 2, **graph_result["provenance"], "rag_filters": graph_result["rag_filters"], "llm_mode": llm_mode},
        created_at=datetime.utcnow()
    )

async def execute_rag_search(request: AgentRequest) -> AgentResult:
    """
    Standard·RAG Agent Core Logic.
    사용자 질의를 기반으로 Vector DB를 검색하고 근거(Evidence)로 추가합니다.
    """
    logger.info("Starting RAG search", task_id=request.task_id)
    
    # 1. 쿼리 추출 (명시적 Intent 객체가 있으면 사용, 없으면 원본 쿼리 사용)
    search_query = request.original_query
    if request.parsed_intent and request.parsed_intent.target_objects:
        search_query += " " + " ".join(request.parsed_intent.target_objects)
        
    # 2. Vector DB 검색 수행 (실제 DB 연동 코드 호출, 없으면 내부 Fallback)
    graph_context = getattr(request, "graph_context", None) or request.previous_agent_outputs.get("graph_context", {})
    exact_term_docs = _exact_marine_term_docs(request.original_query)
    if exact_term_docs:
        canonical = str((exact_term_docs[0].get("metadata") or {}).get("canonical_term") or "해양 용어")
        summary = f"{canonical}란 {exact_term_docs[0]['content']}"
        graph_result = {
            "graph_supported": True,
            "graph_paths": [],
            "provenance": {
                "method": "exact_marine_term_lookup",
                "query": request.original_query,
                "candidate_document_ids": [exact_term_docs[0]["doc_id"]],
                "evidence_candidate_counts": {},
            },
            "rag_filters": {"document_type": "marine_term_dictionary"},
            "evidence_candidates": {},
        }
        return _build_fast_rag_result(
            request=request,
            retrieved_docs=exact_term_docs,
            evidences=[f"[해양수산 용어사전 - {canonical}] {exact_term_docs[0]['content']}"],
            graph_result=graph_result,
            summary=summary,
            llm_mode="exact_marine_term_lookup",
        )
    exact_docs = _exact_s101_feature_docs(search_query)
    if exact_docs:
        graph_result = {
            "graph_supported": True,
            "graph_paths": [],
            "provenance": {
                "method": "exact_s101_feature_catalogue_lookup",
                "query": search_query,
                "candidate_document_ids": [doc["doc_id"] for doc in exact_docs],
                "evidence_candidate_counts": {},
            },
            "rag_filters": {"product_id": "S-101", "document_type": "feature_catalogue"},
            "evidence_candidates": {},
        }
        evidences = [f"[{doc['title']} v{doc['version']} - {doc['section']}] {doc['content']}" for doc in exact_docs]
        summary = _deterministic_rag_summary(search_query, exact_docs)
        return _build_fast_rag_result(
            request=request,
            retrieved_docs=exact_docs,
            evidences=evidences,
            graph_result=graph_result,
            summary=summary,
            llm_mode="exact_catalogue_lookup",
        )

    graph_result = GraphRAGRetriever().retrieve(search_query, graph_context)
    clearance_level = request.security_context.clearance_level if request.security_context else "PUBLIC"
    retrieved_docs = search_vdb(
        query=search_query, 
        top_k=2,
        user_id=request.user_id,
        clearance_level=clearance_level,
        rag_filters=graph_result["rag_filters"]
    )
    
    # 3. Evidence 및 Provenance 구성 (Raw Text)
    evidences = []
    for doc in retrieved_docs:
        evidence_text = f"[{doc['title']} v{doc['version']} - {doc['section']}] {doc['content']}"
        evidences.append(evidence_text)
        
    structured_result: Dict[str, Any] = {
        "retrieved_count": len(retrieved_docs),
        "rag_results": retrieved_docs,
        "citations": [],
        "graph_supported": graph_result["graph_supported"],
        "graph_paths": graph_result["graph_paths"],
        "provenance": graph_result["provenance"],
        "rag_filters": graph_result["rag_filters"]
    }
    summary = "관련된 표준/법령 문서를 찾지 못했습니다."
    
    if retrieved_docs:
        if os.environ.get("RAG_SUMMARY_MODE", "deterministic").lower() == "deterministic":
            summary = _deterministic_rag_summary(search_query, retrieved_docs)
            return _build_fast_rag_result(
                request=request,
                retrieved_docs=retrieved_docs,
                evidences=evidences,
                graph_result=graph_result,
                summary=summary,
                llm_mode="deterministic_fast_summary",
            )

        if llm_api_enabled() and _ollama_fast_response_enabled():
            from services.standard_rag_agent.schemas import RagAgentResponse

            try:
                fast_docs = _build_document_outputs(retrieved_docs)
                summary = await _generate_fast_ollama_summary(search_query, evidences)
                structured_result = RagAgentResponse(
                    documents=fast_docs,
                    summary=summary,
                ).model_dump()
                structured_result["retrieved_count"] = len(retrieved_docs)
                structured_result["rag_results"] = retrieved_docs
                structured_result["citations"] = [
                    {"document_id": doc.get("doc_id", doc.get("document_id", "N/A")),
                     "source": doc.get("source", doc.get("title", "N/A")),
                     "source_id": doc.get("source_id"),
                     "source_file": (doc.get("metadata") or {}).get("source_file") or (doc.get("metadata") or {}).get("source_path"),
                     "section": doc.get("section"),
                     "document_type": (doc.get("metadata") or {}).get("document_type"),
                     "chunk_id": doc.get("doc_id", doc.get("chunk_id")),
                     "similarity": doc.get("similarity"),
                     "provenance": graph_result["provenance"]}
                    for doc in retrieved_docs
                ]
                structured_result["rag_evidence"] = structured_result["citations"]
                structured_result["kg_provenance"] = graph_result["provenance"]
                evidence_candidates = graph_result.get("evidence_candidates") or {}
                structured_result["kg_provenance_candidates"] = evidence_candidates.get("kg_provenance", [])
                structured_result["rag_evidence_candidates"] = evidence_candidates.get("rag_evidence", [])
                structured_result["regulatory_evidence_candidates"] = evidence_candidates.get("regulatory_evidence", [])
                structured_result["evidence_candidate_summary"] = {
                    key: len(value) for key, value in evidence_candidates.items() if isinstance(value, list)
                }
                structured_result["graph_supported"] = graph_result["graph_supported"]
                structured_result["graph_paths"] = graph_result["graph_paths"]
                structured_result["provenance"] = graph_result["provenance"]
                structured_result["rag_filters"] = graph_result["rag_filters"]
                evidence_bundle = build_evidence_bundle(
                    graph_context=graph_result,
                    structured_result=structured_result,
                    task_id=request.task_id,
                )

                return AgentResult(
                    task_id=request.task_id,
                    trace_id=request.trace_id,
                    agent_name="standard-rag-agent",
                    agent_version="2.0.0-structured",
                    status=AgentStatus.COMPLETED,
                    summary=summary,
                    answer_text=summary,
                    structured_result=structured_result,
                    evidence=evidences,
                    evidence_bundle=evidence_bundle,
                    provenance={"search_method": "graph_scoped_vector_search", "top_k": 2, **graph_result["provenance"], "rag_filters": graph_result["rag_filters"], "llm_mode": "ollama_fast_summary"},
                    created_at=datetime.utcnow()
                )
            except Exception as e:
                logger.warning("Fast Ollama RAG summary unavailable, returning deterministic fast RAG result", error=str(e))
                fast_docs = _build_document_outputs(retrieved_docs)
                summary = _deterministic_rag_summary(search_query, retrieved_docs)
                structured_result = RagAgentResponse(
                    documents=fast_docs,
                    summary=summary,
                ).model_dump()
                structured_result["retrieved_count"] = len(retrieved_docs)
                structured_result["rag_results"] = retrieved_docs
                structured_result["citations"] = [
                    {"document_id": doc.get("doc_id", doc.get("document_id", "N/A")),
                     "source": doc.get("source", doc.get("title", "N/A")),
                     "source_id": doc.get("source_id"),
                     "source_file": (doc.get("metadata") or {}).get("source_file") or (doc.get("metadata") or {}).get("source_path"),
                     "section": doc.get("section"),
                     "document_type": (doc.get("metadata") or {}).get("document_type"),
                     "chunk_id": doc.get("doc_id", doc.get("chunk_id")),
                     "similarity": doc.get("similarity"),
                     "provenance": graph_result["provenance"]}
                    for doc in retrieved_docs
                ]
                structured_result["rag_evidence"] = structured_result["citations"]
                structured_result["kg_provenance"] = graph_result["provenance"]
                evidence_candidates = graph_result.get("evidence_candidates") or {}
                structured_result["kg_provenance_candidates"] = evidence_candidates.get("kg_provenance", [])
                structured_result["rag_evidence_candidates"] = evidence_candidates.get("rag_evidence", [])
                structured_result["regulatory_evidence_candidates"] = evidence_candidates.get("regulatory_evidence", [])
                structured_result["evidence_candidate_summary"] = {
                    key: len(value) for key, value in evidence_candidates.items() if isinstance(value, list)
                }
                structured_result["graph_supported"] = graph_result["graph_supported"]
                structured_result["graph_paths"] = graph_result["graph_paths"]
                structured_result["provenance"] = graph_result["provenance"]
                structured_result["rag_filters"] = graph_result["rag_filters"]
                evidence_bundle = build_evidence_bundle(
                    graph_context=graph_result,
                    structured_result=structured_result,
                    task_id=request.task_id,
                )

                return AgentResult(
                    task_id=request.task_id,
                    trace_id=request.trace_id,
                    agent_name="standard-rag-agent",
                    agent_version="2.0.0-structured",
                    status=AgentStatus.COMPLETED,
                    summary=summary,
                    answer_text=summary,
                    structured_result=structured_result,
                    evidence=evidences,
                    evidence_bundle=evidence_bundle,
                    provenance={"search_method": "graph_scoped_vector_search", "top_k": 2, **graph_result["provenance"], "rag_filters": graph_result["rag_filters"], "llm_mode": "ollama_timeout_deterministic"},
                    created_at=datetime.utcnow()
                )

        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from services.standard_rag_agent.schemas import RagAgentResponse, StandardDocumentOutput
        
        sys_msg = """당신은 해양 표준 및 법령 전문 RAG 에이전트입니다.
사용자의 질의와 아래 제공된 검색 문서(Context)들을 분석하여, 법령 적용 조건 설명과 함께 
반드시 지정된 Pydantic JSON 규격(document_id, title, version, section, page, source, excerpt_reference, retrieved_at, relevance_score)으로 출력하세요.
"""
        context_str = "\n---\n".join(evidences)
        user_msg = f"질의: {search_query}\n검색 문서:\n{context_str}"
        
        try:
            if not llm_api_enabled():
                raise ValueError("No API Key")
            model_name = os.environ.get("LLM_MODEL", "gpt-4o")
            llm = ChatOpenAI(model=model_name, temperature=0)
            structured_llm = llm.with_structured_output(RagAgentResponse)
            llm_result: RagAgentResponse = await structured_llm.ainvoke([
                SystemMessage(content=sys_msg),
                HumanMessage(content=user_msg)
            ])
            structured_result = llm_result.model_dump()
            structured_result["retrieved_count"] = len(retrieved_docs)
            summary = llm_result.summary
        except Exception as e:
            logger.warning("LLM extraction failed (e.g. Quota Exceeded), using Hardcoded Fallback Mock", error=str(e))
            # Fallback (OpenAI 크레딧 초과 시에도 정상 포맷 반환)
            mock_docs = []
            for doc in retrieved_docs:
                mock_docs.append(StandardDocumentOutput(
                    document_id=doc.get("doc_id", "N/A"),
                    title=doc.get("title", "N/A"),
                    version=doc.get("version", "N/A"),
                    section=doc.get("section", "N/A"),
                    page=doc.get("page", "N/A"),
                    source=doc.get("source", "N/A"),
                    excerpt_reference=doc.get("content", "N/A"),
                    retrieved_at=datetime.utcnow().isoformat() + "Z",
                    relevance_score=0.95
                ))
            fallback_res = RagAgentResponse(
                documents=mock_docs,
                summary=f"검색된 {len(mock_docs)}개의 법령/표준 문서에 기반하여 사용자 질문과 일치하는 규정을 확인했습니다. (LLM 크레딧 초과로 인한 텍스트 요약 Fallback 동작중)"
            )
            structured_result = fallback_res.model_dump()
            structured_result["retrieved_count"] = len(retrieved_docs)
            summary = fallback_res.summary
            
    structured_result["rag_results"] = retrieved_docs
    structured_result["citations"] = [
        {"document_id": doc.get("doc_id", doc.get("document_id", "N/A")),
         "source": doc.get("source", doc.get("title", "N/A")),
         "source_id": doc.get("source_id"),
         "source_file": (doc.get("metadata") or {}).get("source_file") or (doc.get("metadata") or {}).get("source_path"),
         "section": doc.get("section"),
         "document_type": (doc.get("metadata") or {}).get("document_type"),
         "chunk_id": doc.get("doc_id", doc.get("chunk_id")),
         "similarity": doc.get("similarity"),
         "provenance": graph_result["provenance"]}
        for doc in retrieved_docs
    ]
    structured_result["rag_evidence"] = structured_result["citations"]
    structured_result["kg_provenance"] = graph_result["provenance"]
    evidence_candidates = graph_result.get("evidence_candidates") or {}
    structured_result["kg_provenance_candidates"] = evidence_candidates.get("kg_provenance", [])
    structured_result["rag_evidence_candidates"] = evidence_candidates.get("rag_evidence", [])
    structured_result["regulatory_evidence_candidates"] = evidence_candidates.get("regulatory_evidence", [])
    structured_result["evidence_candidate_summary"] = {
        key: len(value) for key, value in evidence_candidates.items() if isinstance(value, list)
    }
    structured_result["graph_supported"] = graph_result["graph_supported"]
    structured_result["graph_paths"] = graph_result["graph_paths"]
    structured_result["provenance"] = graph_result["provenance"]
    structured_result["rag_filters"] = graph_result["rag_filters"]
    evidence_bundle = build_evidence_bundle(
        graph_context=graph_result,
        structured_result=structured_result,
        task_id=request.task_id,
    )

    return AgentResult(
        task_id=request.task_id,
        trace_id=request.trace_id,
        agent_name="standard-rag-agent",
        agent_version="2.0.0-structured",
        status=AgentStatus.COMPLETED,
        summary=summary,
        answer_text=summary,
        structured_result=structured_result,
        evidence=evidences,
        evidence_bundle=evidence_bundle,
        provenance={"search_method": "graph_scoped_vector_search", "top_k": 2, **graph_result["provenance"], "rag_filters": graph_result["rag_filters"]},
        created_at=datetime.utcnow()
    )
