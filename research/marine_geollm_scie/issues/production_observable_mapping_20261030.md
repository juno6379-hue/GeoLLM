# P 실제 출력의 공통 평가 관측 범위

기준 raw: runs/20261030_binding_graph_v2_ready/production_rows.jsonl. 이는 noLLM 연결 smoke이며 아직 model-enabled 결과가 아니다. 새 결과도 같은 JSON 경로가 실제 존재할 때만 매핑한다.

| 평가 재료 | 실제 P 경로 | 허용 범위 |
|---|---|---|
| 사용자 답안 | final_state.final_dict.answer_text 또는 summary; claims[].text | 실제 작성된 답안 문자열. 같은 검사를 baseline 답안에도 적용 |
| 최종 상태 | final_state.status 및 final_dict.status | 운영 상태 관측. 의미 정답으로 자동 변환하지 않음 |
| 검색 상태 | final_dict.structured_result.search_execution.status | 명시 필드가 있을 때만 사용. 없으면 null |
| 부분완료 이전 도구상태 | structured_result.execution_result_status, task_results[].status | Q5 SUCCESS_EMPTY와 전체 PARTIAL 구분 |
| 공간 출력 | structured_result.features/feature_ids/count/distance_m/reference_geometry | 실제 반환 결과/단위. coverage 미확정을 0건 정답으로 취급하지 않음 |
| 실제 반환 인용 | structured_result.citations[]의 source_file/source_id/section/page/document_type/chunk_id | locator를 순수 매핑. 모델이 인용한 문서 존재와 주장 지지는 별개 |
| Evidence | evidence_bundle.rag_evidence[].source_ref,data / spatial_feature_evidence | 실제 evidence 연결관측. 독립 검수의 entailment 점수는 아님 |
| 속성·허용기하 | document_answer 구조가 없고 답안에도 없다면 null/미관측 | documents[].excerpt_reference나 citations[].detail_text로 누락 답안을 채우지 않음 |
| claim→citation 연결 | claims[].evidence_ids | Q6은 빈 배열. 인용3개 존재를 연결3개로 바꾸지 않음 |

Q6 실제 answer_text에는 Anchorage Area 정의 영문문장과 feature:AnchorageArea가 명시됐다. 따라서 공통 지표로 양쪽 답안에서 고정 FC 정의 문자열이 공백/대소문자 정규화 뒤 실제 포함되는지, feature code가 토큰 경계와 함께 명시되는지 관측할 수 있다. 이는 정확문구 출력 지표이며 번역·의역 답안을 오답으로 단정하는 의미정확도와 구분한다. P prose 전체를 무조건 null 처리하거나 baseline 구조출력에만 유리한 지표를 전체 우열로 쓰지 않는다. 반대로 출력하지 않은 geometry/attribute bindings를 근거본문에서 추출해 답안을 완성하면 안 된다.

Q6 FC 인용 source_file은 outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml, section=feature:AnchorageArea, page=null이다. DCEG는 Dataset/S-101_Annex_A_DCEG_Ed_2.0.0.pdf, section page_413/page_415, page413/415이다. citation detail_text는 문서근거로만 취급한다. 별도 전문가 검수 없이 source해소/locator존재를 claim-support의 참값으로 변환하지 않는다.

이 문서는 연구 평가 경로를 설명하며 운영코드·원본raw·GOLD를 변경하지 않는다. 실제 형식차이로 자동매핑이 불가능한 항목은 OUTPUT_MAPPING_NOT_AVAILABLE을 유지하고, 공통 관측가능 항목의 분모를 별도로 공개한다.
