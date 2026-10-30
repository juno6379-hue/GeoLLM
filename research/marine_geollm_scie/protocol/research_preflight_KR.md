# 연구 실행 준비 검사

`runners/research_preflight.py`는 논문 평가를 실행하기 전 **로컬 자료와 선언된 계약**을 검사한다. DB 연결·SQL 실행·임베딩·모델 호출·운영 DB 쓰기를 하지 않는다. 기존 Results도 변경하지 않는다. `READY`는 검사에 제공한 범위의 준비 상태이며 논문 점수나 현재 서비스의 성공을 뜻하지 않는다.

## 구분하는 차단점

| 분류 | 검사 | 해석 |
| --- | --- | --- |
| ENVIRONMENT | 파일 존재, 별도 환경 관측 artifact | 환경 미확인/접속 실패를 모델 오류로 집계하지 않음 |
| DATA_PROVENANCE | manifest·원천 SHA256, 캡처 시각·트랜잭션·행 수 | 현재 계산한 해시만 있고 기대 해시가 없으면 UNKNOWN |
| RELATION_SCHEMA | 필요한 관계 및 열과 manifest 선언 대조 | 선언 검사이며 DB 적재·접속 성공 자체는 증명하지 않음 |
| DATABASE_LOAD_OBSERVATION | LOADED_VERIFIED·행 수·COPY 재출력 해시와 원천 대조 | 로더가 기록한 실측 관측이며 현재 DB를 다시 조회하지 않음 |
| COVERAGE | AOI가 snapshot bbox 안에 있는지, 별도 coverage 근거 | bbox 포함만으로 객체군·시점·원천 완전성 확정하지 않음 |
| INPUT_CONTRACT | 사용자가 확정한 검색영역 | 장소 이름이나 기준점만으로 반경/AOI를 만들지 않음 |
| REFERENCE_APPROVAL | 명시적 human approval·GOLD·APPROVED | 사용자 승인 AI보조 참조와 독립 전문가 검수 구분 |
| EVALUATION_CONTRACT | 필요한 semantic/QEC/spatial/evidence 계약 완결성 | 사용자 승인이 미확정 정답 집합을 자동 완성하지 않음 |
| EXECUTION_PROFILE | 임베딩 필수 여부와 활성 여부 | 비활성 프로파일 제약을 모델 오류로 분류하지 않음 |

모든 필수 검사가 PASS일 때만 READY이다. BLOCKED 또는 UNKNOWN이 하나라도 있으면 NOT_READY다. 정상 clarification 여부는 실행 흔적을 평가하는 별도 단계이며 이 준비 검사가 추정하지 않는다.

## 입력 JSON

- `snapshot_manifest: {path, sha256}`와 선택적 `snapshot_data_file`: 기존 단일관계 snapshot 형식을 지원한다.
- 새 묶음 manifest는 `relations: [{relation, columns: [[name,type]], rows, csv_path, sha256}]`, `files: [{path,sha256}]`, `captured_at`, `source_transaction`을 지원한다.
- `csv_path` 상대경로는 manifest 디렉터리 기준이고 files의 경로는 `--root` 기준이다. `expected_db_identity`는 연구 컨테이너·DB와 정확히 일치해야 한다.
- `loaded_verification: [{relation,rows,roundtrip_sha256,content_match}]`를 원천과 대조한다. content_match=true만으로 통과하지 않으며 행 수와 해시도 일치해야 한다.
- `source_files`를 명시하면 manifest files 대신 사용한다. 일부 파일만 주고 전체 자료 검증으로 설명하지 않는다.
- `required_relations: {"schema.table": ["column_a", "geometry"]}`: 실제 실험이 요구하는 관계를 호출자가 지정한다.
- `environment_observation: {status: "AVAILABLE" | "UNAVAILABLE", observed_at, artifact: {path,sha256}}`: 외부 관측 기록 참조이며 실시간 접속을 재확인하지 않는다. artifact 없는 AVAILABLE 선언은 UNKNOWN이다.
- `observations`는 `DB_PROBE`, `GRAPH_NO_LLM`, `RETRIEVAL_COMPONENT`별 manifest와 선택적 rows/integrity_after 파일의 `{path,sha256}`를 받는다. snapshot 참조·DB SQL/결과 해시·검색 결과 행 수/해시를 대조한다. 실행 상태 수와 후보 수만 기록하며 정확도는 추론하지 않는다.
- `profile: {embedding_required: false, embedding_enabled: false}`: 현재 제한 프로파일의 명시적 선택이다.
- `references: {path,sha256}`: 승인 v3 또는 작업 계약 v4 JSONL. v4의 `source_human_approval=true`를 신규 계약의 승인으로 승계하지 않는다. `evaluation_enabled=false`는 차단한다.
- `cases: [{case_id, required_components: ["spatial"], requires_spatial_input: true, aoi_bbox_epsg4326: [minlon,minlat,maxlon,maxlat], coverage_verified, coverage_evidence_sha256}]`.
- 이미 승인된 원형 AOI 등은 `aoi_reference: {path,sha256}`로 참조할 수 있다. 이때 AOI 계약 제공과 bbox 포함 미측정을 분리하며, 원래 확정된 Q4를 미확정 사례로 되돌리지 않는다.

AOI와 coverage는 호출자가 근거를 갖고 명시해야 한다. coverage 해시는 관측 기록 식별자이며 runner가 원천의 의미적 완전성을 재계산하는 것은 아니다. 원천 ID 집합의 정확성, 거리 정답, 통계 검정은 이 runner의 범위 밖이다.

## 실행

```powershell
.\.venv\Scripts\python.exe -m research.marine_geollm_scie.runners.research_preflight --config outputs/preflight_config.json --output-dir outputs/scie_preflight_NEW_RUN --root D:/An_GeoLLM
.\.venv\Scripts\python.exe -m pytest research/marine_geollm_scie/tests/test_research_preflight.py -q
```

출력은 새 디렉터리의 `preflight.json`, `preflight_KR.md`다. 기존 디렉터리로 실행하면 거부하며, 원본 configuration SHA를 기록한다. 자격증명·환경변수·DSN을 요청하거나 출력하지 않는다.

## 2026-10-30 실제 검사

`outputs/scie_preflight_20261030_v1`에 170개 검사를 실행했다. 입력은 `outputs/scie_preflight_inputs_20261030_v1/config.json`이며 최종 LOADED_VERIFIED manifest와 contracts_v4 DRAFT 18건을 고정 해시로 대조했다.

- 원천·manifest·참조 해시 등 DATA_PROVENANCE 37개, 관계·열 5개, COPY 재출력 검산 5개 모두 PASS. 21개 마운트 파일과 5개 CSV를 실제 읽어 해시를 확인했다.
- 신규 v4 작업분해는 원래 v3 승인과 별개이므로 승인 검사18개·평가계약 검사81개 BLOCKED다. 이전 v3 사용자 승인18건을 취소한 것이 아니다.
- 승인된 Q4 원형 AOI artifact 3개는 제공됨으로 표시했다. 그 밖의 공간6개는 이 입력에 AOI가 없으며 coverage도 미확정이다. 문서 적재만으로 검색 성공을 선언하지 않았다.
- 당시 새 graph/API probe가 진행 전이므로 런타임 관측은 UNKNOWN이다. DB 적재 검증 PASS와 분리했다.
- 최종 NOT_READY이며 모델 점수는 생성하지 않았다. 테스트8개 통과. 이후 graph probe 결과는 새 preflight run으로 연결하며 이 기록을 덮어쓰지 않는다.

## 후속 v2: 실제 실행 관측 연결

`outputs/scie_preflight_20261030_v2`는 v1을 보존하고 193개 검사를 수행했다. configuration은 `outputs/scie_preflight_inputs_20261030_v2/config.json`이다. 환경 상태 PASS는 완료된 artifact의 사후 확인이며 기록 시각은 실행 시각으로 바꾸지 않았다.

| 실행 범위 | 관측 | 주장하지 않는 것 |
| --- | --- | --- |
| 연구 DB read-only probe | 5개 SQL·결과 해시 및 snapshot binding 일치, 모델 호출0 | 저장 벡터 self retrieval을 의미 정확도로 해석하지 않음 |
| 격리 graph / noLLM | 6행: COMPLETED2, PARTIAL1, BLOCKED3; 실행 후 원천 무변경 관측 확인 | 반환/COMPLETED를 승인된 전체 의미 성공으로 자동 변환하지 않음 |
| 별도 임베딩 검색 component | bge-m3 1024차원 호출9, 검색9/9 반환, 각 후보3개, 모델 digest 유지 | 후보 반환을 근거 정확도 또는 Full P 성능으로 해석하지 않음 |

provenance54·관측 binding5·관계5·적재검산5·환경1 검사는 PASS다. 저장 벡터의 모델 프로파일 동일성은 UNKNOWN이고, v4 DRAFT 승인18/계약81 차단 및 AOI6/coverage12 미확정은 유지됐다. 따라서 최종 NOT_READY다. 임베딩을 비활성화한 graph와 임베딩을 호출한 별도 검색 실험은 분리했다. 확장 테스트10개가 통과했고 기존 Results/latest는 변경하지 않았다.
