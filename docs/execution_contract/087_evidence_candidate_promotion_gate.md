# Phase 8.7 Evidence 후보 승인 및 KG 승격 Gate

## 목적

Phase 8.5/8.6에서 생성·검색 연결된 evidence 후보를 바로 지식으로 확정하지 않는다. 검토자가 승인한 후보만 `data/evidence_registry.yaml`에 승격하고, KG 재생성 시 승인 evidence만 그래프 관계로 반영한다.

## 원칙

- 기본 decision은 `hold`이다.
- `approved`가 아닌 후보는 registry와 KG에 반영하지 않는다.
- `review_required: true` 후보는 `review_required_accepted: true`가 있어야 승인된다.
- 승인된 후보도 실행 권한을 직접 만들지 않는다.
- 실행은 계속 `QueryExecutionContext -> ExecutionValidator PASS -> Tool 실행 -> EvidenceBundle 반환` 경로를 따른다.

## 산출물

- 검토 템플릿: `outputs/review/evidence_candidate_review_decisions.yaml`
- 승격 registry: `data/evidence_registry.yaml`
- KG 반영: `scripts/build_marine_kg.py`가 `data/evidence_registry.yaml`을 읽어 `EvidenceItem` 노드와 승인 관계를 생성

## 명령

검토 템플릿 생성:

```powershell
python scripts\prepare_evidence_candidate_review.py
```

dry-run 적용:

```powershell
python scripts\apply_approved_evidence_candidates.py
```

승인 항목 registry 반영:

```powershell
python scripts\apply_approved_evidence_candidates.py --write
```

KG 재생성:

```powershell
python scripts\build_marine_kg.py
```

## 검토 YAML 작성 규칙

승인하려는 evidence 항목만 다음 값을 채운다.

- `decision: approved`
- `reviewer`
- `reviewed_at`
- `reason`
- `review_required_accepted: true` 또는 후보가 `review_required: false`

반려 항목은 `decision: rejected`, 보류 항목은 `decision: hold`로 둔다.

## KG 승격 규칙

승인 evidence는 다음 구조로 반영된다.

- `EvidenceItem` 노드 생성
- 후보의 `edge_candidates`를 승인된 KG edge로 생성
- edge에는 `evidence_id`, `review_status`, `verification_status`, `source_ref` provenance를 보존
- `EvidenceItem -> supportsSubject -> subject`
- `EvidenceItem -> supportsObject -> object`

## 다음 보강 지점

- Phase 8.8에서 승인 evidence와 RAG 실제 검색 결과가 충돌하는지 검사한다.
- Phase 8.9에서 승인 evidence를 Graph-RAG ranking의 가중치로 사용하되, 후보 evidence와 승인 evidence를 UI에서 분리 표시한다.
