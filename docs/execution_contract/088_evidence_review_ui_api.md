# Phase 8.8 Evidence 후보 검토 UI/API

## 목적

Phase 8.7에서 만든 파일 기반 승인 gate를 통합대시보드에서 사용할 수 있도록 UI와 API를 연결한다. 검토자는 후보 evidence를 조회하고, 승인/반려/보류를 저장한 뒤 승인 항목만 registry 병합 dry-run 또는 실제 병합으로 넘길 수 있다.

## API

기본 prefix는 `/api/v1`이다.

- `GET /evidence-candidates`
  - 후보 목록 조회
  - query: `partition`, `decision`, `review_required`, `limit`, `offset`
- `GET /evidence-candidates/{evidence_id}`
  - 단일 후보와 현재 decision 조회
- `POST /evidence-candidates/{evidence_id}/decision`
  - decision 저장
  - body: `decision`, `reviewer`, `reason`, `review_required_accepted`, `verification_status_override`
- `POST /evidence-candidates/apply`
  - 승인 항목 registry 병합 실행
  - body: `write`, `overwrite`

## UI

`services/orchestrator/static/index.html`의 통합대시보드 하단에 `Evidence 후보 검토 및 승인 Gate` 패널을 추가했다.

기능:

- KG/RAG/법령 evidence partition 필터
- 승인/반려/보류 상태 필터
- `review_required` 필터
- 후보 목록 및 상세 edge 후보 확인
- 검토자, 사유, review_required 수락 체크 입력
- 승인/반려/보류 저장
- registry 병합 dry-run
- 승인 항목 registry 병합

## 안전 규칙

- `approved` 저장 시 검토자와 사유가 필요하다.
- `review_required: true` 후보는 `review_required_accepted: true`가 없으면 승인할 수 없다.
- registry 병합은 별도 버튼으로 실행한다.
- 실제 write 병합은 브라우저 confirm을 거친다.
- UI 승인도 실행 권한을 직접 만들지 않는다. 실행 권한은 registry/schema adapter와 ExecutionValidator가 결정한다.

## 현재 제한

- 로컬 가상환경 import 테스트는 기존 오케스트레이터 import 경로의 `sqlite3` DLL 문제와 Ollama embedding 연결 시도로 완료하지 못했다.
- 정적 HTML의 기존 한글 문자열 일부는 원천 파일 인코딩 문제로 깨져 있다. 신규 패널은 정상 한글로 추가했지만, 전체 UI 인코딩 정리는 별도 단계가 필요하다.

## 다음 단계

Phase 8.9에서 승인 evidence와 실제 RAG 검색 결과, KG edge, registry 상태 간 충돌을 탐지하는 deterministic validator를 추가한다.
