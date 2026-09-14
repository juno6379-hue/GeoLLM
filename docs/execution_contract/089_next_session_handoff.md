# 다음 세션 인수인계

## 현재 상태

- Phase 8.8까지 구현됨.
- 통합대시보드에 `Evidence 후보 검토 및 승인 Gate` 패널 추가됨.
- 백엔드 API:
  - `GET /api/v1/evidence-candidates`
  - `GET /api/v1/evidence-candidates/{evidence_id}`
  - `POST /api/v1/evidence-candidates/{evidence_id}/decision`
  - `POST /api/v1/evidence-candidates/apply`
- Docker backend `geollm_backend` 재시작 후 API 확인 완료.
- 현재 evidence 후보:
  - 총 1092건
  - 승인 0건
  - 반려 0건
  - 보류 1092건
- `data/evidence_registry.yaml`은 빈 registry 골격만 있음.
- KG validator 결과:
  - `PASS`
  - nodes 8846
  - edges 9642
  - errors 0
  - warnings 27

## 확인된 실행 URL

- 통합대시보드: `http://localhost:8000`
- backend health: `http://localhost:8000/health`
- evidence 후보 API: `http://localhost:8000/api/v1/evidence-candidates?limit=2`
- S-101 viewer/dev server: `http://localhost:5173`
- portrayal/status backend: `http://localhost:3000/health`

## 다음에 바로 할 일

1. Phase 8.9 시작.
2. 승인 evidence 충돌 검증기 추가.
   - 승인 evidence와 RAG 실제 검색 결과 충돌 확인
   - 승인 evidence와 KG edge/object 존재 여부 확인
   - 승인 evidence와 registry layer/schema 상태 확인
   - 충돌 시 `NEEDS_REVIEW`로 되돌리는 리포트 생성
3. 한글 인코딩 정규화 보강.
   - evidence 후보 JSONL의 mojibake 탐지
   - review YAML의 깨진 한글 필드 탐지
   - UI/API 출력 전 normalizer 또는 원천 산출물 재생성 방식 결정
4. 검토 UI 개선.
   - 긴 후보 목록 pagination
   - 승인 후 registry 병합 결과 표시
   - KG 재생성/validator 실행 버튼 또는 상태 표시

## 검증 명령

```powershell
python -m py_compile services\orchestrator\router.py services\orchestrator\graph_rag_retriever.py services\standard_rag_agent\agent.py services\standard_rag_agent\vdb.py services\orchestrator\evidence_builder.py scripts\prepare_evidence_candidate_review.py scripts\apply_approved_evidence_candidates.py scripts\build_marine_kg.py
python scripts\apply_approved_evidence_candidates.py
python -c "from services.orchestrator.kg_ontology_validator import validate_kg_ontology; r=validate_kg_ontology(); print(r.get('status'), 'nodes=', r.get('node_count'), 'edges=', r.get('edge_count'), 'errors=', len(r.get('errors', [])), 'warnings=', len(r.get('warnings', [])))"
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/evidence-candidates?limit=2" | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/evidence-candidates/apply" -Method Post -ContentType "application/json" -Body '{"write":false,"overwrite":true}' | ConvertTo-Json -Depth 5
```

## 주의사항

- mock fallback은 테스트/명시 허용 환경에서만 허용한다.
- 실행 루트는 계속 `QueryExecutionContext -> ExecutionValidator PASS -> Tool 실행 -> EvidenceBundle 반환`을 강제한다.
- 승인 evidence는 실행 권한이 아니라 KG/RAG/법령 근거 승격이다.
- UI 일부 기존 한글 문자열은 과거 인코딩 문제로 깨져 있으므로 다음 단계에서 정리한다.
