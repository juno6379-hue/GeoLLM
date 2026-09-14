# Phase 8.2 구현 현황

## 완료

- `data/ontology_ingestion_rules.yaml`을 추가하여 새 Dataset 자산을 Upper Ontology, 해양수산 업무 도메인, S-100/S-101/S-104/S-111/S-124 제품 후보로 분류하는 규칙을 정의했다.
- `scripts/profile_dataset_for_ontology.py`를 추가하여 파일명, 포맷, 압축 구성, Shapefile 필드, 좌표계 추정, 공간 프로파일을 `outputs/ontology/dataset_profiles.jsonl`로 생성하도록 했다.
- `scripts/propose_ontology_bindings.py`를 추가하여 프로파일 기반 온톨로지 바인딩 후보, registry patch 후보, 검토 큐를 생성하도록 했다.
- 자동 제안은 `CANDIDATE` 또는 `NEEDS_REVIEW`만 생성하며 `execution_status: executable`을 자동 부여하지 않는다.
- KG 계약에 `OntologyIngestionRule`, `OntologyBindingProposal`과 제안 관계를 추가했다. 이 노드는 실행 권한이 아니라 검토 가능한 KG provenance 후보로만 사용한다.
- 상세 설계는 `docs/execution_contract/082_ontology_auto_ingestion_framework.md`에 정리했다.

## 남은 작업

1. 검토 완료 후보를 registry에 병합하는 승인 전용 스크립트를 추가한다.
2. S-101 Feature Catalogue/DCEG feature 및 attribute 매칭 점수를 자동 산출한다.
3. 법령·고시 RAG chunk와 데이터 레이어 간 `authorizedBy`, `definedBy` 후보를 자동 생성한다.
4. QueryExecutionContext의 DataBinding/ToolBinding 후보 생성과 ExecutionValidator gate를 연결한다.
