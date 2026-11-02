# 공간 범위 실행 전 차단 독립 감사 — 2026-11-02

이 문서는 운영 수정 담당자와 별도의 감사 에이전트가 원본 관측·코드·단위검증을 대조한 기록이다. 실제 운영 API 검증은 주검증자가 별도 수행하며, 이 문서의 fixture 결과를 실DB 실행 결과로 대체하지 않는다. 논문 GOLD나 기존 v5 원본은 변경하지 않았다.

## v5 실패의 실제 증거

원본 `research/marine_geollm_scie/runs/20261101_gold_v2_eight_k1_v5/graph/production_rows.jsonl`의 `PILOT_Q5_03`:

- 질의: `Find wrecks within 5 km of Dokdo and explain their S-101 attributes.`
- 최종 상태 `PARTIAL`, 공간 도구 `_fetch_result` 호출, 공간 SQL 제출·완료 1회, 비공간 SQL 11회.
- `execution_attempted`, `execution_started`, `tool_called`, `sql_executed`, `execution_succeeded` 모두 true였다. SQL 성공은 공간 정답 성공이 아니다.
- 실행 QEC는 `feature_search_by_radius`, `EXECUTION_READY`였다. coverage receipt는 `UNKNOWN`, `required=false`, 원천 `GBENC_S101_feature / projection.s101_feature_current`, 사유 `COVERAGE_CONTRACT_UNVERIFIED`였다.

원인은 자료 범위 확인이 일반 반경 검색에서 선택사항이었던 정책이다. UNKNOWN을 경고로 남기면서 실행을 허용했다. 운영 `data/spatial_layer_registry.yaml`에는 현재 승인된 `coverage_contract`가 없다. 따라서 독도가 데이터 범위 밖이라는 연구 판단과 별개로, 운영은 확인되지 않은 범위를 확정해 실행할 근거가 없다.

## 수정 및 교차검증

- 일반 S-101 공간 연산에도 서버가 범위 검증을 요구한다. 요청의 `require_complete_coverage=false` 또는 사전 `ADEQUATE` 표시는 승인 권한이 없다.
- 반경·지도영역 fast path는 `_fetch_result` / `_fetch_bounds_result` 호출 전에 ExecutionValidator를 거친다. 직접 executor 진입에서도 transaction 안의 재검증을 유지한다.
- 이중 검증이 필요한 이유: 연구 observer는 `_fetch_result` 진입 자체를 실행 시도·도구 호출로 기록한다. 내부 SQL만 차단하면 `sql_executed=false`이어도 `execution_attempted=false`를 충족하지 못한다.
- 지도영역 QEC의 기준 geometry를 중심점 대신 전체 polygon으로 전달한다. 중심점 포함만으로 전체 viewport가 수록 범위에 포함된다고 판단해서는 안 된다.
- 최초 수정 중 `REFERENCE_OR_SOURCE_UNRESOLVED` 전체를 범위 검사에서 제외하는 우회를 독립 재현했다. `EPSG:3857` 또는 `POINT(999 999)`가 `EXECUTION_READY`로 통과했다. 이를 수정 담당자에게 전달했고, 현재는 geometry·binding이 존재하면 UNKNOWN을 차단하며 진짜 기준영역 누락의 `NEEDS_USER_INPUT`은 유지한다.

독립 재실행 명령:

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/test_spatial_coverage_gate.py -q --disable-warnings
```

결과: **46 passed (11.00s)**. 작성자의 동일 테스트 실행과 중복 합산하지 않는다. 검증 대상은 미검증 선언·원천/판/Feature 불일치·해시 변조·요청 플래그 우회·승인 receipt 변조·기준영역 누락·preflight 도구 미호출·직접 executor SQL 미실행이다. 정상 승인 테스트는 격리 fixture다.

추가 독립 adversarial probe 6건:

| 입력 조건 | 관측 판정 | 실행 승인 |
|---|---|---|
| EPSG:3857 | BLOCKED_DATA / DATA_COVERAGE_UNVERIFIED | false |
| POINT(999 999) | BLOCKED_DATA / DATA_COVERAGE_UNVERIFIED | false |
| 기준 geometry 없음 | NEEDS_USER_INPUT | false |
| 극지 반경 외접영역 미확정 | BLOCKED_DATA / DATA_COVERAGE_UNVERIFIED | false |
| 날짜변경선 횡단 외접영역 미확정 | BLOCKED_DATA / DATA_COVERAGE_UNVERIFIED | false |
| 자기교차 AOI polygon | NEEDS_USER_INPUT | false |

## 실제 API에서 확인할 조건

1. v5 Q5_03 원문: 공간 미실행·count 미확정·범위 검증 부족 설명. 문서 근거만 제공할 경우 별도 부분 응답이며 실제 Wreck 속성값으로 주장하지 않는다.
2. 독도 등대+Wreck 복합: 공간 하위작업을 일부만 완료 처리하지 않는다.
3. selected area 없는 intersects: 추가입력 요청을 범위 오류로 덮지 않는다.
4. 부산 반경 Wreck: 현재 승인 원천 선언이 없으므로 UNKNOWN 차단도 정상 정책 결과다. 과거 18건 성공을 그대로 회귀 기대값으로 삼지 않는다.
5. S-101 정의 문서 및 원천 지명 조회: 공간 범위 정책이 문서-only 경로나 지명 원천 조회를 무조건 막지 않아야 한다.
6. 미실행은 최종 문구뿐 아니라 QEC·stage·실제 관측을 함께 대조한다. 관측하지 않은 필드를 false로 생성하지 않는다.

## 운영과 논문 실험의 구분 및 제한

- 연구 `prepare_eight_profiles.py`의 부산 snapshot 범위는 `DECLARED_RESEARCH_SNAPSHOT`, `real_world_completeness=false`다. 운영의 전국/부산권 권위 coverage가 아니다. 운영 registry에 복사해 승격하지 않는다.
- 연구 baseline executor는 연구 범위를 검사하지만 운영 P1은 서버 원천 계약을 따른다. 동일 source context 제공과 동일 authority 사용은 다르며 새 실행 보고서에 차이를 명시한다.
- 현재 운영에 승인 coverage가 없어 UNKNOWN 차단은 정상 부산 요청도 제한한다. 이는 자료 준비 미완료이며, 범위 원천 검수·등록을 완료했다는 뜻이 아니다.
- `SchemaBindingAdapter._bind_layer`의 `snapshot_version`은 registry version이다. 향후 승인 선언을 도입할 때 실제 DB snapshot identity와 갱신 lineage를 추가 검증해야 한다. 버전 문자열 일치만으로 실데이터 불변을 주장하지 않는다.
- 이번 범위는 `spatial_coverage.SPATIAL_OPERATIONS`와 S-101 반경/영역 실행 경로다. 사고 공간조회·통항·다른 overlay 등 모든 GeoLLM 연산의 coverage 감사 완료를 뜻하지 않는다.
- GOLD v2 Safe Abstention은 미실행 외에 대상별 차단 상태와 원천 snapshot hash·범위 설명도 요구한다. 운영에서 UNKNOWN을 정확히 차단해도 이 모든 연구 항목을 만족하지 않을 수 있다. 점수를 맞추기 위해 연구 GOLD/hash를 운영 답변에 삽입하지 않는다.
- 최초 확인 시 Windows 연구 Python 프로세스는 없고 v5 status는 `COMPLETED_OBSERVATIONS/DONE`이었다. 초기 Docker 조회는 실패했고 주검증자가 복구했다. 새 실제 API 및 전체 동결 실험 완료는 이 단위 감사 결과와 별도다.

## 실제 운영 API 6건 원본 독립 대조

주검증자가 실행한 `outputs/coverage_preflight_runtime_20261102_v1`의 요약만 보지 않고 6개 원본 JSON의 `completion.final_result`, QEC, coverage receipt, preflight receipt를 각각 읽었다. 모두 SSE 완료 이벤트를 수신했다. 이는 모든 질의의 업무 성공을 뜻하지 않는다. 수집기 기록상 세 운영 소스 hash는 실행 전후 동일했다. 다만 독립 감사 시점에는 `execution_validator.py`가 이미 후속 변경되어 수집 당시 hash와 달랐고 나머지 두 파일만 일치했다. 따라서 아래 API 관측을 후속 수정까지 포함한 최종 코드 검증으로 재사용하지 않는다.

| 사례 | 실제 최종 상태 | 확인 내용 |
|---|---|---|
| v5 Q5_03 원문, 독도 Wreck+속성 | BLOCKED / DATA_COVERAGE_UNVERIFIED | UNKNOWN·required=true, count=null, 실행 전 차단 설명 |
| 독도 5km 침선 | BLOCKED / DATA_COVERAGE_UNVERIFIED | 같은 범위 부족 정책 적용 |
| 부산 지도 기준점 1km 침선 | BLOCKED / DATA_COVERAGE_UNVERIFIED | 부산에도 승인 coverage가 없어 차단; 정상 공간 기능의 가용성 제한 |
| 선택영역 없는 intersects | NEEDS_CLARIFICATION / AOI_REQUIRED | QEC NEEDS_USER_INPUT, execution_status=NOT_RUN 유지 |
| Wreck S-101 정의 | COMPLETED | public_catalogue_document_lookup 승인, FC 2.0.0 원문·locator 반환 |
| 독도 주변 5km 해양지명 | BLOCKED / EXECUTION_GATE | marine_gazetteer 원천도 UNKNOWN 범위 정책에 차단됨 |

첫 세 반경 사례에는 `spatial_preflight.status=BLOCKED_BEFORE_DISPATCH`, `scope=target_spatial_query`와 네 필드 `execution_attempted/execution_started/tool_called/sql_executed=false`가 보존됐다. 실행 전 차단 경로에 기록된 receipt이며, 운영 DB의 모든 SQL을 계측한 전역 관측은 아니다. 기준점 해소·schema 검사의 비공간 SQL까지 미실행이라고 표현하지 않는다. 독립 연구 observer의 새 동결 실행과 별도로 해석한다.

**지명 회귀 비용:** 앞의 정상 대조 계획과 달리 주변 해양지명 조회도 현재 코드에서는 `feature_search_by_radius` 공간 계약으로 검증되고, `serving.marine_gazetteer_current`에 승인 coverage가 없어 차단된다. 이는 새 정책과 일관되지만 이전 Q4 지명 검색 가용성을 낮춘다. 문서-only 정의는 정상 유지됐다고 확인할 수 있으나, 지명 검색까지 회귀가 없다고 주장해서는 안 된다. 지명 원천의 명시적 corpus 조회 계약 또는 검수된 범위 선언이 후속으로 필요하며, 테스트 통과를 위해 client flag로 예외를 주면 안 된다.

Q5_03에서 문서 속성 부분 답변은 이번 원본에 없고 전체 BLOCKED로 종료했다. 공간 미실행 개선과 문서 부분 응답 완성은 구분한다. 지명 사례에는 위 네 필드 receipt가 없으므로 감사에서 소급 생성하지 않았다. 이 사례의 API 응답만으로 동일 계측 수준의 네 필드 false를 주장하지 않는다.

재현 수집기: `scripts/check_coverage_preflight_runtime.py`. 원본 6건을 덮어쓰지 않고 후속 검증은 새 출력 폴더에 기록한다. 새 논문 전체 비교 결과는 아직 이 감사에 포함되지 않는다.

## 최종 소스 API 재검증 v3 — 독립 확인

후속 오류 설명 보완 뒤 `outputs/coverage_preflight_runtime_20261102_v3`를 별도로 대조했다. 감사자는 추가 API나 모델 호출 없이 `verification.json`과 6개 원본을 읽어 SHA-256을 다시 계산했다. **원본 6개 hash 모두 일치**, 수집기의 세 운영 소스 hash도 **현재 디스크와 모두 일치**했다. v1의 후속 소스 변경 제한은 이 v3 관측으로 해소되며, v1 원본은 그대로 보존한다.

- Q5_03 원문·독도 반경·부산 반경: 모두 `BLOCKED / DATA_COVERAGE_UNVERIFIED`, QEC `BLOCKED_DATA`, coverage `UNKNOWN/required=true`, `count=null`. `spatial_preflight` 네 실행 필드 false가 각각 존재한다.
- 선택영역 누락: `NEEDS_CLARIFICATION / AOI_REQUIRED`, QEC `NEEDS_USER_INPUT`, `execution_status=NOT_RUN` 유지.
- S-101 정의: `COMPLETED / public_catalogue_document_lookup`, 문서 실행 승인 유지.
- 주변 지명: 여전히 `BLOCKED_DATA`지만 일반 `EXECUTION_GATE` 대신 `DATA_COVERAGE_UNVERIFIED`를 반환하며, 현재 공간 범위가 검증되지 않았고 검색 결과 0건이라는 의미가 아니라는 설명이 제공된다. 지명 조회 가용성 제한은 해소되지 않았다. 이 경로의 네 필드 preflight receipt는 없으므로 추가로 생성하거나 있다고 보고하지 않는다.

6건의 `passed=true`는 위 정책·응답 계약을 확인한 결과다. 6건 모두 검색 성공, 논문 정확도 100%, 전체 시스템 완성을 뜻하지 않는다. Q5_03 문서 부분 답변, 승인된 운영 coverage 확보, 실제 공간 양성 실행과 신규 동결 논문 전체 비교는 별도 범위로 남는다. 감사 문서 갱신 종료 후 코드나 원본을 변경하지 않았다.
