# 연구 실행 준비 검사

상태: **NOT_READY**. 논문 점수·모델 오류 판정이 아닙니다.

manifest 관계·열은 선언 검사이며 현재 DB 접근 관측과 구분합니다. 기존 Results를 변경하지 않습니다.

| 분류 | 검사 | 상태 | 설명 |
| --- | --- | --- | --- |
| DATA_PROVENANCE | snapshot_manifest | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:0 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:1 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:2 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:3 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:4 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:5 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:6 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:7 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:8 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:9 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:10 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:11 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:12 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:13 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:14 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:15 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:16 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:17 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:18 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:19 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | source_file:20 | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:manifest | PASS | 기대 해시와 파일을 대조했습니다. |
| OBSERVATION_BINDING | DB_PROBE | PASS | 별도 실행 관측이 같은 snapshot manifest를 참조하는지 검사합니다. |
| DATA_PROVENANCE | DB_PROBE:document_storage.sql | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:document_storage.json | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:vector_identity.sql | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:vector_identity.json | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:document_literal_evidence.sql | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:document_literal_evidence.json | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:q4_source_objects.sql | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:q4_source_objects.json | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:spatial_coverage.sql | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | DB_PROBE:spatial_coverage.json | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | GRAPH_NO_LLM:manifest | PASS | 기대 해시와 파일을 대조했습니다. |
| OBSERVATION_BINDING | GRAPH_NO_LLM | PASS | 별도 실행 관측이 같은 snapshot manifest를 참조하는지 검사합니다. |
| DATA_PROVENANCE | GRAPH_NO_LLM:rows | PASS | 기대 해시와 파일을 대조했습니다. |
| DATA_PROVENANCE | GRAPH_NO_LLM:integrity_after | PASS | 기대 해시와 파일을 대조했습니다. |
| OBSERVATION_BINDING | GRAPH_NO_LLM:integrity | PASS | 격리 graph 실행 후 원천 무변경 관측을 참조합니다. graph 반환과 실행 성공을 동일시하지 않습니다. |
| DATA_PROVENANCE | RETRIEVAL_COMPONENT:manifest | PASS | 기대 해시와 파일을 대조했습니다. |
| OBSERVATION_BINDING | RETRIEVAL_COMPONENT | PASS | 별도 실행 관측이 같은 snapshot manifest를 참조하는지 검사합니다. |
| DATA_PROVENANCE | RETRIEVAL_COMPONENT:rows | PASS | 기대 해시와 파일을 대조했습니다. |
| OBSERVATION_BINDING | RETRIEVAL_COMPONENT:rows | PASS | 검색 manifest에 기록된 행 수와 원시 결과 해시를 대조했습니다. |
| MODEL_PROFILE | RETRIEVAL_COMPONENT | UNKNOWN | 질의 임베딩 호출과 저장 벡터 모델의 동일성은 별도 조건입니다. 후보 반환을 근거 정확도로 승격하지 않습니다. |
| EXECUTION_PROFILE | research_db_identity | PASS | 명시적 연구 DB 식별자와 snapshot 대상의 일치를 검사합니다. |
| DATA_PROVENANCE | snapshot_capture | PASS | 캡처 시각·트랜잭션·행 수 기록 검사입니다. DB 현재 상태를 증명하지 않습니다. |
| RELATION_SCHEMA | knowledge.document_chunks | PASS | manifest 선언과 필수 관계·열을 대조했습니다. 실제 DB 존재 여부는 별도 관측이 필요합니다. |
| DATA_PROVENANCE | knowledge.document_chunks:row_count | PASS | 원천 행 수 선언 검사이며 DB 적재 행 수와 구분합니다. |
| DATA_PROVENANCE | knowledge.document_chunks:csv | PASS | 기대 해시와 파일을 대조했습니다. |
| DATABASE_LOAD_OBSERVATION | knowledge.document_chunks | PASS | 별도 로더가 기록한 COPY 재출력 해시·행 수와 원천을 대조했습니다. 현재 DB를 재접속한 결과는 아닙니다. |
| RELATION_SCHEMA | serving.marine_gazetteer_current | PASS | manifest 선언과 필수 관계·열을 대조했습니다. 실제 DB 존재 여부는 별도 관측이 필요합니다. |
| DATA_PROVENANCE | serving.marine_gazetteer_current:row_count | PASS | 원천 행 수 선언 검사이며 DB 적재 행 수와 구분합니다. |
| DATA_PROVENANCE | serving.marine_gazetteer_current:csv | PASS | 기대 해시와 파일을 대조했습니다. |
| DATABASE_LOAD_OBSERVATION | serving.marine_gazetteer_current | PASS | 별도 로더가 기록한 COPY 재출력 해시·행 수와 원천을 대조했습니다. 현재 DB를 재접속한 결과는 아닙니다. |
| RELATION_SCHEMA | serving.navigation_aid_current | PASS | manifest 선언과 필수 관계·열을 대조했습니다. 실제 DB 존재 여부는 별도 관측이 필요합니다. |
| DATA_PROVENANCE | serving.navigation_aid_current:row_count | PASS | 원천 행 수 선언 검사이며 DB 적재 행 수와 구분합니다. |
| DATA_PROVENANCE | serving.navigation_aid_current:csv | PASS | 기대 해시와 파일을 대조했습니다. |
| DATABASE_LOAD_OBSERVATION | serving.navigation_aid_current | PASS | 별도 로더가 기록한 COPY 재출력 해시·행 수와 원천을 대조했습니다. 현재 DB를 재접속한 결과는 아닙니다. |
| RELATION_SCHEMA | serving.island_gazetteer_current | PASS | manifest 선언과 필수 관계·열을 대조했습니다. 실제 DB 존재 여부는 별도 관측이 필요합니다. |
| DATA_PROVENANCE | serving.island_gazetteer_current:row_count | PASS | 원천 행 수 선언 검사이며 DB 적재 행 수와 구분합니다. |
| DATA_PROVENANCE | serving.island_gazetteer_current:csv | PASS | 기대 해시와 파일을 대조했습니다. |
| DATABASE_LOAD_OBSERVATION | serving.island_gazetteer_current | PASS | 별도 로더가 기록한 COPY 재출력 해시·행 수와 원천을 대조했습니다. 현재 DB를 재접속한 결과는 아닙니다. |
| RELATION_SCHEMA | projection.s101_feature_current | PASS | manifest 선언과 필수 관계·열을 대조했습니다. 실제 DB 존재 여부는 별도 관측이 필요합니다. |
| DATA_PROVENANCE | projection.s101_feature_current:row_count | PASS | 원천 행 수 선언 검사이며 DB 적재 행 수와 구분합니다. |
| DATA_PROVENANCE | projection.s101_feature_current:csv | PASS | 기대 해시와 파일을 대조했습니다. |
| DATABASE_LOAD_OBSERVATION | projection.s101_feature_current | PASS | 별도 로더가 기록한 COPY 재출력 해시·행 수와 원천을 대조했습니다. 현재 DB를 재접속한 결과는 아닙니다. |
| DATA_PROVENANCE | environment_probe | PASS | 기대 해시와 파일을 대조했습니다. |
| ENVIRONMENT | runtime_probe | PASS | 환경 관측 결과이며 모델 오류 또는 정상 질의 차단으로 분류하지 않습니다. |
| EXECUTION_PROFILE | embedding | PASS | 임베딩 호출 비활성은 명시적 프로파일 제약입니다. 모델 오류로 간주하지 않습니다. |
| DATA_PROVENANCE | references | PASS | 기대 해시와 파일을 대조했습니다. |
| REFERENCE_APPROVAL | PILOT_Q1_01 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_01:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_01:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_01:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_01:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q1_02 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_02:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_02:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_02:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_02:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q1_03 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_03:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_03:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_03:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q1_03:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q2_01 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_01:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_01:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_01:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_01:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q2_02 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_02:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_02:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_02:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_02:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q2_03 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_03:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_03:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_03:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q2_03:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q3_01 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_01:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_01:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_01:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_01:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_01:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| INPUT_CONTRACT | PILOT_Q3_01:aoi | UNKNOWN | 이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다. |
| COVERAGE | PILOT_Q3_01:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q3_02 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_02:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_02:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_02:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_02:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_02:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| INPUT_CONTRACT | PILOT_Q3_02:aoi | UNKNOWN | 이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다. |
| COVERAGE | PILOT_Q3_02:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q3_03 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_03:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_03:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_03:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_03:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q3_03:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| INPUT_CONTRACT | PILOT_Q3_03:aoi | UNKNOWN | 이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다. |
| COVERAGE | PILOT_Q3_03:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q4_01 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_01:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_01:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_01:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_01:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_01:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| DATA_PROVENANCE | PILOT_Q4_01:aoi_reference | PASS | 기대 해시와 파일을 대조했습니다. |
| INPUT_CONTRACT | PILOT_Q4_01:aoi | PASS | 명시적 AOI 계약 artifact를 참조합니다. bbox 포함 검사는 별도 미측정입니다. |
| COVERAGE | PILOT_Q4_01:bbox | UNKNOWN | AOI 계약은 제공됐지만 bbox coverage는 이 검사에서 대조하지 않았습니다. |
| COVERAGE | PILOT_Q4_01:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q4_02 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_02:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_02:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_02:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_02:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_02:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| DATA_PROVENANCE | PILOT_Q4_02:aoi_reference | PASS | 기대 해시와 파일을 대조했습니다. |
| INPUT_CONTRACT | PILOT_Q4_02:aoi | PASS | 명시적 AOI 계약 artifact를 참조합니다. bbox 포함 검사는 별도 미측정입니다. |
| COVERAGE | PILOT_Q4_02:bbox | UNKNOWN | AOI 계약은 제공됐지만 bbox coverage는 이 검사에서 대조하지 않았습니다. |
| COVERAGE | PILOT_Q4_02:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q4_03 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_03:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_03:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_03:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_03:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q4_03:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| DATA_PROVENANCE | PILOT_Q4_03:aoi_reference | PASS | 기대 해시와 파일을 대조했습니다. |
| INPUT_CONTRACT | PILOT_Q4_03:aoi | PASS | 명시적 AOI 계약 artifact를 참조합니다. bbox 포함 검사는 별도 미측정입니다. |
| COVERAGE | PILOT_Q4_03:bbox | UNKNOWN | AOI 계약은 제공됐지만 bbox coverage는 이 검사에서 대조하지 않았습니다. |
| COVERAGE | PILOT_Q4_03:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q5_01 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_01:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_01:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_01:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_01:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_01:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| INPUT_CONTRACT | PILOT_Q5_01:aoi | UNKNOWN | 이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다. |
| COVERAGE | PILOT_Q5_01:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q5_02 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_02:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_02:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_02:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_02:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_02:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| INPUT_CONTRACT | PILOT_Q5_02:aoi | UNKNOWN | 이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다. |
| COVERAGE | PILOT_Q5_02:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q5_03 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_03:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_03:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_03:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_03:spatial | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q5_03:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| INPUT_CONTRACT | PILOT_Q5_03:aoi | UNKNOWN | 이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다. |
| COVERAGE | PILOT_Q5_03:completeness | UNKNOWN | 객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다. |
| REFERENCE_APPROVAL | PILOT_Q6_01 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_01:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_01:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_01:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_01:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q6_02 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_02:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_02:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_02:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_02:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |
| REFERENCE_APPROVAL | PILOT_Q6_03 | BLOCKED | 사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_03:semantic | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_03:qec | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_03:evidence | BLOCKED | 필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다. |
| EVALUATION_CONTRACT | PILOT_Q6_03:enabled | BLOCKED | 새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다. |

## 별도 실행 관측

서로 다른 실행 범위를 합쳐 Full P 또는 의미·근거 정확도로 표현하지 않습니다.

```json
[
  {
    "kind": "DB_PROBE",
    "scope": "REAL_DATA_BINDING_AND_VECTOR_OPERATOR_PROBE_NOT_FULL_PIPELINE",
    "accuracy_inferred": false,
    "probes": 5,
    "model_calls": 0,
    "database_writes": false
  },
  {
    "kind": "GRAPH_NO_LLM",
    "scope": "P_current_production_no_llm",
    "accuracy_inferred": false,
    "rows": 6,
    "status_counts": {
      "BLOCKED": 3,
      "COMPLETED": 2,
      "PARTIAL": 1
    },
    "differences_from_model_baselines": [
      "LLM APIs disabled",
      "pgvector capability retrieval disabled",
      "external dependencies unreachable",
      "HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1; uncached Hugging Face assets cannot be downloaded",
      "frozen source subset; measured size is referenced in snapshot_manifest"
    ]
  },
  {
    "kind": "RETRIEVAL_COMPONENT",
    "scope": "ACTUAL_EMBEDDING_RETRIEVAL_COMPONENT_NOT_FULL_GRAPH",
    "accuracy_inferred": false,
    "rows": 9,
    "status_counts": {
      "RETRIEVAL_COMPLETED": 9
    },
    "embedding_calls": 9,
    "model": {
      "name": "bge-m3:latest",
      "model": "bge-m3:latest",
      "modified_at": "2026-07-21T15:44:34.8396223+09:00",
      "size": 1157672605,
      "digest": "7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab",
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "bert",
        "families": [
          "bert"
        ],
        "parameter_size": "566.70M",
        "quantization_level": "F16",
        "context_length": 8192,
        "embedding_length": 1024,
        "runner": "ggml"
      },
      "capabilities": [
        "embedding"
      ]
    },
    "model_digest_unchanged": true,
    "stored_embedding_model_profile_verified": false,
    "returned_candidate_counts": [
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3
    ]
  }
]
```
