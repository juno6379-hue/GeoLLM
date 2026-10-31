# Dataset 운영 원천·적재·검색 감사 — 2026-10-31

## 결론

운영 문서 벡터는 완료됐지만 Dataset 전체 처리·공간 실행·의미 지식 연결·최종 답변 활용까지 완료된 것은 아니다. 논문 전용 임베딩이 아니라 운영 DB를 확인했다. 이번 점검은 원본 재해시, 운영 DB SELECT, 실제 근거 API 및 코드 경로 감사다. 생성형 답변/SSE의 신규 종단 검증은 실행 중인 K5와 같은 Ollama를 공유하므로 종료 후 별도 run에서 수행한다.

## 원본 대조

현재 Dataset 244파일(10,867,342,303 bytes), SHA256 고유229개. 10월2일 manifest와 경로 추가/삭제·크기 변경·전체 SHA256 변경 모두0. 원본이 사라졌다는 증거는 없다. 파일이 존재한다는 것과 검색에 적재됐다는 것은 다르다.

새 audit.json은 기존 추출 기록과 오늘 운영 DB snapshot을 대조했다. 32파일 EXTRACTED, 42파일 SOURCE_RECORDS_EXTRACTED, 84파일 기존 본문 완전성 미검증, 31파일 기존 record 완전성 미검증, 55파일 형식별 adapter/처리 확인 필요. 55파일에는 서명ZIP·dump·HTML·SHP sidecar·중첩 archive·보조코드 등이 포함되므로 모두 본문 임베딩 누락이라고 세면 안 된다. 단독 SHP와 중첩 압축의 실제 원천 lineage 대조가 필요하다. 새 추출을 수행한 것이 아니라 기존 추출 증거의 재대조다.

기존 추출 기록의 고유hash 기준 빈 section557개는 OCR 대상 확정 수가 아니다. 빈 페이지/표/이미지 여부를 판정해야 하며 기존 항로서지61개 빈 PDF쪽 등의 기존 제한과 중복 합산하지 않는다. 수치조류 바이너리 grid/time/encoding 사양, archive 내부 전 항목, dump 원본과 적재 관계 완전성은 미검증이다.

## 운영 DB 직접 확인

knowledge.document_chunks 23,215/임베딩23,215. dataset_source_text6,362, coastal_pilot6,111, small_harbour_guide2,329. 파일/DB 요약 profile311개도 전체 숫자에 포함되므로 23,215개 모두 원본 본문이라고 표현하지 않는다. 기존 일부 벡터 생성 provenance 미확정은 이번 COUNT로 해소되지 않는다.

serving.dataset_source_records 총1,338,776행: 기존 추출 정적공간209,952 + CSV1,128,824와 일치. 유효 geometry206,120. 정적공간3,832행은 공간 사용 제외이며 CSV의 무geometry는 좌표 추정 금지 정책에 따른 것이다. CSV 1,128,824행을 불량 geometry로 세면 안 된다. small_harbour_guide439/439, marine_gazetteer_current1,146/1,146, island_gazetteer_current1,140/1,140, navigation_aid_current314/314를 확인했다. 적재·geometry 유효성은 최신성/위치 권위/실행 adapter 지원을 보증하지 않는다.

## 지식 연결

현재 Dataset 그래프 파일23,418노드/23,232관계. 노드는 source186, DocumentChunk23,193, RecordCollection39. 관계23,232개 모두 derivedFromSource다. 이는 출처 연결이며 항만 입구·방파제·시설·법령 적용 범위의 검수된 의미 관계가 아니다. 런타임은 coastal 그래프 일부를 읽고 Dataset 문서의 derivedFromSource를 응답 시 추가한다. 전체 Dataset 그래프가 canonical 의미 추론에 사용된 것으로 간주하지 않는다.

## 실제 운영 근거 API 8질의

2026-10-31 실제 GET /api/v1/dataset-evidence, semantic=false. 원본 live_lexical_probes.json 보존.

| 질의 | 문서 | 공간기록 | 관측 |
|---|---:|---:|---|
| 부산항 입구 |5|5|COMPLETED, 상위 문서는 2023 사고심판사례집316/856쪽. 현재 입구 안내의 적합성을 보장하지 않음|
| 다대포항 |5|2|COMPLETED, 소형선항만 안내 본문|
| 울릉도 |5|5|COMPLETED, 저동항 안내 및 항로서지|
| 해양공간관리계획 |5|0|COMPLETED, 부산 계획18/126쪽|
| 해양사고심판 |5|0|COMPLETED, 법령정보/사례집|
| 양식장 |5|0|PARTIAL, 공간조회 OperationalError|
| 수로 |5|0|PARTIAL, 공간조회 OperationalError|
| 없는자료XYZ987654 |0|0|정상 빈 검색|

8요청 모두 JSON응답, 6 COMPLETED/2 PARTIAL. 시간7.48~24.62초. 논문 CPU실행·원본hash·DB감사와 병행한 관측이므로 단독 서비스 SLO나 이전보다 느려진 원인을 확정하지 않는다. 공간조회3초 statement_timeout이 코드에 있지만 OperationalError의 원인이 timeout인지 DB로그/격리 재현으로 확정해야 한다.

## 답변 활용의 중요한 제한

coastal_knowledge.retrieve는 semantic=true여도 content/title ILIKE를 먼저 요구하고 lexical 점수를 유사도보다 먼저 정렬한다. 어휘가 다른 질문을 벡터만으로 회수하는 구조가 아니다. CSV는 자료명 중심이며 임의 시계열/속성 집계 adapter를 대신하지 않는다.

router.py 일반 SSE는 graph 실행 종료 후 final_dict에 coastal_evidence를 붙인다. 즉 근거 패널 검색 성공은 이미 생성된 최종 답변이 이 근거를 사용했다는 증거가 아니다. instant 위치 응답도 답변 생성 후 근거를 붙인다. 별도 dataset-explanation에서 Qwen이 인용을 고르는 경로와 일반 답변 통합을 구분해야 한다. Dataset provenance fast path는 행수/적재정보를 답하며 일반 내용 질문을 해결하는 경로와 다르다.

## 다음 순서

1. K5 완료 후 추가 Ollama 부하 없는 시간에 실제 SSE 최종답변·근거·Qwen 선택을 같은 질의로 수집. 모델/실행 승인/답변/근거 출처를 각각 판정. semantic 검색과 어휘 변형·부정 질문 포함.
2. 양식장/수로 공간조회 오류를 격리 재현하고 실행계획/DB 오류코드 확인. 현재 원본은 유지.
3. 55개 미대조 파일은 서명/sidecar/중복/보조파일과 실제 누락 원천을 분리. archive member manifest, 빈페이지 검수/OCR, 수치조류 사양, dump 검증.
4. canonical 객체와 의미 관계·원천 판 검수. 답변 생성 이전에 검증된 근거를 공급하도록 개선 여부 판단 및 별도 변경·실제 API 검증. 지금 동결 소스는 변경하지 않았다.

원시 자료: outputs/dataset_audit_20261031/{raw_manifest/raw_source_manifest.json,hash_comparison.json,live_snapshot.json,audit.json,audit.md,live_lexical_probes.json}. 후속 automation geollm-k5에 K5 종료 후 운영 종단 검증을 추가했다. 현재 전체 점검 완료가 아니며 이번 소스/DB mutation 없음.

## K5 종료 후 운영 점검 시작

K5가20:44:50KST 종료된 뒤 모델서버500 별도재현2건을 마쳤다. 운영6질의 SSE/semantic/Qwen 인용은 outputs/dataset_live_followup_20261031_v1에서 순차진행중이며 완료아님. 공간SQL별도readonly재현에서 양식장 pgcode57014/statement_timeout3초 확인, 수로5행1.85초 성공. 원본 공간오류를 전부 동일원인으로 단정하지 않는다.

## 후속 수정과 검증 완료

별도수정에이전트의 운영답변연결 보완과 실제6질의 재검증을 완료했다. [수정보고서](dataset_answer_fix_20261031.md) 참조. 긍정5개는 원문발췌3개씩 본문반영/PARTIAL, 음성0건/BLOCKED이며 기존원본보존. 별도공간검색오류와 전체원천/의미연결미완료는남아있다.
