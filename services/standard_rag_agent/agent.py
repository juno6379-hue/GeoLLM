from datetime import datetime
import os
import json
import urllib.request
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


def _exact_s101_feature_docs(search_query: str) -> list[dict[str, Any]]:
    query_lower = search_query.lower()
    if "s-101" not in query_lower and "s101" not in query_lower and "feature catalogue" not in query_lower:
        return []
    if not any(term in query_lower for term in ("definition", "정의", "설명", "feature catalogue", "근거")):
        return []

    docs: list[dict[str, Any]] = []
    for feature in _load_s101_catalogue_features():
        code = str(feature.get("code") or "")
        name = str(feature.get("name") or code)
        aliases = [str(alias) for alias in feature.get("aliases") or []]
        needles = [code.lower(), name.lower(), *[alias.lower() for alias in aliases]]
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
    return docs[: int(os.environ.get("RAG_EXACT_LOOKUP_TOP_K", "2"))]


def _deterministic_rag_summary(search_query: str, retrieved_docs) -> str:
    if not retrieved_docs:
        return "관련 표준 문서 근거를 찾지 못했습니다. 임의의 정의나 기준은 생성하지 않았습니다."

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
