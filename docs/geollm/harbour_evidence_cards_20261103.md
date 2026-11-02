# 소형선항만 안내 카드·사진 원천 연결

## 구현

- `coastal_knowledge.retrieve`는 명시 항만명 exact 또는 `항만명(하위항)`만 검색한다. 인천항 요청에 북항·내항·연안항·남항을 같은 원천 객체 ID로 연결한다. 인접 시설을 동명 항만으로 치환하지 않는다.
- `harbour_evidence.harbour_card`는 소개·항해·시설·교통·기상·보급수리·조석·주변 안내의 원문 필드, 발행기관·원천연도·주소·원본파일·SHA와 객체 ID를 제공한다.
- 손상 필드와 U+FFFD가 있는 본문은 보류한다. 정상 필드도 DBF 길이 제한/현행성 미검증을 표시한다. 대표점은 입구 좌표가 아니다.
- `PPATH`와 `PHOTO1_PAT`~`PHOTO5_PAT`는 원문 연결 사진 참조다. Dataset 내부 실제 파일 존재를 확인할 때만 `/api/v1/harbour-photo` URL과 파일 SHA를 제공한다. 원격 URL, 경로탈출, 임의 사진은 허용하지 않는다. 주변 관광지 사진도 포함되므로 항만시설 사진이라고 단정하지 않는다.
- UI 모듈 `harbour-evidence.js`: `HarbourEvidence.render(host, coastal.harbour_cards)` 호출. 텍스트는 textContent, 이미지 URL은 내부 사진 endpoint만. 실제 파일 미존재/HTTP 실패를 별도로 표시한다.

## 실제 원천 확인

`outputs/coastal_knowledge/ports.jsonl` 및 ports 담당자의 운영 DB SELECT에서 인천4개 객체를 확인했다. 공통 source digest `0052e5c2f295b823b06ae7236281c5460801d4d3d195b8a2470e01bfbd95e4fb`, 행365 북항/366 내항/368 연안항/370 남항.

사진은 `소형선용항만/무역항/인천항(북항)/01_인천북항.jpg` 같은 상대 참조만 있다. 현재 확인한 `Dataset/소형선항만 안내정보`에는 SHP/DBF/SHX/PRJ/CPG만 있으며 연결 사진 실체를 확인하지 못했다. 사진 미연결 상태를 숨기지 않는다. 원천 사진을 확보한 뒤 연결 경로와 내용 일치를 확인해야 한다.

북항/내항은 INTRODU·VOYAGE_INF·FLT_STTUS·TRAFFIC_IN·TOUR_INFO·SUPPLY_REP 손상 표시가 있다. 연안항/남항은 INTRODU·FLT_STTUS·SUPPLY_REP가 손상됐다. 본문 복구는 다른 원문 확보/대조 과제로 남는다. 이 카드는 근거 표시 보완이며 데이터 완전성·최신성·항해 안전성 검증 완료가 아니다.

## 검증과 통합

### 최종 원문 일부 표시 검증

- 원문 감사에서 단순 오디코딩이 아닌 DBF 254byte 끝 UTF-8 잘림을 확인했다. `data/source_verification/harbour_prefix_20261103_v1.json`의 인천4항18필드에 한해 source/DBF/field/content SHA와 끝부분 잘림을 검증한 정상 접두부만 표시한다. 이전 전체 보류 중 이18필드만 `원문 일부`로 전환했으며 누락 문장은 복원하지 않는다.
- 실제 웹에서 북항의 항만 소개·출처를 펼쳐 원문 일부 문구와 SHA를 확인했다. Qwen 비교 갱신 중 카드가 접히는 문제도 같은 요청 generation 안에서 펼침 상태를 유지하도록 수정했다. 새 질의는 초기화한다.
- 최종 화면: `outputs/harbour_cards_source_audit_20261103_v1/final_harbour_card.png`. 4항 사진20참조는 여전히 원본 미연결이다.
- 최종 통합 Python111·Node16 통과(다른 검사와 중복 합산 금지). 전체 운영 결과는 `dashboard_full_validation_20261103.md`를 참조한다.

### 부모 통합 검증 (2026-11-03)

- 운영 backend에 카드 API·원문 필드 연결을 적용하고, `ExecutionView`와 새 카드 스크립트를 연결했다. 기존 관리 메뉴 스크립트는 보존했다.
- 실제 브라우저에서 `인천항으로 이동`을 입력해 안내 원천의 북항·내항·연안항·남항 네 카드를 확인했다. 별도 원천 후보도 구분해 표시하며 항만 안내 네 항목과 혼동하지 않는다. 후보 좌표는 지도에 표시하지만 입력 확인 중이라는 상태를 유지한다.
- 북항의 `이 위치로 조회`를 선택한 뒤 `인천항(북항)의 기준 위치를 확인했습니다.`와 지도 마커를 확인했다. 항만 대표점이며 입구 위치 검증으로 승격하지 않는다.
- 화면 증거: `outputs/dashboard_full_replay_20261103_v1/harbour_cards.png`, `incheon_north_selected.png`. 원문 출처 상세에 파일·객체 ID·SHA를 남기고, 사진 원본 미연결과 손상 본문은 별도로 표시한다.
- Python 항만 family·기준 위치·카드 회귀 묶음 29 passed. Node 카드·실행·의도 비교·반경 표시 묶음 15 passed. 아래 개별 검사와 중복되므로 합산하지 않는다.
- 100개 현재 UI 예시와 기존 19개 질의를 합쳐 중복 제거한 116개 운영 API 점검은 별도 진행 중이다. 위 카드 검증을 전체 질의 완료로 표현하지 않는다. 점검 중 UI만 보완했으며 backend 변경은 점검 종료 후 별도 검증한다.

- Node 카드 안전표시 검사 1 통과: 사용자 텍스트 HTML 실행 금지, 외부 이미지 URL 차단, 없는 사진 표시, 원천 ID 노출.
- Python: 손상본문/없는사진/정상파일SHA/경로탈출/빈필드 및 기존 coastal 회귀 검사 10 passed, 1 warning (177초). 통합 최종 검증과 구분한다.
- 부모가 script include/ExecutionView 호출을 연결한다. backend 재시작·실API·실브라우저 검증은 부모 통합 단계이며 이 작업에서 실행하지 않았다.
- DB/임베딩/연구/GOLD/홀드아웃은 변경하지 않았다.
