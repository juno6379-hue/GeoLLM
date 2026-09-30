# Phase A 실행계약 재개·원천 검사 보완 — 2026-09-30

## 변경

- 일반 질의의 추가 입력 경로가 이전 계획/QEC를 남긴 채 checkpoint를 이어가던 문제를 수정했다. 반경·장소 외의 질의도 입력을 합친 뒤 revision을 올리고 계획, QEC, Agent 요청/결과, 검토 승인을 폐기해 다시 계획한다.
- 메모리 checkpoint가 사라졌으면 저장된 snapshot으로 같은 초기화를 수행한다. 둘 다 없으면 오류를 반환하며 이전 승인을 추정하지 않는다. 완료/차단/실패 작업에 추가 질의를 보내면 기존 계약대로 새 task ID를 만든다.
- Standard RAG의 원천 사전 검사를 실제 검색 SQL과 맞췄다. content/metadata/embedding 외에 chunk_id/source_id/source_sha256도 필수다. 원천·SELECT 권한·필수 열을 갖추지 못하면 실행 승인을 내리지 않는다.
- 실제 API 관측기에 선택적 task_id를 추가하고, 실행계약 smoke에 동일 작업의 반경 추가 입력·revision 증가·새 승인 확인을 추가했다.

## 검증

- 수정 전 인계 회귀: 175 passed, 77 warnings, 242.28s.
- 수정 후 같은 회귀와 신규 컬럼/재개 helper 사례: 179 passed, 77 warnings, 197.52s. 기준 실행에서 실제 소스를 수정하며 테스트하지 않았다.
- 일반 질의 stream route의 메모리/저장 snapshot 재개: 2 passed, 1 warning, 82.26s. 외부 도구 실행은 격리했으며 두 경우 모두 이전 승인 폐기와 revision 증가를 검사했다.
- 최종 소스로 `geollm_backend`를 재시작했다. DB·지도·ETA 컨테이너는 재시작하지 않았다.
- 실제 API 원본: `outputs/web-intent-audit/20260930-phase-a-runtime-v1.jsonl`. 이 출력은 런타임 자료이며 소스 커밋 대상이 아니다.
- 재시작 후 실제 API **6/6 통과**: 해운대구 이동·Wreck 정의·1km 검색 COMPLETED 및 ExecutionValidator 승인, 반경 누락 NEEDS_CLARIFICATION/미승인, 60km BLOCKED/미승인, 반경 누락 작업에 1km 추가 입력 시 동일 task ID·revision 2·COMPLETED·새 승인. UI 정적 자산과 검토 이력 API도 확인했다. 브라우저 렌더링 검증은 아니다.
- `git diff --check`, 변경 Python 파일 문법 검사를 통과했다.

## 남은 범위

- 이번 테스트 통과는 전체 저장소 테스트·의미 정확도·성능 SLO 통과를 뜻하지 않는다. API 관측 제한은 socket 180초/전체 300초이며 응답 지연 개선을 주장하지 않는다.
- 일반 RAG·사고 관계·시계열의 운영 원천을 사용하는 end-to-end 사례 확대, 권한/원천 변경 시의 실제 서비스 검증, UI 렌더링 E2E는 남았다. Phase A 전체 완료로 선언하지 않는다.
- AIS/Drone/Map 미구현 adapter, 실제 원천/기간/커버리지, 독립 human gold·calibration/holdout, QLoRA DEFER 상태는 유지한다.
- parser & Map_viewer 연동은 가능성 검토만 완료한 상태이며 이번 변경에 포함하지 않았다. 별도 관리자 UI와 사용자 피드백 변경은 보존한다.
