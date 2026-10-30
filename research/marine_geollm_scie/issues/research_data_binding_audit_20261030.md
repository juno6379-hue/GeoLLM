# 연구 데이터 연결 독립 감사 — 2026-10-30

## 범위와 실제 관측

운영 서비스/DB/라우팅은 수정하지 않았다. 원본 `runs/20261030_rq_v2_graph_smoke/production_rows.jsonl` 6행, launcher 로그, 실제 `marine-scie-pilot-db/scie_pilot` 카탈로그와 projection을 읽었다. 원본 smoke는 수정 이전 코드이며 새 결과로 덮어쓰지 않는다. GRAPH_RETURNED는 실행·정답 성공이 아니다.

| 사례 | 원본 상태 | 직접 원인 및 분류 |
|---|---|---|
| Q1_03 Wreck 정의 | BLOCKED | knowledge.document_chunks 부재로 문서 binding 실패: 연구 데이터 누락 |
| Q2_03 Wreck 속성 | BLOCKED | 같은 문서 binding 실패. 적재만으로 속성 설명 의무 충족을 보장하지 않음 |
| Q3_03 selected area 교차 | BLOCKED | 선택 geometry 없는 원문이 document_search로 향해 같은 binding에서 차단. 기대는 위치 확인/미실행; 문서 적재 후 실행완료를 정답으로 해석하면 안 됨 |
| Q4_01 독도 해양지명 | BLOCKED | serving.marine_gazetteer_current 부재. 기준점은 공개 원천으로 해소됐으나 데이터 relation 검증에서 차단 |
| Q5_03 독도 Wreck+속성 | COMPLETED/SUCCESS_EMPTY | 당시 snapshot 공간 SQL0건. 독도 coverage 미확정이므로 공간정답0으로 해석 금지. 속성 설명 누락은 이후 별도 운영 수정으로 PARTIAL 계약 반영됨 |
| Q6_03 AnchorageArea 출처 | BLOCKED | 문서 binding 실패. normalized_query의 Anchor재령Area 변형도 관측: 별도 정규화 잠재결함, 본 감사에서 운영 재현/수정 안 함 |

실제 연구 DB projection은 **25,300행**, Wreck **172행**, Wreck extent `BOX(128.9232991 34.9129583,129.3 35.1858904)`, geometry invalid0, SRID4326이다. `knowledge.document_chunks`, `serving.marine_gazetteer_current`, `public.codeinformation`는 to_regclass NULL. extension은 postgis 계열이며 **vector 없음**. 이 결과는 현재 subset 상태이며 전국 S-101 coverage 선언이 아니다.

## 필요한 최소 데이터 계약

1. 문서 relation `knowledge.document_chunks`: 필수 `chunk_id, source_id, source_sha256, content, metadata, embedding`. binding은 존재/컬럼/SELECT 권한만 검사하며 본문 관련성·embedding 준비는 보장하지 않는다. 실제 검색에는 embedding vector 차원·모델 일치, NULL 아님, metadata jsonb와 기본 필터 `product_id=S-101`, `version=2.0.0`, `product_specification=INT.IHO.S-101.2.0`가 필요하다. 다른 Dataset 자료를 이 메타데이터로 위조하지 않는다.
2. 해양지명 `serving.marine_gazetteer_current`: graph SQL은 `source_id, layer_id, name, properties, provenance, geometry`를 읽고 `layer_id='marine_gazetteer_mof'`, `geometry IS NOT NULL`, `ST_DWithin(geometry::geography, 기준점::geography, 반경)`을 적용한다. 거리 ORDER BY 및 LIMIT100으로 잘리는지도 별도 기록한다. approved Q4와 같은 원본/해시·원본 ID·전체1,146행 보존 후 ID44–54 검산은 다른 평가 runner에서 한다.
3. 장소 해소 `projection.s101_feature_valid`: `feature_instance_id, feature_type_name, attributes, geometry, product_specification, dataset_version_id`가 필요하다. 항만은 HarbourAreaAdministrative/INT.IHO.S-101.2.0, attributes.name 비어있지 않음 조건으로 이름별 ST_PointOnSurface(ST_Collect)를 만든다. subset 집계 대표점이 전체 운영 원천 대표점과 같다는 보장은 없다.
4. 장소 해소 `serving.island_gazetteer_current`: `source_id,name,properties(NP_ENM),geometry,source_asset,source_member,provenance,ingested_at` 필요. KHOA 원천도 활성화하려면 POSTGIS DB의 `public.maritime_gazetteer_khoa(gid,korn_nm,eng_nm,geometry,ancmnt_yr,ancmnt_inf)` 필요. 없는 원천을 빈뷰로 위장하지 말고 unavailable 상태를 기록한다.
5. S-101 radius는 `projection.s101_feature_current`의 feature_instance_id/type/code/attributes/geometry 및 관련 source/version 컬럼을 기존 snapshot 그대로 유지한다. 독도에 Wreck가 없다는 결론에는 dataset cell/coverage와 대상유형 완전성이 추가로 필요하다.
6. `public.codeinformation(name,code,type)`의 `type=0` 조회가 실패하지만 로컬 FC fallback이 있어 원본 smoke의 직접 차단 원인은 아니다. 넣는다면 실제 원천 덤프만 사용하고 FC 임의 합성 DB로 사실 권위를 꾸미지 않는다.

## DB 외 의존성과 읽기 전용 정책

- `services/standard_rag_agent/vdb.py:search_vdb`는 DISABLE_LLM_API=1이면 RetrievalUnavailable을 명시 발생시킨다. 따라서 DB 문서와 vector를 적재해도 현재 **P_current_production_no_llm**는 검색/답변 성공 조건이 아니다. 임베딩을 실제 사용하는 별도 profile과 model/digest/dimension/endpoint 도달성·예산 조건을 먼저 정한다. noLLM profile에서 임의 lexical adapter로 바꾼 결과를 full P로 부르지 않는다.
- graph retrieval은 `outputs/graph/kg_nodes_v2.jsonl`, `kg_edges_v2.jsonl`, `outputs/evidence/{kg_provenance,rag_evidence,regulatory_evidence}_candidates.jsonl`, `outputs/coastal_knowledge/{nodes,edges}.jsonl`, `outputs/dataset_pipeline/{nodes,edges}.jsonl`도 읽는다. DB만 동결해서는 동일 근거 조건이 아니다. 파일별 해시와 chunk_id→source_id→원본 locator 연결을 동결한다.
- 로그에서 `marine_geo.orchestrator_logs` 부재는 비치명 감사로그 경고였다. 이를 해소하려고 연구 데이터 연결의 read-only를 해제하지 않는다. 필요 시 파일 기반 연구 관측을 사용하고 감사 DB 쓰기가 차단됐음을 표시한다.
- `shared/observability/audit_logger.py`는 상대 `logs/audit.log` FileHandler를 만든다. source RO를 유지하면서 `/work/logs`만 연구 tmpfs로 분리한다. source `.env`는 빈파일 bind와 PYTHON_DOTENV_DISABLED로 가리고 internal network 검사·연구 DB allowlist를 유지한다.

## 연구 launcher 최소 변경과 검증

`launch_production --database scie_binding_v2 --snapshot-manifest <새 manifest> --session --repeats 1 --output-dir <새 run>`을 추가했다. 기본 scie_pilot은 보존한다. 명시 허용 DB 두 개 외 거부하며 새 DB는 manifest 필수, manifest 자체는 RO bind, S101/POSTGIS URL 모두 선택 연구 DB인지 worker에서 재검사한다. `/work/logs` tmpfs를 추가했다. 운영코드 변화 없음. 관련 단위검사 **7 passed**. 새 snapshot 적재/실제 graph 재실행은 부모 에이전트 담당이며 본 문서 시점에는 아직 성공으로 기록하지 않는다.

최소 검증 SQL/절차(모두 연구 DB READ ONLY):

```sql
BEGIN READ ONLY;
SELECT to_regclass('knowledge.document_chunks'), to_regclass('serving.marine_gazetteer_current');
SELECT has_table_privilege('knowledge.document_chunks','SELECT');
SELECT column_name,udt_name FROM information_schema.columns
 WHERE table_schema='knowledge' AND table_name='document_chunks';
SELECT count(*),count(embedding),count(DISTINCT source_sha256)
 FROM knowledge.document_chunks;
SELECT metadata->>'product_id',metadata->>'version',metadata->>'product_specification',count(*)
 FROM knowledge.document_chunks GROUP BY 1,2,3;
SELECT layer_id,count(*),count(geometry),array_agg(DISTINCT ST_SRID(geometry))
 FROM serving.marine_gazetteer_current GROUP BY 1;
SELECT feature_type_name,count(*),ST_Extent(geometry)
 FROM projection.s101_feature_current WHERE feature_type_name='Wreck' GROUP BY 1;
ROLLBACK;
```

이어 실제 SchemaBindingAdapter의 binding과 SELECT 실행, source hash/locator 해소, metadata-filter 일치 행의 유무, vector 차원/모델 일치, Q4 같은 원천 oracle 비교, 문서 없는 질의/선택영역 없는 질의의 비실행을 분리 검사한다. 빈 relation이나 관계 생성만으로 데이터 완성을 선언하지 않는다. 무관 문서 retrieval이 생겨도 의미 정답으로 채점하지 않는다.


추가 강화: 새 bundle은 status=LOADED_VERIFIED와 db_identity 일치를 launcher/worker 양쪽에서 확인한다. 실행 전후 CSV 및 mounted files 해시를 검증하고 manifest 자체 해시 변화도 실패로 처리한다. 결과는 snapshot_integrity_after.json에 분리하며 실패 원시 관측은 지우지 않는다. binding_snapshot export/load 코드의 read-only source, fixed target, no DROP, 원본 컬럼 순서·내용 roundtrip 검증을 독립 검토했다. ORDER BY source_id 동률이 있으면 동일 내용이라도 roundtrip 바이트해시가 달라질 수 있으므로 원천 키 유일성 선행 확인이 필요하다. 현재 서버에서 vector 확장 패키지0.8.6은 available이며 기존 scie_pilot에 미설치인 상태와 구분한다.


## 분리된 운영 수정 backlog (이번 작업에서 수정하지 않음)

**P0 후보 — 선택 영역 없는 공간 요구가 문서 요구로 치환됨.** 원문 Q3_03 `Find wrecks intersecting the selected area.`에는 spatial_context가 없다. 원본 graph trace에서 analysis_type=document_search, primary_agent=Standard RAG Agent, unresolved_slots=[]이며 문서 schema에서 차단된다. 코드상 `graph.py:_looks_like_standard_rag_query`의 wreck 부분문자열 조건(약918행)이 true이고, task plan 생성부(약5341행)는 analysis_type가 없으면 document_search로 채운다. 이후 공간 hint 분기보다 앞서 적용된다. 따라서 문서 적재는 이 요구의 올바른 해결이 아니다. 수정 후보 계층은 원문 작업/선택영역 지시어를 보존하는 intent→analysis_type 및 누락 공간슬롯 계약이다. API 재현 전 운영 unsafe 실행 확정으로 쓰지 않는다. 재현은 새 isolated graph run에서 동일 Q3_03을 spatial_context={}로 실행하고, 별도 source-backed polygon을 준 정상 대조와 일반 Wreck 정의 질의를 함께 검사한다. 기대: AOI없음은 clarification/미실행, polygon있음은 지원 연산과 실제 SQL 확인, 정의는 기존 문서 경로 유지. 연구 GOLD를 runtime 특례로 쓰지 않는다.

**P1 후보 — 영어 토큰 내부 사전 치환.** `outputs/dictionaries/marine_term_dictionary.yaml:25851`의 canonical 재령/alias age, `query_normalizer.py:338`의 q.replace(syn,canonical)가 `AnchorageArea` 내부 age를 치환한다. 원본 Q6 matched_rules에 age→재령이 있고 normalized_query=Anchor재령Area, normalization_confidence=1.0이다. 원천 파일과 코드 원인이 일치한다. 이는 문서 relation 누락과 독립적인 정규화 문제이다. 수정 후보는 영문 alias 토큰 경계와 표준 feature identifier 보호이며 AnchorageArea literal 예외보다 일반 경계 규칙이 필요하다. 실제 API 영향과 다른 alias 회귀는 아직 검증하지 않았다. 경량 재현 명령: `python -c "from services.orchestrator.query_normalizer import QueryNormalizer; print(QueryNormalizer().normalize('What source supports the S-101 definition of AnchorageArea?'))"`. DB/LLM이 필요 없는 normalize 단위 재현 후 실제 API 정상/부정 검증을 별도 수정 단계에서 수행한다. 현재 smoke 원본은 보존하고 이 개선을 데이터 연결 변경의 효과로 합산하지 않는다.

새 graph 결과 대기 중이며 `runs/20261030_binding_graph_v2` 생성 뒤 독립 검토 결과를 추가한다.


최초 `20261030_binding_graph_v2`는 Docker 실행 전 상대 Windows bind 경로가 거부되어 exit125였다. graph 결과0행이며 파일 hash 일치(true)는 실행 성공이 아니다. 부모가 launcher output.resolve()로 연구 경로만 보완했고 원본 실패를 보존한 `20261030_binding_graph_v2_ready`를 별도로 실행했다. 이 수정은 데이터 품질이나 운영 graph 수정과 구분한다.


## 새 연결 후 독립 검토 결과

`20261030_binding_graph_v2_ready`는 6/6 GRAPH_RETURNED, 전후 snapshot hash 검증 true. 별도 `independent_binding_audit.json`에 raw SHA와 관측을 보존했다. 모든 QEC가 EXECUTION_READY이지만 이는 해당 계획의 binding 준비 여부이고 질의 의미 정확성이나 최종 성공률이 아니다.

- Q1/Q2/Q3: 최종 BLOCKED. schema/data binding은 통과했지만 search_vdb의 noLLM/임베딩 비활성 조건에서 차단됐다. Q3의 selected AOI 누락을 문서경로로 바꾼 문제는 그대로 남았다.
- Q4: COMPLETED, 해양지명11건. 본 감사는 ID집합/거리의 독립 정답 채점이 아니며 별도 Q4 oracle 검사를 따른다.
- Q5: PARTIAL,0건,OUTPUT_OBLIGATIONS_UNMET. 이는 기존 별도 운영 수정이 반영된 상태이며 데이터 적재의 효과로 합산하지 않는다. 독도 coverage 미확정이므로 참0건 아님.
- Q6: COMPLETED, 문서3개. noLLM에서도 agent의 exact_catalogue_lookup 경로로 FC와 DCEG 근거를 연결했다. 따라서 'noLLM이면 모든 문서 경로 실패'라고 일반화하지 않는다. normalized Anchor재령Area는 여전히 남지만 원문 기반 검색이 이를 우회했다. 정규화 문제 존재와 실제 최종 답변 실패를 구분한다.

Q6 문서ID `s101_feature_exact_anchoragearea`는 FC feature:AnchorageArea이며 DCEG `57e88d95455cbb52c17f6078`(section page_413), `762031a3a7fedcdd41ee61d0`(page_415)은 연구 DB에 실제 존재했다. 읽기 전용 확인에서 본문 길이1463/3210, 둘 다 source_id=s101_dceg_2_0_pdf, source_sha256=7168ea98269736b0713c27d661177dc9c65f5c3dd038e0f33b481bec31c5645e이고 본문에 anchorage가 포함됐다. 이 확인은 locator와 본문 존재의 증거이며 전문가의 claim entailment 평가를 대신하지 않는다. metadata.page가 빈값이므로 응답 page는 section 등 파생 locator와 구분하여 검수한다.

운영 수정은 하지 않았고 원본 실패/이전 graph raw를 덮어쓰지 않았다. 남은 우선순위는 noLLM과 분리한 실제 embedding profile 동결, 원문 요구/출력의무별 평가, 독도 S-101 coverage 확인, 두 별도 운영 backlog의 실제API 재현이다.
