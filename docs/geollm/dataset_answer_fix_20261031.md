# 운영 Dataset 근거의 실제 답변 반영 수정 — 2026-10-31

## 수정 전 실제6질의

outputs/dataset_live_followup_20261031_v1/rows.json·answer_audit_before.json을 보존했다. 6개 SSE는 종료됐으나 다음 문제가 있었다.

| 질의 | 수정 전 본문 문제 | 수정 후 실제SSE |
|---|---|---|
| 부산항 입구 정보를 알려줘 | 위치 후보 선택 요구, 문서/Qwen인용은 별도 존재 | PARTIAL, 항로서지 원문3개+출처 |
| 다대포항 소형선항만 안내정보를 알려줘 | 지명/좌표 입력 요구 | PARTIAL, 안내정보 원문3개+출처 |
| 해양공간관리계획을 설명해줘 | 계획서가 있는데 문서없음으로 COMPLETED | PARTIAL, 계획서 원문3개+출처 |
| 양식장 관련 정보를 알려줘 | unsupported operation: clarification_required | PARTIAL, 관련원문3개+출처 |
| 수로 관련 정보를 알려줘 | unsupported operation: clarification_required | PARTIAL, 관련원문3개+출처 |
| 없는자료XYZ987654에 관한 자료를 찾아줘 | 지명조회로 오인, '관한' 때문에 semantic 무관문서5개 | BLOCKED/EVIDENCE_NOT_FOUND, 문서0·인용0 |

## 원인과 변경

기존 일반 SSE는 graph 답변을 만든 뒤 coastal_evidence를 부착했다. 이 때문에 근거 패널에서 자료를 찾더라도 주답변에는 활용되지 않았다. 정보질문이 지명실행 경로를 탔고 Standard RAG가 Dataset 본문을 찾지 못한 응답도 따로 남았다.

별도 수정 에이전트가 services/orchestrator/dataset_answer.py를 추가하고 공통 graph parse에 연결했다. 순수 정보/자료설명 요청 형태를 판별하되 지도·좌표·거리·실행·시간·정책·표준 전용질문은 기존경로로 유지한다. 특정항만/질의목록의 답변을 하드코딩하지 않는다. 기존 instant 위치 경로가 문서질문을 먼저 가로채지 않게 하고 state/재개flag를 보완했다.

ExecutionValidator의 dataset_document_lookup 계약이 실제 document_chunks SELECT권한/필수열을 검사한다. 승인된 근거만 원문·대상·source ID/hash·locator를 확인해 summary/answer_text에 넣는다. 구조화 source_passages/citations/rag_evidence와 동일근거를 보존한다. 설명의 종합완결성·최신성을 과장하지 않아 PARTIAL이며 공간실행은 NOT_RUN/coordinate_authority=false다. 자료없음과 DB/승인장애는 서로 다른BLOCKED로 표시한다.

coastal_knowledge.query_terms에서 '관한/대한' 등 기능어와 조사'에'를 정리하고 핵심어의 AND일치를 요구한다. 안내자료 요청에는 항로서지/소형선항만을 우선한다. 문서전용 요청은 무관한 공간SQL을 실행하지 않는다. 최종본문에 쓰인 evidence를 SSE에서 다시조회해 덮지 않는다. Qwen은 별도인용선택/비교이며 사실/실행권한을 부여하지 않았다.

## 실제 검증

- 별도 에이전트 관련회귀: `python -m pytest tests/unit/test_dataset_answer.py tests/unit/test_coastal_knowledge.py tests/unit/test_execution_authority.py tests/unit/test_execution_gate_regressions.py -q --disable-warnings --maxfail=2` → **96 passed**,14.00초. 테스트네트워크/LLM차단fixture로 단위검사와 실제모델검증을 구분했다.
- backend 재기동 최초 after_v2는 준비전 RemoteDisconnected6건이며 원본보존. 모델/로딩준비후 health200 확인한 새 **after_v3**에서 같은6질의를재실행했다. source_unchanged_after=true.
- after_v3/verified_answers.json **6/6**: 긍정5질의 각3발췌가 실제검색원문과 본문에 모두존재, sourcehash/제목/문서승인일치, 공간미실행, 불필요위치질문없음. semantic 문서각5, Qwen선택인용각3. 음성질의는 본문/semantic문서0·Qwen NO_EVIDENCE. 인용일치/실행계약 검사이지 인간의 의미정답률은 아니다.
- 별도 POST/GET 통제3건: 이동과 지도복합은 NEEDS_CLARIFICATION으로 기존위치경로유지, 비공개는 BLOCKED_POLICY. 문서전용응답으로 다른작업을 완료처리하지 않았다. **성공한 지도이동을 검증한 것이 아니다**. 이동의 최종본문 부재 및 복합의 LOCATION_UNCONFIRMED는 남은 기존경로 한계다.
- UI는 기존 answer_text/summary를 사용하므로 별도UI변경없이 본문이 제공된다. 이번 검증은 웹과같은 실제SSE/API이며 브라우저렌더링/지도상호작용을 새로검증하지 않았다.

## 남은 제한

- 원문발췌를 제공하는 답변이며 종합적인 생성설명이나 질문전체 의미완결은 미확정이다. 부산항입구는 관련항로서지가 우선되지만 같은페이지의 주변지역설명이 포함돼 국소문장선택·가독성 개선여지가 있다.
- 독립 semantic endpoint는 여전히 lexical 후보를 먼저 제한하므로 동의어·다른표현 recall은 미검증이다. AND변경은 부정질문의 false positive를 줄이지만 일부복합표현 recall을 낮출 수 있다.
- 별도 dataset-evidence의 공간조회는 양식장/수로에서 OperationalError/PARTIAL이 여전히 관측됐다. 본문설명 경로와 분리했을 뿐 공간검색 성능오류를 해결했다고 하지 않는다. 양식장은 SQLSTATE57014/3초timeout 재현, 수로는 단독성공관측도 있어 부하별검증필요.
- 복합지도+정보의 부분답변 결합, 현재자료판 검수, 55파일형식/중첩archive/OCR/수치조류/canonical의미관계 연결은 별도남은작업이다.
- 논문K5 원시540관측/채점은 그대로보존했다. 이번 운영소스변경을 적용한 논문비교가 필요하면 새동결run을 사용한다.

## 산출물

- before: outputs/dataset_live_followup_20261031_v1
- 준비전실패: outputs/dataset_live_followup_20261031_after_v2
- 정상재검증: outputs/dataset_live_followup_20261031_after_v3/{rows.json,*_events.json,verified_answers.json,manifest.json}
- 통제: outputs/dataset_answer_controls_20261031_v1/{rows.json,verified_controls.json}
- 재현script/검증기: outputs/dataset_audit_20261031/{run_after_fix_v3.py,verify_after_fix.py,run_controls.py}

요청한6질의의 수정/재검증/인계가완료되어 후속자동점검을종료한다. 소스·테스트·문서만묶고 기존UI/feedback/별도테스트변경은보존한다.
