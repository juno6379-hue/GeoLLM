# L1/L2/L3 실행 검증 범위 진단

20261030 별도 run에서 **19개 항목 중17개 진단 실행, 2개 NOT_SUPPORTED**를 기록했다. DB·LLM 호출은 없고, 실제 production QEC/ExecutionValidator에 합성 relation 메타데이터만 주입했다. GOLD는0이며 탐지 정확도·실제 GIS 안전성 측정으로 사용할 수 없다. 기존20261029 pilot과 운영코드는 변경하지 않았다. 신규 테스트는4 passed(36.97초)다.

## 관측된 범위

generic `feature_search_by_radius`에서 존재하지 않는 feature 문자열, 잘못된 CRS 문자열, route와 다른 spatial_relation, feature+CRS 복합변형은 이 gate를 통과했다. 이는 **해당 gate에서 검사를 관측하지 못했다**는 뜻이다. 전체 production 경로의 상위 grounding 또는 하위 실행기 검사가 없는 것으로 단정하지 않는다. 사용자의 입력이 실제 이 QEC까지 도달하는지, 하위 실행기가 무엇을 허용하는지는 별도 end-to-end 재현이 필요하다.

단위 원문은 QEC의 정규화된 `distance_m`와 별도 필드로 존재하지 않아 '단위 누락'을 충실히 주입할 수 없다. generic radius의 attribute ownership/CodeList 검사는 별도 source-attribute 경로와 다르므로 이 경량 진단에서는 NOT_SUPPORTED로 남겼다. 임의 필터를 넣고 전체 S-101 속성 검증 실패라고 주장하지 않았다.

관측된 차단에는 잘못된 WKT, relation 누락, 도구 미등록, relation+도구 복합누락, 범위 초과 거리, 권한·schema·relation 변경 후 재검증이 포함된다. 모든 native blocker는 raw에 그대로 있으며 `typed_issues`는 기존 failure_taxonomy 코드로 연구 측에서 분류한 결과다. production이 native typed issue를 제공했다고 표현하지 않는다.

## 승인 이후 변경: 두 종류를 구분

1. **QEC 입력 변경**: 승인 후 distance/CRS/filter를 수정하면 기존 input-hash receipt가 무효화되는지 확인했다. 다시 검증한 이후 통과 여부는 별도 필드이며, CRS/filter 같은 검증 미적용 필드가 재승인되는 것을 기존 receipt 유지와 혼동하지 않는다.
2. **외부 상태 변경**: QEC를 그대로 두고 adapter의 tool registry, SELECT 권한, geometry column, relation 존재 여부를 변경했다. `is_execution_authorized(qec)`는 외부 DB/registry를 읽지 않기 때문에 기존 receipt만으로 변경을 알아내지 않는다. 같은 QEC를 `validate_execution_context`로 **다시 검증하면** tool/권한/schema/relation의 주입된 결함은 차단된다. registry version 문자열만 바꾼 경우에는 의미적 내용이 그대로이므로 차단 여부를 정답 라벨로 정하지 않았다.

두 번째 관측은 TOCTOU 감사 후보이다. 실행 직전 검증 여부·transaction 경계·동일 snapshot 사용 여부가 실제 서비스 경로에서 확인되지 않은 상태이므로 보안 취약점 확정이나 운영 실패로 보고하지 않는다. 다음 검증은 '승인→외부 상태 변경→실제 실행'을 **격리 DB에서** 관측해야 하며 운영 DB 변경은 금지한다.

## 산출물과 재현

- `runs/20261030_fault_coverage/coverage_rows.jsonl`: 전체 입력 QEC, 재검증 결과, 이전 receipt와 재검증 후 판정, 합성 환경
- `runs/20261030_fault_coverage/coverage_summary.json`: 범위·미지원·source hash
- 실행: `.venv\Scripts\python.exe -m research.marine_geollm_scie.fault_injection.coverage_pilot --output-dir <새 결과 경로>`
- 테스트: `.venv\Scripts\python.exe -m pytest research/marine_geollm_scie/tests/test_fault_coverage.py -q`

## 격리 launcher 정정

기존 production 중단 run의 metadata에 있던 '25000-row' 문구는 대략값으로 잘못 고정돼 있었다. 실제 snapshot_manifest의 `subset_rows`는 **25300**, `source_sha256`는 `1300232a3f03d17ea822eeff55fde99c5458b836f86d26bfd445b9afe8bb7f85`다. 이전 metadata를 덮어쓰지 않고 여기 정정하며 향후 launcher는 원본 snapshot_manifest와 hash를 직접 연결한다.

또한 `--env-file`을 쓰지 않는 것만으로 read-only 저장소 안 `.env`의 자동 로드를 막을 수 없다. 향후 launcher는 `/work/.env`를 빈 연구 파일로 덮어 mount하고 PYTHON_DOTENV_DISABLED를 설정한다. 기존 중단 run은 이 추가 파일 차단이 적용되지 않았다. 전용 Docker network는 `docker network inspect ... --format '{{.Internal}}'`에서 **true**를 확인했다. 이 확인은 Docker 격리 설정 증거이며 실제 egress packet 실험을 했다는 뜻은 아니다. 실제 비밀값은 출력하지 않았다. 추가 graph 실행은 하지 않았다.
