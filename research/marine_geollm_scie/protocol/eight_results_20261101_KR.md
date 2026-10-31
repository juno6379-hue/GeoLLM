# GOLD v2 8방법 K1 결과와 한계

2026-11-01 03:39:02 KST 종료. 약66분24초. `runs/20261101_gold_v2_eight_k1_v2`의 관측 수집과 보고서 생성은 완료했으나, 논문 RQ 전체·독립 인간 의미 정확도 검증은 완료되지 않았다.

## 원본과 검증

- [통합 기계 보고서](../runs/20261101_gold_v2_eight_k1_v2/report_with_faults/comparison_KR.md), 같은 폴더 summary.json/scores.jsonl에 조건·오류 유형·분모·비용이 있다.
- [통제 오류 보고서](../runs/20261101_gold_v2_eight_k1_v2/fault_report/comparison_KR.md).
- B0/B1/B2/B3/B4/P0/H/P1 각18, 총144개 고유 문항·방법 관측. 별도 오류9×3=27관측. 부모·자식 프로세스 종료, supervisor 전체단계 exit0 확인.
- 주검증자가 144개 raw hash, 전체272개 동결 파일, 18문항의 공유 최초계획 및 B4/H 공유검토, fault27개 계약·원본·Oracle hash, 보고서3파일 hash를 재확인했다. 오류0. 최종 증빙 `outputs/gold_v2_eight_final_verification_20261101.json`.
- 모델 digest 사후 검증 및 소스 불변 gate 통과. immutable GOLD와 v1 실패 원본을 덮어쓰지 않았다. v1은 projector 형식 오류로 중단된 별도 실행이다.

## 기계 계약 결과

| 방법 | 통과 | 측정된 문항 | 전체 |
|---|---:|---:|---:|
| B0 | 0 | 15 | 18 |
| B1 | 0 | 15 | 18 |
| B2 | 0 | 14 | 18 |
| B3 | 2 | 14 | 18 |
| B4 | 2 | 14 | 18 |
| P0 | 0 | 14 | 18 |
| H | 0 | 14 | 18 |
| P1 | 8 | 18 | 18 |

이 수치는 기계 계약 검사이며 자유문 의미 정확도나 방법의 일반적 우열이 아니다. 결측을 실패 0으로 채우지 않았다. 생성·실행 인터페이스 및 예산이 다르고 K1 단일 실행이다. B0/B1/B2는 domain tool 없는 조건이다. B1 일부 문항은 검색 packet이 비어 있었다.

P1 공간 실행 성공과 공간 정답은 평가 대상5건 중 각3건이다. Silent Spatial Failure는 성공한3건 중0건이며, 전체 시스템의 무오류 증거가 아니다. coverage Safe Abstention은 별도3건 중0건이다. 성공3건은 Q4_01/02/03의 동일 `dokdo_radius_5km` 동등 질의군이므로 독립 공간 성공3종으로 세면 안 된다. 추가로 baseline은 관측 완료된 미실행의 execution_succeeded를 null로, P1은 false로 기록하는 비대칭이 발견됐다. 공통 실행성공 정의를 고정한 별도 평가 버전이 필요하며, 현재 P1 0.6과 baseline 미측정을 직접 순위 비교하면 안 된다. B0~H의 공간 성공·정확성 전체 비율은 결측으로 확정할 수 없으며, 미측정을 0%나 안전성 보장으로 해석하면 안 된다.

비교 원시 상태는 INVALID_RESPONSE15, EXECUTOR_RETURNED34, VALIDATOR_BLOCKED34, completed39, INVALID_INITIAL_PLAN4, GRAPH_RETURNED18이다. 같은 최초계획 실패가4분기에 나타나므로 독립 모델 실패4회로 세면 안 된다. EXECUTOR_RETURNED 역시 SQL 성공을 뜻하지 않는다. 토큰 상한에 따른 JSON 절단과 잘못된 응답 구조를 관측에서 제외하지 않았다.

## 통제 오류: 중요한 미완료 항목

- LLM 검토9회는 모두 HTTP/모델 응답 완료, done_reason=stop,185~209토큰이었다. 시간 초과가 아니다. 요구한 `{invalid, reason, plan}` 대신 plan 객체만 반환해 REVIEW_SCHEMA 검증에 모두 실패했다. 일부 계획 변화가 있더라도 사후 포장하거나 검출 verdict를 추론하여 복구 성공으로 채점하지 않았다.
- 따라서 B4 최초 검출9건 모두 미측정, H는 Validator가 검출한4건만 판정되고5건은 미측정이다. B4/H의 실제 복구 시도0건이므로 시도 대비 복구율·의미 보존율은 미측정이다. 적격6건 대비 공동 복구 성공은0건이다.
- P0 오류8건 중4건을 놓쳐 False Ready4/8. 누락은 CRS 불일치, 잘못된 Feature, 대상 확장, 잘못된 반경이다. 검출4건 중 단위 타입1건은 compiler 거절이고3건은 native 검사다. 이를 전부 native Validator 검출로 귀속하지 않는다.
- 정상 control1건은 차단하지 않아 False Block0/1이다. 표본1건으로 일반화하지 않는다. permission fault는 격리 권한 원천이 없어 미실행이다.

## 운영과 연구를 분리한 다음 작업

1. 원시 결과·GOLD·모델·예산을 보존한다. 먼저 미실행 시 execution_succeeded의 공통 정의를 고정해 새 평가 버전에서 재검증한다. RQ2/RQ4용 검토 응답 계약을 별도 개발 검증에서 안정화하고, 수정 시 새 동결 run으로 재실행한다. 이번 실패를 정상 응답으로 소급 변환하지 않는다.
2. 사용자 요청의 원래 CRS/Feature/반경/대상 집합과 계획의 의미 일치를 검사하는 계약을 보완한다. P0에는 새 추론·자동교정을 넣지 않는다. 운영 source coverage와 승인된 canonical 참조·복합 실행 지원도 별도 검증한다.
3. 운영 revision3→1, shadow selection/score mismatch, nearest 등대·부산항 참조 인터페이스 미지원은 별도 잔여다. 운영 수정 뒤 전체 benchmark 재실행이 필요하다.
4. 독립 GOLD 결과 수령과 반복 실험 후 정확도·변동성 및 RQ별 결론을 작성한다. 현재 scientific_completion=false, rq1_to_rq5_complete=false, production_release_approved=false를 유지한다.

관측·보고서 완료에 따라 이 run의 자동 후속 점검은 종료한다. 이는 남은 운영 오류나 논문 검증 전체의 완료를 의미하지 않는다.
