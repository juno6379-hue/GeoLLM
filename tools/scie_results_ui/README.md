# 논문 결과 전용 UI

운영 GeoLLM과 분리된 읽기 전용 파일 기반 뷰어입니다. 운영 라우터, DB, Ollama를 호출하거나 수정하지 않습니다.

## 실행

저장소 루트에서:

```powershell
.venv/Scripts/python.exe -m tools.scie_results_ui.server --port 8001
```

화면: http://localhost:8001/research/scie-results

JSON: http://localhost:8001/research/scie-results/api/dashboard

서버는 127.0.0.1에만 바인딩합니다. POST/PUT/PATCH/DELETE는 405입니다. 원본 열기는 adapter가 읽은 연구 artifact만 허용하며 텍스트로 제공합니다. 운영 8000 포트의 재시작이나 변경이 필요하지 않습니다.

## 근거 우선순위

`research/marine_geollm_scie/RESULTS_INDEX_KR.md`의 **최신 완료** 행이 결과 선택 기준입니다. 현 인덱스에서는 v5가 선택되고 v6는 별도 진행 현황입니다. v6 worker가 종료돼도 검증 인계와 인덱스 갱신 전에는 v5를 자동 대체하지 않습니다. 과거 `results/latest`와 6방법 K5는 합산하지 않습니다.

- `benchmark/gold_v2_immutable_20261101_v1`: manifest, 질의, 답안계약, 독립 SQL/GIS 검산 근거.
- 선택 run의 `report_with_faults/summary.json`: RQ별 기계 계약과 비용.
- 선택 run의 `comparison/observations.jsonl`: 사례별 실행 기록과 공유 plan/review hash.
- 각 run의 status/comparison manifest/graph 물리 행 수/fault rows: 수집 현황. 행 수는 평가 성공 수가 아닙니다.
- `reliability/reliability_case_registry.yaml`, `reliability_gap_audit.json`: 정책 및 기록 시점 운영 감사. 최신 운영 수정 완료를 자동 의미하지 않습니다.

각 source에는 경로, SHA256, 버전, 조회 생성 시각, 상태, 제한을 제공합니다. 진행 중 JSONL 마지막 불완전 행은 PARTIAL로 표시하며 집계에서 제외합니다. 독립 인간 GOLD, 미측정 비용과 null은 0으로 바꾸지 않습니다. 공간 실행과 공간 정확도, 범위 밖 안전중단은 별개입니다. Q4 표현 변형은 독립 문제 여러 건으로 해석하지 않습니다.

## 검증

```powershell
.venv/Scripts/python.exe -m pytest tools/scie_results_ui/tests -q
```

UI 구현/뷰어는 `tools/scie_results_ui/`에 격리되어 실행 중인 연구 runner의 동결 소스와 운영 화면을 수정하지 않습니다. 본 UI는 논문 최종 정확도 또는 운영 릴리스 승인 대시보드가 아닙니다.
