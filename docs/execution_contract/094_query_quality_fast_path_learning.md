# Query Intent, KG/RAG Quality, and Fast Path Learning Flow

작성일: 2026-09-17

## 목적

GeoLLM 질의 처리는 단순한 fast path 조건문으로만 확장하면 유지보수가 어려워진다. 사용자의 질의 표현은 계속 변하고, Dataset, S-101, AIS/V-PASS, gazetteer, 법령/고시/표준 문서의 연결도 계속 늘어난다. 따라서 각 질의에 대해 다음을 함께 남겨야 한다.

- 어떤 의도로 분류했는가
- 어떤 KG seed, graph path, evidence 후보를 사용했는가
- 의도/KG/evidence 유사도가 어느 정도였는가
- 현재 응답의 정확도는 확정값인가, 추정값인가
- 실패 또는 오분류가 발생했을 때 어떤 학습 항목으로 환류할 것인가

이 문서는 `services/orchestrator/graph.py`, `services/orchestrator/graph_rag_retriever.py`, `services/orchestrator/router.py`, `services/orchestrator/static/index.html`에 반영된 흐름을 설명한다.

## 전체 흐름

1. 사용자가 질의를 입력한다.
2. `parse_intent_node`가 정규화, 빠른 판별식, slot 추출을 수행한다.
3. 특정 질의는 fast path로 즉시 실행 또는 차단된다.
4. 일반 질의는 `graph_rag_node`에서 KG seed, graph path, evidence 후보를 검색한다.
5. `GraphRAGRetriever`가 `quality_metrics`를 산출한다.
6. 실행 결과 또는 차단 결과는 `structured_result.quality_metrics`와 `orchestrator_v2.quality_metrics`를 포함한다.
7. `/api/v1/tasks/stream` compact 응답은 해당 품질 메트릭을 보존한다.
8. 로컬 UI의 핵심 결과 요약 카드가 유사도와 추정 정확도를 표시한다.
9. 품질 경고 또는 차단 상태는 `data/feedback/query_quality_issues.jsonl`에 누적되어 후속 개선 작업의 입력으로 사용된다.

## Fast Path의 역할과 한계

fast path는 다음 경우에 필요하다.

- 이미 authoritative registry, catalogue, Dataset ingestion report에 의해 결정적으로 답할 수 있는 질의
- 공간/통항 분석처럼 준비된 binding이 없으면 임의 결과를 만들면 안 되는 질의
- LLM 또는 vector search를 거치면 느리거나 잘못된 hallucination 가능성이 커지는 질의

하지만 fast path는 조건 조합이 좁아지는 문제가 있다. 예를 들어 `gazetteer`라는 단어가 포함된 질의라도 다음 두 의도가 다를 수 있다.

- "도서지명 gazetteer에서 섬을 찾아줘" -> 공간/gazetteer lookup
- "도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘" -> Dataset provenance/evidence lookup

따라서 fast path는 단순 키워드가 아니라 `대상 + 행위 + 근거/출처/적재/검증 맥락`을 함께 봐야 한다. 2026-09-17 변경에서는 Dataset/gazetteer provenance 질의를 공간 island lookup 차단보다 먼저 평가하도록 조정했다.

## Quality Metrics

`GraphRAGRetriever.retrieve()`는 다음 품질 메트릭을 반환한다.

```json
{
  "intent_similarity": 0.0,
  "kg_similarity": 0.0,
  "evidence_similarity": 0.0,
  "evidence_average_similarity": 0.0,
  "estimated_accuracy": 0.0,
  "confidence_band": "low|medium|high",
  "method": "heuristic_online_query_quality_v1",
  "coverage": {
    "seed_count": 0,
    "related_node_count": 0,
    "graph_path_count": 0,
    "evidence_candidate_count": 0
  }
}
```

각 항목의 의미는 다음과 같다.

- `intent_similarity`: 질의 토큰과 KG seed 또는 context token이 얼마나 맞물렸는지 나타낸다.
- `kg_similarity`: KG에서 관련 node와 graph path가 충분히 연결되었는지 나타낸다.
- `evidence_similarity`: 가장 높은 evidence 후보 match score다.
- `evidence_average_similarity`: evidence 후보 전체의 평균 match score다.
- `estimated_accuracy`: 위 점수들을 조합한 온라인 추정값이다.
- `confidence_band`: `estimated_accuracy` 기반의 high, medium, low 구간이다.

중요: `estimated_accuracy`는 라벨 기반 실측 정확도가 아니다. 사용자가 확인하거나 evidence reviewer가 승인한 ground truth가 쌓이기 전까지는 "추정 정확도"로만 해석해야 한다.

## Fast Path Quality

fast path는 GraphRAG를 거치지 않는 경우가 많다. 그래서 `_quality_metrics_from_state()`가 다음 방식으로 품질 블록을 보강한다.

- GraphRAG context가 있으면 그 `quality_metrics`를 그대로 사용한다.
- deterministic exact route인 경우 `method=deterministic_exact_route_match`로 표시한다.
- 차단 또는 품질 신호가 없는 경우 `method=quality_unavailable`, low band로 표시한다.

예시: Dataset/gazetteer provenance 질의

```json
{
  "intent_similarity": 1.0,
  "kg_similarity": 1.0,
  "evidence_similarity": 1.0,
  "estimated_accuracy": 1.0,
  "confidence_band": "high",
  "method": "deterministic_exact_route_match",
  "fast_path": "dataset_evidence_gazetteer",
  "notes": [
    "Exact fast-path route. Ground-truth accuracy still requires review feedback."
  ]
}
```

이 값은 "현재 규칙이 정확히 매칭되었다"는 뜻이지, 실제 사용자 의도 정확도가 검증 완료되었다는 뜻은 아니다.

## Gazetteer Provenance 사례

문제 질의:

```text
해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘
```

이전 문제:

- `근거` 키워드 때문에 법령/고시/표준 no-evidence fast path로 잘못 라우팅되었다.
- 결과적으로 "법령/고시/표준 항목에서 확정 근거를 찾지 못했다"는 완전히 다른 의미의 답변이 나왔다.

수정 후:

- `gazetteer + 근거/출처/원천/적재/provenance` 조합을 Dataset evidence intent로 판정한다.
- `fast_dataset_evidence_answer_node`가 다음 근거를 반환한다.

| 항목 | 원천 | 적재 테이블 | 건수 |
| --- | --- | --- | --- |
| 해양지명 gazetteer | `Dataset/해양수산부_공동활용체계_해양지명_20221231.csv` | `serving.marine_gazetteer_current` | 1,146 |
| 도서지명 gazetteer | `Dataset/도서지명.zip` | `serving.island_gazetteer_current` | 754 |

근거 산출물:

- `outputs/reports/requested_dataset_layer_ingestion.md`
- `outputs/reports/dataset_embedding_coverage.json`

## UI 노출

`services/orchestrator/static/index.html`의 핵심 결과 요약 카드는 다음을 표시한다.

- 의도: `orchestrator_v2.route_plan.intent`
- 유사도: `quality_metrics.kg_similarity`, 없으면 `intent_similarity` 또는 `evidence_similarity`
- 정확도: `quality_metrics.estimated_accuracy`

기존에는 공간 객체가 있으면 정확도를 임시로 `100.0%`로 표시했다. 이 로직은 제거되었고, 이제 모든 경로가 동일한 품질 메트릭을 사용한다.

## 학습 루프

향후 개선은 다음 루프로 진행한다.

1. 질의, route plan, `quality_metrics`, evidence bundle을 함께 저장한다.
2. 사용자가 "의도가 틀렸다", "근거가 다르다", "지도 표시가 틀렸다"라고 지적하면 해당 질의를 benchmark issue로 등록한다.
3. evidence reviewer가 후보를 승인/반려하면 그 결과를 라벨로 남긴다.
4. 라벨을 기준으로 다음 항목을 조정한다.
   - query normalizer dictionary
   - ontology node/edge
   - GraphRAG evidence candidate scoring
   - fast path 우선순위
   - context resolver scoring weight
5. 같은 질의를 regression test에 추가한다.

## 품질 이슈 로그

다음 상태는 서버 warning 로그와 `data/feedback/query_quality_issues.jsonl`에 함께 기록한다.

- `NO_AUTHORITATIVE_EVIDENCE`
- `BLOCKED_DATA`
- `quality_metrics.method == quality_unavailable`
- `estimated_accuracy < 0.55`
- `kg_similarity < 0.35`
- `evidence_similarity < 0.35`
- `execution_ready == false`이면서 clarification 경로가 아닌 경우

JSONL 레코드 예시는 다음과 같다.

```json
{
  "timestamp": "2026-09-17T11:40:00",
  "task_id": "example-task",
  "query": "사용자 질의",
  "issue_type": "blocked_or_no_evidence_response",
  "severity": "high",
  "route_plan": {},
  "quality_metrics": {},
  "evidence_summary": {},
  "details": {},
  "status": "pending_review"
}
```

이 로그는 장애 로그라기보다 학습용 품질 backlog다. 운영상 예외, 오분류, 품질 저하, 근거 부족, 실행 binding 부족을 한 곳에 모아 다음 ontology/GraphRAG/fast path 개선 작업의 입력으로 삼는다.

## 운영 원칙

- fast path는 속도와 안전장치이며, 학습을 대체하지 않는다.
- 모든 fast path는 `quality_metrics` 또는 그 부재 사유를 반환해야 한다.
- 품질이 낮거나 차단된 질의는 반드시 `query_quality_issues.jsonl`에 남겨 재학습 후보로 검토한다.
- `estimated_accuracy`는 추정값으로 표기하고, 실측 accuracy처럼 사용하지 않는다.
- Dataset provenance, 법령/고시, S-101 표준, 공간 실행, AIS/V-PASS 분석은 서로 다른 evidence domain으로 분리한다.
- "근거 없음" 답변은 마지막 수단이어야 하며, 먼저 질의 domain을 재확인해야 한다.

## 검증 질의

다음 질의는 회귀 검증에 사용한다.

```text
해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘
```

기대:

- `agent_name`: `Data Discovery Agent`
- `analysis_type`: `dataset_evidence_lookup`
- `fast_path`: `dataset_evidence_gazetteer`
- `quality_metrics` 존재
- 답변에 두 원천 파일, 두 serving 테이블, 행 수가 포함됨

```text
S-101 Obstruction definition and DCEG evidence
```

기대:

- `agent_name`: `Standard RAG Agent`
- `analysis_type`: `document_search`
- `quality_metrics` 존재
- S-101 Feature Catalogue 또는 DCEG 근거가 포함됨
