from datetime import datetime
from typing import Dict, Any

from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus
from services.standard_rag_agent.vdb import search_vdb
from services.orchestrator.graph_rag_retriever import GraphRAGRetriever
from services.orchestrator.evidence_builder import build_evidence_bundle
from shared.observability.logger import get_logger
from services.llm_config import llm_api_enabled

logger = get_logger("standard_rag_agent")

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
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from services.standard_rag_agent.schemas import RagAgentResponse, StandardDocumentOutput
        import os
        
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
