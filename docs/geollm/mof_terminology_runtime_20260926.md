# 해수부 순화어의 질의 분석·근거 검수 연결

## 왜 이 단계를 분리했는가

해수부 순화어 자료는 표현 간 관계의 근거다. `잠제 → 수중 방파제`라는 관계에서 S-101 Feature, geometry, 속성 필터나 도구 입력이 자동으로 따라오지는 않는다. 특히 `예선`은 해양 밖에서도 쓰이므로 문자열 발견을 해양 의미 확정으로 취급할 수 없다. 독립 human gold도 아직 없다.

이번 변경은 이전 단계의 오프라인 후보 4개를 실제 질의 분석과 검수 양식에 연결한다. 원문 치환, 도구 선택권 부여, 전체 해양 온톨로지 완성은 이 변경의 결과가 아니다.

## 구현과 근거

- `data/mof_terminology_relations.json`: 해수부 자료 PDF 1쪽의 원문·hash·locator와 순화어 관계 4개를 보존한 재현 가능한 보조 registry. 관계는 `recommended_korean_label`이며 `owl:sameAs` 또는 S-101 매핑으로 저장하지 않는다. 원문 출처는 기존 `mof_reference_inventory_20260926.json`의 `mof_standard_terms_3`이며 원본 hash는 `6ea5be3733130b47e1f8ba0a47c988bb210d094d85fd753b7f0ec5868a984885`다. 현행 고시의 효력은 미확인이다.
- `build_mof_normalization_review.py`: 원문 단위의 text hash/identity를 검사한 뒤 같은 번호의 표 행에서만 대상어·순화어를 묶는다. 기존 180자 이내 검사만으로는 다음 행의 다른 순화어가 연결될 수 있었으므로 행 경계를 추가했다. 이 검사도 의미 검수를 대신하지 않는다.
- `marine_terminology.py`: registry를 프로세스별 한 번 검증하고 질의에서 원문 구간을 기록한다. `^`가 있는 원문의 순화어만 띄어쓰기/붙여쓰기를 허용한다. 조사 뒤 경계를 확인해 `예선전`, `물양장비` 같은 접두부 오인을 줄인다. 모든 후보는 `DOMAIN_SENSE_UNRESOLVED`, `AI_REVIEW_REQUIRED`, `execution_authorized=false`다.
- `korean_query_analysis.py`: `maritime_terminology`에 원문·관계·출처·제외/인용 상태를 제공한다. registry가 없거나 손상되면 `TERMINOLOGY_UNAVAILABLE`을 기록하고 기존 질의 처리는 유지한다.
- `semantic_slot_binding.py`: 순화어 관계를 기존 Feature/KG 입력과 구분한다. 개념 매핑이 없는 활성 후보는 `unresolved_terminology`에 남기고, 실제 후보 중 Feature 입력을 요구하는 capability ID를 함께 기록한다. 그 ID는 필요한 검수 지점을 나타내며 선택·실행된 도구가 아니다. 순화어만으로 Feature 입력을 충족시키지 않는다.
- `export_korean_review_pack.py`: 질의에서 확인한 순화어 관계의 원문 unit을 검수 근거 후보로 연결한다. `reference_bindings`와 human gold는 자동 승인하지 않는다.
- `definition_router.py` / `definition_response.py`: `잠제의 순화어는?`처럼 단일 용어의 순화어를 명시적으로 묻는 요청은 실제 source registry에서 직접 읽는다. 응답은 `terminology_relation_lookup`, 근거 유형은 `source_lexical_relation`이다. 원문 인용·페이지·hash를 반환하며 일반 정의·복합 공간 요청은 이 경로가 처리하지 않는다. 이 조회 완료가 객체 매핑이나 실행용 동의어 승인이라는 뜻은 아니다.

## 실제 실행과 평가 범위

관련 단위 테스트는 순화어 원문 구간, 선택적 띄어쓰기, 동음이의어, 접두부, 다중어 제외, 인용, 다음 표 행 오연결, 원문·인용 변조, 무근거 실행 입력, 보조 자료 누락, 검수 양식 연결을 검사한다. 순화어 직접 조회와 일반 정의·복합 요청의 분리까지 추가한 최종 `test_marine_terminology.py`, `test_reference_evaluation.py`, `test_definition_router.py` 45개 통과. 기존 `test_korean_slot_evidence.py`와 `test_grounded_shadow_metrics.py` 48개 통과(Kiwi 활성). 파일 집합이 서로 다른 93개이며 중간 실행 30개는 합산하지 않는다.

첫 API 실행은 재시작 뒤 30회 readiness 대기 안에 서비스가 준비되지 않아 질의 평가를 시작하지 못했다. 단위/실제 API 병행 초기화가 있었으며 특정 원인으로 확정하지 않는다. 이후 health 200을 확인했다. 검사기에 설정 가능한 120초 기본 대기와 별도 `.readiness.json` 기록을 추가했다. readiness는 질의 정확도와 분리한다. `outputs/korean-intent-shadow/live-mof-terminology-v2.jsonl`은 12/13 계약 통과이며 `잠제의 순화어는?`의 30.204초 관측 timeout을 보존한다. 순화어 직접 조회 수정 후 별도 v3에서 재검증한다.

이번 단계는 신규 Qwen 추론이나 정확도/F1 재측정이 아니다. 기존 1.5B/4B와 혼합 순위의 실험 결과를 그대로 유지하며, 원문 선택·지연 개선 후 새로운 동일 입력 snapshot으로 모델 비교를 진행해야 한다. 의미 accuracy/F1, QLoRA 승격 조건은 아직 충족하지 않았다.

최종 `live-mof-terminology-v3.jsonl`은 13/13 계약 통과다. 순화어 직접 조회는 COMPLETED, `terminology_relation_lookup`, 원문 관계와 `llm_used=false`를 확인했고 관측 시간은 1.012초였다. 이전 timeout과 조건이 완전히 통제된 벤치마크는 아니므로 일반 성능 개선율로 환산하지 않는다. 기존 실제 침선 반경 검색·사고 조회, 정박지 KG 연결과 누락 위치·잘못된 수량·기간 미지원·제외 조건도 회귀 확인했다. v3 readiness는 21.078초이며, 13/13은 계약 통과 수이지 의미 정확도가 아니다.

## 재현과 남은 작업

`PYTHONPATH=/app`인 backend에서 다음과 같이 새 출력 경로로 재생성한다. configs가 마운트되지 않은 컨테이너에서는 해당 seeds를 먼저 컨테이너에 복사한다.

```text
python scripts/build_mof_normalization_review.py --seeds <mof_normalization_review_seeds.json> --reference-index outputs/maritime-reference-index/v3/units.jsonl --output <새 review.jsonl> --bundle <새 registry.json>
python -m pytest tests/unit/test_marine_terminology.py tests/unit/test_reference_evaluation.py tests/unit/test_definition_router.py tests/unit/test_korean_slot_evidence.py tests/unit/test_grounded_shadow_metrics.py -q
python scripts/check_korean_semantic_pipeline.py --output <새 live.jsonl> --readiness-timeout 120
```

남은 핵심은 용어별 의미·적용 범위 검수, FC/DCEG의 객체·속성 조건과 연결한 관계 검수, 승인된 관계의 검색·도구 적용, 독립 gold다. 순화어 사전 확대나 실제 정의 답변 완료를 이번 4개 후보 연결로 대신하지 않는다. 기존 P0 portrayal 산출물·복합 요청·부정 조건 실행도 별도로 남아 있다.
