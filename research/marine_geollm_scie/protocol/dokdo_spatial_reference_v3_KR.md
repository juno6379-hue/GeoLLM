# 사용자 승인 Q4 공간 참조와 실제 ID

사용자가 2026-10-30 채팅에서 검토안의 사용자 승인 전환과 공간 정답 ID 작성을 지시했고, 추가로 **독도 동도 기준점·2022 해양지명 CSV** 조건을 명시적으로 선택했다. 원본 검토안을 수정하지 않고 `benchmark/approved_v3/`에 USER_APPROVED_AI_ASSISTED 버전을 생성했다. 독립된 두 전문가 검수나 holdout은 아니다.

## 고정 조건과 실제 ID

- 원본: `Dataset/해양수산부_공동활용체계_해양지명_20221231.csv`, 1,146행.
- 원본 SHA256: `bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464`.
- 기준점: `data/public_place_anchors.json`의 `mof:dokdo:east-island`, 경도 131.86955555555556 / 위도 37.24077777777778. 독도 전체 경계나 항행 안전 기준점이 아니다.
- 거리: WGS84 타원체의 지표 최단거리, **5000m 이하** 포함. 원본의 명시적 도분초 필드를 WGS84로 해석하는 실험 조건이다. CRS가 표기되지 않은 투영 WKT를 정답 계산에 사용하지 않았다.
- 평가 ID: `mof_marine_names_20221231:<공간정보일련번호>`. 원본 일련번호를 보존하기 위한 namespace이며, S-101 feature ID나 운영 DB의 hashed ID가 아니다.

| 원본 ID | 지명 | 기준점 거리(m) |
|---|---|---:|
| 44 | 북향초 | 1009.230 |
| 45 | 가지초 | 959.409 |
| 46 | 강치초 | 863.775 |
| 47 | 가제초 | 844.864 |
| 48 | 삼봉초 | 696.701 |
| 49 | 괭이초 | 514.180 |
| 50 | 서도초 | 1123.071 |
| 51 | 군함초 | 840.219 |
| 52 | 넙덕초 | 810.365 |
| 53 | 부채초 | 363.893 |
| 54 | 동도초 | 281.372 |

이 동일한 11개 ID를 `PILOT_Q4_01/02/03`에 연결했다. 3문항은 같은 하나의 동등표현 그룹이며 독립 공간 표본 3개가 아니다.

## 검산과 실패 보존

Python Vincenty inverse와 연구 PostGIS `ST_Distance(geography, geography, true)`를 각각 계산했다. DB 쿼리는 inline record에 대한 읽기 전용 transaction이며 운영 DB·연구 DB 테이블을 수정하지 않는다. 전체 1,146행에서 두 방식의 5km 포함 여부가 일치했고, 거리 최대 차이는 **0.000004477m**다. 반경 경계까지의 최소 여유는 약 **3876.929m**다. 거리 계산의 일치는 지명 원천의 현실 세계 완전성을 보증하지 않는다.

초기 parser가 따옴표·decimal minutes·60초 표기 등을 지원하지 않아 45행을 처리하지 못한 run v1은 `REFERENCE_INCOMPLETE`로 보존했다. v2는 표기만 정규화하고, 60초를 정확히 다음 분으로 올림 처리한다. 한 필드가 깨진 경우 다른 명시적 좌표 필드를 사용하고 이를 기록한다. 두 필드가 모두 해석되면 수치 일치를 요구하며, 누락된 동서남북을 추측하지 않는다. 다른 필드를 사용하거나 비교하지 못한 경고 행은 3건이며 원문과 선택 필드를 모두 남겼다. 최종 미처리 행은 0이다.

산출물:

- `outputs/scie_dokdo_reference_20261030_v2/spatial_reference.json`
- `outputs/scie_dokdo_reference_20261030_v2/all_distances.jsonl`
- `outputs/scie_dokdo_reference_20261030_v2/reference_query.sql`

## 실제 시스템 출력과의 대조

`q4_live_observation.py`는 원래 질의만 API에 보내며 GOLD를 읽지 않는다. `score_q4_observations.py`는 실행 후 별도로 정답을 읽고 원본 ID·원천 SHA256·기준점·반경·전체 반환 건수를 검증한다. 운영 hashed ID를 이름으로 추측 매칭하지 않고 실제 반환 레코드의 `공간정보일련번호`로 매핑한다. 도구 미실행의 빈 결과를 정상 빈 정답으로 채점하지 않는다.

초기 실제 API `outputs/scie_q4_live_20261030_v1/`에서 한국어 5km/5000m 두 질의는 11개 동일 집합과 원천 SHA256을 확인했다. 영어 질의는 기준 위치를 명령문 앞부분으로 잘못 추출해 검색하지 않았다. 이 실패를 보존하고 별도 시스템 에이전트가 일반 영어 거리-장소 구문을 수정한다. 후속 실행은 새 run ID와 별도 cohort로 측정한다. 평가 자료를 보고 수정한 개발 결과이므로 holdout 개선으로 표현하지 않는다.

## 나머지 공간 정답의 한계

- Q3_01 최근접 등대: 전국 대상 coverage·시설 중복정책 미확정.
- Q3_02 부산항 내부 정박지: 권위 polygon·경계 포함정책 미확정.
- Q3_03 선택 영역: 원질의에 선택 geometry가 없으므로 ID 창작 대신 추가 입력 요구를 유지.
- Q5_01 등대+Wreck, Q5_02 정박지+제한구역, Q5_03 Wreck+속성: 각 자료 coverage·기준 geometry·하위작업을 추가 확인해야 함.
- 기존 S-101 연구 snapshot 25,300행은 **부산 bbox 128.9–129.3 / 34.9–35.3**의 부분집합이다. 이 데이터의 독도 조회 0건은 독도 Wreck 공간 정답으로 등록하지 않았다.

## 재현

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.dokdo_spatial_reference --output outputs/<새참조경로>
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.q4_live_observation --output outputs/<새관측경로>
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.score_q4_observations --raw outputs/<관측>/api_rows.jsonl --reference outputs/<참조>/spatial_reference.json --output outputs/<새채점경로>
```

기존 파일을 덮어쓰지 않는다. 3개 좌표/거리 단위검증, 3개 원천 결합/미실행/불완전 반환 채점 검증을 포함한 연구 테스트 전체는 당시 **80 passed**였다. 이후 추가 변경은 최종 인계에서 별도로 검증한다.
