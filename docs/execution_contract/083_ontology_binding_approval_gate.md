# Phase 8.3 온톨로지 바인딩 승인 Gate

## 목적

Phase 8.2에서 생성된 자동 제안은 의미 후보일 뿐이다. Phase 8.3은 사람이 검토한 항목만 registry에 병합하는 승인 gate를 제공한다. 이 단계에서도 `execution_status: executable` 자동 승격은 금지한다.

## 파일

- 입력 제안서: `outputs/ontology/ontology_binding_proposals.jsonl`
- 검토 템플릿: `outputs/review/ontology_binding_review_decisions.yaml`
- 병합 대상:
  - `data/spatial_layer_registry.yaml`
  - `data/data_registry.yaml`

## 절차

1. 검토 템플릿 생성

```powershell
python scripts\prepare_ontology_binding_review.py
```

2. 사람이 `outputs/review/ontology_binding_review_decisions.yaml`에서 항목을 검토한다.

허용 decision:

- `hold`: 보류. 기본값이며 병합하지 않는다.
- `rejected`: 반려. 병합하지 않는다.
- `approved`: 승인. `reviewer`, `reviewed_at`, `reason`이 모두 있어야 한다.

3. dry-run으로 병합 결과 확인

```powershell
python scripts\apply_approved_ontology_bindings.py
```

4. 승인 항목만 registry에 반영

```powershell
python scripts\apply_approved_ontology_bindings.py --write
```

## 정책

- 자동 제안은 registry에 직접 병합하지 않는다.
- 승인 파일의 기본 decision은 모두 `hold`이다.
- `approved`가 아닌 항목은 무시한다.
- 승인된 항목도 기본적으로 `executable`이 될 수 없다.
- `executable` 승격은 별도 DB schema 검증, 물리 테이블 확인, ExecutionValidator 통과 후 별도 단계에서만 허용한다.
- 병합 후 KG 재생성과 ontology validator를 통과해야 KG provenance로 사용할 수 있다.

## 다음 단계

Phase 8.4에서는 S-101 Feature Catalogue와 DCEG를 사용해 후보 레이어가 어떤 feature/attribute와 대응되는지 점수화한다. 예를 들어 침선, 장애물, 간출암, 보호수역, 진입제한, 속도제한, AIS/V-PASS 같은 후보를 S-101 feature 및 S-100 제품군과 더 강하게 연결한다.
