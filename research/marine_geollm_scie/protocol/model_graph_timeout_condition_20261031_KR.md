# 연구용 semantic prior timeout 조건 — 2026-10-31

기존 v5 graph는 운영 기본 2.5초 timeout을 보존했으나 Qwen 생성 11회가 모두 시간 초과됐다. 기존 결과는 변경하지 않는다. 운영 소스·기본값도 변경하지 않는다.

새 연구 profile에 선택 필드 `semantic_prior_timeout_seconds`를 넣으면 연구 worker에만 `GEOLLM_SEMANTIC_PRIOR_TIMEOUT_SEC`를 전달한다. 허용 범위는 유한한 숫자 2.5~180초다. 생략 시 2.5초로 기존 조건을 보존한다. 문자열·bool·NaN·무한대·범위 초과는 거부한다.

예시 추가 필드:

```json
{"semantic_prior_timeout_seconds": 180}
```

기존 profile의 모델 digest, 완료된 임베딩 증거, snapshot SHA 및 coverage 필드는 모두 유지한 **새 profile 파일**을 만든다. 원본 profile을 수정하면 기존 재현 조건이 깨지므로 금지한다. 기존 v5 graph 출력 디렉터리도 덮어쓰지 않는다.

```text
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.launch_model_graph --output research/marine_geollm_scie/runs/20261031_graph_timeout180_v1/graph --snapshot outputs/scie_model_snapshot_20261030_v3/snapshot_manifest.json --profile research/marine_geollm_scie/runs/20261031_graph_timeout180_v1/model_profile.json
```

위 명령은 새 profile을 작성·검증한 뒤 실행한다. 이 문서 자체는 실행 완료 증거가 아니다.

180초 조건의 방법명은 `P_current_production_model_enabled_restricted_semantic_prior_timeout_180s`이며 manifest와 매 문항 observation에 동일한 `graph_condition`을 기록한다. worker는 실제 환경변수와 profile 일치를 graph import 전에 검사한다. launcher는 연구 runner 파일도 source hash 및 실행 전후 불변 검사에 포함한다.

운영 프롬프트·temperature·모델·일반 호출 예산은 유지하되 semantic prior 시간 제한만 바뀐다. 문항 600초·전체 worker 13,000초 제한은 유지한다. timeout 확대가 성공 응답·올바른 모델 판단·동일 계산예산을 뜻하지 않는다. 원시 `model_calls.jsonl`에서 실제 성공/실패·지연·응답을 다시 검증해야 한다. 프로파일이 다른 기존 baseline과 비교할 때 비용·시간 조건 차이를 명시한다.

검증: timeout 경계·잘못된 값 거부·기본값 보존·환경/profile 불일치 차단 및 기존 profile 연동 회귀 18 passed. 신규 모델 실행은 수행하지 않았다.

## 후속: 첫 180초 run의 초기화 오류와 재검증 조건

위 준비 기록 이후 `20261031_graph_timeout180_v1`은 18문항 관측과 Qwen 11회 HTTP 200을 확보했다. 그러나 import warmup 84호출 중 1건이 모델 identity 사전 조회(`/api/tags`, 10초) 단계에서 URLError로 실패했다. 초기 ContextResolver module singleton의 FAISS 구성 실패 후 graph가 별도로 생성한 두 번째 인스턴스는 성공했다. graph의 경로별로 두 인스턴스를 사용하므로 영향이 없다고 단정하지 않는다.

기존 launcher는 이 warmup 오류를 최종 gate로 확인하지 않아 EXECUTION_OBSERVED를 기록했다. 원본 manifest와 관측은 그대로 유지하고 `graph/warmup_audit_20261031.json`을 별도 추가하여 DEGRADED_WARMUP 판정을 보존했다. 최초 URL 오류의 세부 reason은 기존 로그에 없어 DNS/연결/읽기 단계의 정확한 구분은 미확정이다.

이후 연구 runner는 read-only tags 조회의 transport 오류에 한해 동일 요청을 최대 1회 추가 시도한다(10초 제한, 0.5초 간격). digest 불일치는 즉시 실패하며 우회하지 않는다. 시도별 상태·지연·안전한 예외 종류/errno를 model_calls에 기록하고 URL·비밀값을 담은 예외 원문은 기록하지 않는다. 최종 warmup proxy 오류가 남으면 원시 18행을 보존한 채 launcher는 DEGRADED_WARMUP/nonzero로 종료한다. 실패를 다음 성공으로 삭제하지 않는다.

`data/tool_registry.yaml`도 manifest의 registry SHA 및 실행 전후 source hash 검사에 포함했다. 새 검증은 동일 timeout180 profile의 새 파일·새 output(`20261031_graph_timeout180_v2` 등)을 사용하고 기존 run을 덮지 않는다. 관련 timeout·initialization·profile 회귀 23 passed. 이 추가 보완의 실제 v2 실행은 별도 진행 기록을 따른다.
