# 운영 데이터 안정화 후 Development K1 실행 순서

2026-11-02 사용자 지정 9단계의 실행 계약이다. 단계 번호는 우선순위이며 완료 선언이 아니다. 기존 v6 원본·GOLD·평가 결과를 보존하고, 운영 보완과 연구 실행을 분리한다. 홀드아웃 문항·정답은 개발에 사용하지 않는다.

## 단계별 완료 조건

| 단계 | 작업 | 다음 단계 진입에 필요한 증거 |
|---|---|---|
| 1 | PDF/DOCX/XLSX 원문 검증, 임베딩, source receipt, lineage | 원본 hash·페이지/문단/시트/셀 locator·본문 hash 연결. 오류 수정 전후 행/벡터 보존. 고정 모델 digest/1024차원/입력 hash 검증. DB CAS 적용과 실제 DB 재조회, receipt 게시 및 소비 확인. 격리·미검증 자료는 별도 명시하며 완료 수에 포함하지 않음 |
| 2 | Coverage 계약 | 원천 identity, 지리 범위, 실세계 완전성 분리. Q4 정상 원천 조회와 범위 밖·변조·누락 조건 실제 API 검증. 연구 snapshot 권위 연결을 별도로 검증하고 정상 fault control 오차단 해소 |
| 3 | 개발18 GOLD atoms·RQ1 | feature/attribute/relation/reference/distance/unit/evidence binding 및 task scope 고정. 전체 prediction atom 추출·잘못된 추가 주장 FP 포함. Semantic F1/Strict Match/B2−B1/paired cluster CI 산출; 표현 변형을 독립 공간 표본으로 중복 집계하지 않음 |
| 4 | RQ2 확대 | 기존8오류와 semantic ambiguity/over-expansion/wrong valid feature/wrong valid attribute/evidence mismatch의 독립 clean→single fault 쌍, 정상 대조, expected fault code 사전 고정. Binary invalid detection과 target-fault-code detection 별도 보고 |
| 5 | RQ3 실행·공간 오답 | 정상 공간 실행을 먼저 통과. wrong reference/polygon/predicate/distance method/CRS/truncation을 실제 executor에 주입. SQL 성공과 object/geometry/relation GOLD 불일치를 독립 측정. SQL 직접 반례와 방법별 성능을 구분 |
| 6 | RQ4 non-empty recovery | 비어 있지 않은 독립 GOLD object set에서 fault→recovery→집합 복원 확인. 원래 feature/reference/relation/distance/evidence 의도 보존을 동시에 검사. 원천 없음·권한 없음은 복구 분모와 분리 |
| 7 | RQ5 telemetry | P1 포함 tool/SQL/model calls, retries, human escalation, evidence completeness, provenance completeness 및 latency/token 원시 이벤트를 요청 ID로 연결. 관측0과 미계측null을 구분하고 공통 비용 경계를 고정 |
| 8 | 실제 ablation | Full P1 및 w/o Ontology/KG validation/QEC/Validator/Post-validation+Recovery를 독립 configuration으로 실행. 설정 hash와 실제 비활성 경로 trace 검증. 운영 배포 금지, 격리 연구 실행만 허용 |
| 9 | 새 Development K1 | 1–8의 검증 receipt와 코드·데이터·GOLD atoms·faults·recovery·ablation·모델·예산·평가계약 freeze 후 8방법×18=144 및 별도 fault/recovery/ablation 실행. 공유 계획·공유 검토·P0 lossless 유지 |

## Coverage는 단일 단계식 등급이 아니다

- `UNKNOWN`: 해당 축의 근거가 아직 확인되지 않음. 원천 identity 미검증과 실세계 완전성 미확인을 같은 사유로 처리하지 않는다.
- `OUT_OF_COVERAGE`: 요청 공간/시간/대상이 검증된 source domain 밖이다. 실세계 객체 부재나 검색0건이라는 뜻이 아니다.
- `SOURCE_BOUND_EXECUTABLE`: 검증된 특정 source/snapshot 안의 조회를 실행할 수 있다. 실세계 완전성이 UNKNOWN이어도 이 범위의 실행은 허용할 수 있다.
- `GEOGRAPHICALLY_COVERED`: 요청 영역이 검증된 지리 domain에 포함된다. 데이터의 누락 없음·현실 최신성을 보증하지 않는다.
- `REAL_WORLD_COMPLETE`: 명시된 대상·기간·범위에 대해 별도 완전성 근거가 있는 경우에만 주장할 수 있다. 파일 존재·행 개수·0건 결과로 승격하지 않는다.

따라서 source identity, geographic coverage, completeness, execution decision은 독립 필드와 근거를 가진다. 연구 scope를 운영 APPROVED로 복사하지 않으며 실행 허가 권위는 ExecutionValidator로 유지한다.

## 기존 성과와 남은 작업

- Q4 운영 원천 조회11건 및 연구 원본ID11/11 대조는 검증됐다. 운영 전체 coverage 및 연구 정상 CONTROL까지 완료한 것은 아니다.
- RQ1 GOLD atom은18문항/필수172·선택5가 작성됐다. canonical prediction36건 및 F1/Strict/CI는 아직 미완료다. 새 AI 원자 주석과 기존 인간 승인 GOLD를 구분한다.
- RQ2 기존 binary B4 0/8, P0/H8/8은 오류유형별N1 결과다. 사후 code 대응과 다음 실험의 사전 code 출력 계약을 구분한다.
- RQ3 실제 동일 snapshot SQL에서 정상minimum geometry24행/GOLD일치, centroid0행/정답24누락을 확인했다. 이는 개발 반례이며 P0/P1 탐지·복구 성과가 아니다. 기존 v6 성공0/5의 CGE/SSFR는null이다.
- PDF 재임베딩 진행 중이며 DOCX/XLSX 및 source receipt 후속이 남아 **현재 단계1은 미완료**다. 2–8의 기존 구현이나 단위검사만으로 단계9를 시작하지 않는다.

## Development K1 수정 규칙

K1에서 낮은 점수 자체를 버그로 간주하지 않는다. 코드 결함은 원본 run 보존→재현→분리 수정→회귀 검증→새 코드/데이터 동결→전체 재실행 순서다. 실행 중 prompt·GOLD·예산·모델을 바꾸지 않는다. 모델의 의미 오류·실제 timeout·형식 실패를 분모에서 제거하지 않는다. 점수를 보고 조건을 최적화하거나 홀드아웃을 개발에 사용하지 않는다.

최종 표는 오류유형/질의조건별 분모, 미측정, 신뢰구간, 근거와 제한을 함께 표시한다. 새 Development K1 완료와 독립 홀드아웃 평가 완료는 별개다.
