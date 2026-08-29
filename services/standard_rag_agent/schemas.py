from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class StandardDocumentOutput(BaseModel):
    document_id: str = Field(description="문서 고유 ID")
    title: str = Field(description="문서 제목")
    version: str = Field(description="표준/문서 버전")
    section: str = Field(description="관련 조항/섹션")
    page: str = Field(description="페이지 번호 (예: p.12 또는 N/A)")
    source: str = Field(description="출처 기관 (예: IHO, IMO, 해양수산부)")
    excerpt_reference: str = Field(description="핵심 인용구간 및 규정 설명")
    retrieved_at: str = Field(description="검색된 시간 (ISO 8601 포맷)")
    relevance_score: float = Field(description="0.0 ~ 1.0 사이의 관련성 점수")

class RagAgentResponse(BaseModel):
    documents: List[StandardDocumentOutput] = Field(description="검색된 표준/법령 문서 목록")
    summary: str = Field(description="분석 결과와 규정 연결 (법령 적용 조건 설명)")
