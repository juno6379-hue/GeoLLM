# RQ3 실행 성공과 공간 정답 분리 계약

2026-11-03. 개발용 연구 진단이다. 운영 코드·DB, 기존 GOLD v2, 홀드아웃은 변경하거나 사용하지 않는다. 독립 인간 검수 완료를 주장하지 않는다.

## 실행 자산과 원천

- 최종 계약: `benchmark/rq3_execution_faults_20261103_v4/contract.json`, manifest와 두 Oracle JSON.
- 실제 실행: `outputs/rq3_execution_faults_20261103_v4/summary.json`, `observations.json`, 000–007 원본 JSON.
- 독립 Oracle는 frozen 2022 해양지명 CSV의 원본 객체 ID와 EWKB를 읽어 Shapely topology / pyproj WGS84 geodesic으로 계산한다. PostgreSQL 실행 결과를 정답 생성에 재사용하지 않는다.
- 독도 기준점 5km는 11개 객체, 명시적 부산 polygon은 4개 객체이다. 부산 polygon은 본 진단에 제공된 영역이며 부산항 공식 항계라고 주장하지 않는다.
- 원천 전체의 source-bound 조회이다. 자료에 없는 객체가 실세계에 없다는 의미가 아니다.
- 원천·profile·snapshot manifest·Oracle·계약·6개 실행/평가 소스의 SHA256 및 Python/Shapely/pyproj 버전을 고정한다. 실제 spatial SQL 앞에는 동일 read-only repeatable-read transaction 안에서 DB 원천 hash/column order guard가 실행된다.

## 고정된 8개 조건

| 원천 조회 | 조건 | 예상 SQL 실행 | 예상 공간 정답 |
|---|---|---|---|
| 독도 5km | clean | 성공 | 11개 원본 객체 |
| 독도 5km | reference 1도 동쪽 이동 | 성공 | 오답 |
| 독도 5km | 거리 5000m를 SQL에서 1000으로 나눔 | 성공 | 오답 |
| 독도 5km | WKT를 EPSG:3857로 잘못 해석 후 4326 변환 | 성공 | 오답 |
| 독도 5km | LIMIT 1001을 1로 변경 | 성공 | 오답 |
| 부산 제공 polygon | clean | 성공 | 4개 원본 객체 |
| 부산 제공 polygon | polygon 1도 동쪽 이동 | 성공 | 오답 |
| 부산 제공 polygon | intersects를 touches로 변경 | 성공 | 오답 |

두 개 독립 source-selection 집단에서 6개 변형을 만든 것이다. 여섯 유형에 대한 일반화 가능한 대규모 정확도 결과가 아니다. `wrong_distance_method`는 현재 단위 적용 오류이다. centroid와 minimum geometry distance 차이는 기존 `outputs/rq3_wrong_executable_20261102_v2`의 별도 SQL 반례로 보존한다. 그 반례를 이 shared-executor 진단이나 8개 방법 비교로 합산하지 않는다.

## 실제 executor와 fault 주입

`FaultDatabase(ObservedDatabase)`는 spatial 단계에서 SQL 본문만 변경한다. 원래 계획과 입력은 변경하지 않고, snapshot guard를 유지한다. metadata SQL에는 적용하지 않는다. 원본/실행 SQL, SQL SHA, 입력 인자와 SHA, 주입 단계, actual DB event를 저장한다. 단일 지정 SQL token이 없으면 임의 치환하지 않고 차단한다.

실제 저장 geometry는 `ST_AsEWKB`로 별도 수집한다. 화면용 GeoJSON 9자리 반올림을 원본 geometry 오류로 판정하지 않는다. 공간 정답은 object set 및 중복, EWKB, 실제 실행 predicate/reference/distance 계약을 함께 확인한다. fault 이름만으로 오답을 결정하지 않는다.

`COMMON_EXECUTOR_DIAGNOSTIC` 결과를 B3/B4/P0/H/P1 결과로 바꿔 부르지 않는다. 실제 방법 비교는 각각의 모델·검토·Validator 경로를 유지한 runner에서 이 DB hook을 주입해야 한다. P1 경로 미연결은 미측정으로 유지한다. 이번 8개 진단과 본래 18질의 8방법 비교는 서로 다른 분모다.

## Table 11 공통 평가

`evaluation/rq3_contract.py`의 `method_table(rows, cases, contract_sha256=...)`는 모든 방법에 같은 case/repeat/eligible 분모를 사용한다. 빠진 행은 제거하지 않고 unknown을 채운다. case query/Oracle/contract hash가 다르면 비교를 거부한다.

- ESR: 실제 spatial SQL 실행 성공 E / 고정 eligible N. HTTP/모델/metadata 성공과 구분한다.
- Spatial Correct: E와 공간 정답 S가 모두 참 / 동일 N. raw S도 별도로 공개한다.
- CGE: 실행 성공 E 중 S의 비율(conditional spatial correctness). ESR−Spatial Correct는 별도의 gap이다.
- SSFR: E 중 S=false 비율. 실행 성공 분모가 0이면 CGE/SSFR는 null이다. 알려지지 않은 실행 성공 여부가 남으면 조건부 비율도 null이다.
- EVQSR: E·S·독립 의미 판정·근거 판정 모두 측정된 경우의 결합값. 일부 미측정이면 null이다. 이번 SQL 진단의 의미/근거 정확도는 미측정이다.
- Paired CI: 동일 case/repeat/query/Oracle/contract와 균형 repeat를 확인하고 equivalence group 단위 paired bootstrap 2,000회(seed 20261103). 차이는 B−A. 정의되지 않는 bootstrap draw를 버리지 않는다. 2개 집단의 CI는 불안정한 개발용 기술통계이며 본 실험의 확증적 CI로 사용하지 않는다.

## 재현 명령

저장소 루트에서 실행한다. 출력 폴더는 반드시 새 경로여야 한다.

```powershell
$env:PYTHONPATH='D:\An_GeoLLM'
.venv/Scripts/python.exe -m pytest research/marine_geollm_scie/tests/test_rq3_execution_faults.py -q
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.rq3_execution_faults --contract research/marine_geollm_scie/benchmark/rq3_execution_faults_20261103_v4 --output outputs/<새_진단폴더>
```

최종 개발 K1에서 전체 코드/profile 동결이 바뀌면 `--prepare-profile <새 profile> --contract <새 계약폴더>`로 새 계약을 만들고 전체 8조건을 실행한다. 원래 v6 profile을 새 K1으로 재라벨하지 않는다.

## 실패 원본 및 수정 검증

- 진단 v1: SQL 성공 8/8, 정상 2건의 ID는 일치했으나 GeoJSON 반올림을 원본 EWKB와 exact 비교해 정상도 오답 판정했다. 원본 및 평가 소스 보존.
- 진단 v2: EWKB 문제는 해결됐지만 실제 executor가 SQL 인자에서 제거한 CRS 필드를 평가기가 요구하여 정상 2건을 오답 판정했다. 실제 SQL SRID 4326 증거로 수정. 원본 및 평가 소스 보존.
- 진단 v3: clean 2/2 공간 정답, fault 6/6 실행 성공·공간 오답 확인.
- 진단 v4: 동일 조건을 평가 의존 소스와 GIS package 버전까지 동결하여 전체 재실행. 최종 summary의 COMPLETED 및 전후 hash 일치를 완료 근거로 사용한다.

단위 테스트는 14개이며 통합 테스트와 중복 합산하지 않는다. 모델 호출은 0회다. 추후 paired method 결과가 없으면 방법 차이/CI를 만들어 넣지 않는다.

## 기본 18질의의 8방법 Table 11 연결

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.report_rq3_methods --observations <새run>/comparison/observations.jsonl --scores <새run>/base_report --benchmark research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1 --output <새run>/rq3_method_report
```

이 별도 보고기는 base_report manifest의 관측·채점·run manifest SHA, frozen benchmark 전체, 각 raw receipt, 채점 소스 hash를 검증하고 실제 raw answer로 공간 채점을 재현한다. 모든 방법의 동일 case/query/repeat/eligibility/equivalence를 확인한다. Oracle identity는 spatial GOLD 및 machine checks를 포함한 사례별 전체 답안 계약의 canonical SHA이다.

출력 `rq3_methods.json` / `table11_KR.md`에는 8방법 ESR, raw spatial, joint spatial, CGE, SSFR, ESR−joint gap, 미측정 EVQSR와 B3 대비 P0/P1 paired CI가 포함된다. CI는 공간 적격 문항만 선택하고 equivalence group으로 resample한다. 공간 정답 판정은 기존 frozen contract의 실제 측정 항목에 한정한다. 측정하지 않은 geometry/relation 기준까지 검증했다고 주장하지 않는다.

별도 SQL fault 8조건을 기본 방법별 성능의 분모에 넣지 않는다. 기존 v6 144개 원본의 읽기 전용 bridge 검증은 `outputs/rq3_methods_bridge_20261103_v1`에 기록했다. 이는 새로운 모델 실험이 아니다. 새 보고기 8개 테스트와 SQL fault 계약 14개 테스트, 총 22개가 통과했다. 기존 v6 P1 실행 성공 0건에서 CGE/SSFR가 null로 보존되는 것을 실제 원본으로 확인했다.
