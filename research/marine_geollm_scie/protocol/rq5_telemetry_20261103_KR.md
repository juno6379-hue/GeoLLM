# RQ5 계측·비용·근거 평가 계약

2026-11-03. 개발 K1의 새로운 144개 관측에 적용한다. 운영 소스·DB·홀드아웃은 변경하지 않는다.

## 실제 수집 범위

- B0–B2: 파일 기반 evidence packet 검색, 모델 호출, 실제 전체 응답 경과시간을 수집한다. 이 검색은 DB를 사용하지 않으므로 SQL 0은 구현 경로상 확인된 값이다.
- B3/B4/P0/H: 분기 시작 전부터 종료까지 `ObservedDatabase.events`를 기록하므로 실행 SQL뿐 아니라 Validator의 snapshot/registry metadata SQL도 포함한다. 차단된 P0/H라도 선행 검증 SQL은 비용에 남는다. 오류로 executor receipt가 없으면 tool-call 수를 0으로 추측하지 않는다.
- SQL count 단위는 query submission이다. 한 read-only transaction에 묶인 snapshot guard, SET, SELECT를 여러 호출로 부풀리지 않는다. 성공 여부·오류·실행 범위는 각 event에 보존한다.
- P1: 연구 전용 ReliabilityObserver의 전체 계측 DBAPI 제출과 논리적인 graph domain operation을 기록한다. baseline의 bounded tool과 P1 graph operation은 단위가 다르므로 scope를 함께 표시한다.
- P1 모델 호출은 연구 proxy의 실제 호출 원본에서 generation/embedding을 분리한다. native Ollama usage와 OpenAI형 usage를 보존한다. 사용량 없는 실패 응답의 token은 null이다. 원래 호출 audit 자체가 없으면 0으로 만들지 않는다.
- baseline retry=0은 caller에 자동 재시도 코드가 없음을 뜻한다. P1은 명시 retry counter를 사용하며 없으면 null이다. proxy identity-check retry는 별도 항목이다.
- baseline human escalation=false는 해당 연구 실행기에 인간 검토 경로가 없다는 뜻이다. P1은 명시적인 최종 검토 요청 상태만 집계한다. 일반 위치/반경 추가입력을 인간 검토로 세지 않는다.

## 공유 호출의 비용

`comparison/rq5_event_ledger.json`에 물리적 generation/review event ID, 원본 call SHA, token, latency, consumer를 기록한다.

- B3 초기 생성은 B3/B4/P0/H 네 방법이 같은 event를 참조한다.
- LLM review는 B4/H가 같은 event를 참조한다.
- standalone: 각 방법을 따로 실행할 때 필요한 공유 호출의 전체 비용을 각각 부담한다.
- allocated: 실제 한 번 수행한 호출의 비용을 consumer 수로 나눈다. 합계는 physical unique-call 비용과 일치한다.
- allocated latency는 작업량 배분이며 응답시간이 아니다. P50/P95는 standalone 실제 경과시간을 사용한다. 공유 generation에는 packet 구성 등 전처리가 포함되고, review callback 및 개별 분기 시간도 포함한다.
- callback 예외로 호출 여부/usage가 불명확하면 알려진 event는 남기되 전체 비용은 incomplete/null이다. 불일치한 payload가 같은 event ID를 주장하면 보고를 거부한다.

## 근거와 정확도 분리

1. 반환 객체별 `object_id + source_snapshot_sha256` 존재율: 구조적 provenance presence일 뿐 원천 hash의 진위나 본문 지지 여부는 아니다.
2. 공통 평가기의 evidence/source/binding machine check: 같은 raw 관측 SHA에 연결된 score report를 받아 별도로 집계한다.
3. 전체 답변 근거 완결성 및 end-to-end provenance correctness: 단순 출처 존재로 완료 처리하지 않는다. 기준이 없는 답변은 미측정으로 남긴다.
4. EVQSR: 동일 공간 적격 cohort에서 semantic, plan validity, execution, spatial, evidence 판정이 모두 있어야 계산한다. 새로운 raw 답변에 독립 의미/근거 판정이 없으면 null이다.
5. False Ready/False Block: 독립 executable GOLD와 실제 Ready 판정이 있어야 계산한다. 통제 fault 집단의 결과는 RQ2 expanded report로 별도 공개하며 기본 18질의에 합산하지 않는다.

## 최종 보고 CLI

```powershell
$env:PYTHONPATH='D:\An_GeoLLM'
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.report_rq5 --observations <새run>/comparison/observations.jsonl --scores <새run>/base_report --output <새run>/rq5_report
```

출력은 `rq5_report.json`, `rq5_report_KR.md`이다. 18×8 공통 case set과 raw receipt hash를 확인한다. JSON에는 비용별 measured/missing, 호출 범위, 고유 event ledger, standalone/allocated 비용, 근거 검사 항목을 남긴다. 부분 cohort에서는 전체율을 null로 유지하고 관측된 비용 분포만 부분표본으로 표시한다.

`--scores`는 report_eight의 폴더를 받아 manifest의 관측 SHA와 scores.jsonl SHA를 검사한다. 또는 `{observations_sha256, rows}` envelope를 받을 수 있다. `--judgments`도 같은 envelope이며 각 행에 이번 raw_artifact_sha256을 요구한다. 이전 답안 채점을 새 답안에 재사용하지 않는다. 보고기는 모델·DB·GOLD·홀드아웃을 읽지 않는다.

## 검증

- `test_rq5_costs.py`: 공유 generation/review 보존 및 배분 합계, telemetry 누락/null, Validator 선행 SQL, 정상 144행 합성 cohort, evidence presence와 correctness 분리, 새 raw hash 결합, legacy SQL count 범위 검증.
- matched branches / 실제 runner 모의 어댑터 / measurement gate / ReliabilityObserver와 함께 29개 테스트 통과. 실제 모델 호출은 하지 않았다.
- 기존 v6의 144개 원본을 읽기 전용으로 재보고한 결과는 `outputs/rq5_integration_probe_20261103_v1/legacy_v6`에 별도로 생성했다. 새 실험 결과가 아니다. 기존 비용 자료에 없는 full SQL/event ledger는 미측정으로 유지했다. 원본 연구 run은 변경하지 않았다.
