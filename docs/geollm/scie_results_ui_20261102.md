# 논문 결과 전용 UI 구현·검증

사용자 지정 `CODEX_Marine_GeoLLM_SCIE_Results_UI_Prompt_KR.md`를 기준으로 데이터 adapter, 화면, 독립 감사 역할을 분리했다. 구현은 `tools/scie_results_ui/`에 격리한다. 운영 FastAPI 정적 HTML/CSS/JS 구성과 네이비 탐색 구조를 참고했으며 운영 화면과 라우터를 수정하지 않는다.

## 실행 및 접근

- 화면: http://localhost:8001/research/scie-results
- 읽기 API: http://localhost:8001/research/scie-results/api/dashboard
- 실행: `.venv/Scripts/python.exe -m tools.scie_results_ui.server --port 8001`
- loopback 전용 서버이며 DB/Ollama/운영 질의 API 호출이 없다. 결과를 다시 읽는 버튼과 15초 파일 조회 캐시를 사용한다. 서비스 재부팅 후 위 명령으로 다시 기동한다.

## 데이터 연결과 화면

1. `RESULTS_INDEX_KR.md`의 최신 완료 행이 인용할 결과를 선택한다. 현재 v5가 144+27 검증 완료 결과이며 v6는 별도 실행 이력이다. worker 종료만으로 검증 완료 결과로 승격하지 않는다.
2. immutable GOLD의 manifest/queries/answer_contracts/protocol에서 질의 수, 방법, 범주, 계약, 공간 GOLD와 독립 검수 상태를 읽는다. 빈 object set도 유효한 공간 GOLD이며 기존 scoring flag와 GOLD 존재 여부는 별개다.
3. 선택 run의 통합 summary에서 RQ별 기계 검사·공간 실행·공간 정답·안전중단·복구·비용을 읽는다. comparison 관측과 fault 원문에서 공유 계획/검토 hash, 실행 로그, native/compiler/LLM 검출 경로를 연결한다.
4. Reliability registry와 gap audit는 감사일·커밋 당시의 구현 상태로 표시한다. 최신 운영 구현 완료로 자동 해석하지 않는다.
5. 개요는 동결/관측/인간 GOLD/holdout/반복/과학적 완료를 별도 카드로 보여준다. Benchmark는 검색·범주 필터와 사례 상세, 방법 비교는 8방법 설명·동일 계획 분기·공유 hash 상세를 제공한다.
6. RQ1은 조건별 기계 검사와 인간 의미 정확도 미측정, RQ2는 오류 유형별 검출·오승인·오차단, RQ3는 실행과 공간 정답·동등 표현군·범위 밖 안전중단 및 Q5-03 실행 추적, RQ4는 의미 보존 복구와 빈 Oracle 제한, RQ5는 관측 비용을 보여준다.
7. 실행 이력은 중단 원본과 완료 관측을 구분한다. 한계/재현성은 source path·SHA256·버전·상태·원문 링크를 제공한다. 없는 로컬 artifact는 자료 없음이며 null을 0으로 바꾸지 않는다.

## 실제 검증

- Python adapter 회귀 8개 통과, Node UI 계약 8개 통과. 독립 감사의 중복 실행은 합산하지 않는다.
- 독립 HTTP 검증: HTML/JS 200, static/artifact 경로 탈출 404, POST 405, 허용 원문 text/plain. source SHA256 및 18개 공유 계획 hash 일치 확인.
- 주검증자가 실제 인앱 브라우저에서 개요, RQ2 오승인/오차단·검출 경로, RQ3 공간 분모, 사례 상세를 확인했다. 1440×1000 및 기본 좁은 화면 배치를 확인했고 브라우저 오류 로그는 없었다.
- 검증 중 모델 digest 키, 과거 감사 상태 표시, graph 경로 경계, 부산항 공간 GOLD 가용성 표시 오류를 수정했다. P0의 미사용 LLM 검출은 null로 보존한다.
- 화면 증거는 `outputs/scie_results_ui_verification_20261102/`에 보존한다. 운영·실험 소스 동결 281파일 해시를 별도로 대조한다.

## 한계와 다음 확인

- 독립 인간 GOLD, holdout, 최종 반복 및 전체 RQ 결론은 미완료다. UI는 이를 보완하거나 점수를 생성하지 않는다.
- 본 UI는 read-only 연구 설명 화면이다. 원문이 많은 최초 조회는 수초가 걸릴 수 있다. 서버는 실행 재개/승인/채점/실험 시작 기능을 제공하지 않는다.
- 새 실험 최종 검증 후 인덱스를 갱신하면 새 완료 결과를 읽는다. 원본 run이 로컬에 없는 다른 컴퓨터에서는 누락을 표시한다. 원시 run은 Git 추적 소스와 별도 보존한다.
