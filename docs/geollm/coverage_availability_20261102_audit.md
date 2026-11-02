# Coverage 가용성 수정 독립 운영 감사 — 2026-11-02

이 감사는 개발 Q4 및 기존 운영 재현 사례에 한정한다. holdout 폴더나 내용을 읽지 않았고 연구 결과를 수정하거나 새 연구 모델 실험을 시작하지 않았다. S-101 승인 범위 구축과 지명 원천 목록 조회 복구는 서로 다른 작업이다.

## 확인한 수정 경계

- `CORPUS_VERIFIED`는 고정 CSV의 전체 행·속성·provenance·좌표변환과 실제 relation의 일치다. `ADEQUATE` 지리 범위가 아니며 geographic coverage는 UNKNOWN, absence_certified는 false여야 한다.
- 예외는 정확한 marine_gazetteer relation/geometry와 반경 연산·대상 집합으로 제한된다. S-101, 혼합 대상, 최근접, 원문의 전체성 요구, hash/실제 원천 불일치는 예외 대상이 아니다.
- query transaction 안에서 원천 identity를 재검사해야 한다. 사전검사 이후 자료 변경이 가능하므로 사전 receipt만으로 조회를 승인하지 않는다.
- 결과 수는 반환 행 수다. 기존 LIMIT 이후 `total_count=len(features)`는 완전한 총계로 오해될 수 있어 `total_count=null` 및 count_scope/상한 설명으로 변경됐다. 실제 해역의 전체 지명이나 부재를 보증하지 않는 설명이 필요하다.

## 독립 수집기

`scripts/check_coverage_availability_20261102.py`는 기존 개발 Q4 원문 3개(5km/5000m/영어), 기존 독도/부산 S-101·영역누락·정의 사례 및 별도 운영 전체성 부정사례를 수집한다. Q4 원문 출처는 `outputs/scie_q4_live_20261030_after_location_fix/api_rows.jsonl`이며 신규 평가셋이 아니다.

새 출력 디렉터리에 raw SSE와 소스 SHA-256, 개별 계약 검사를 보존한다. `--verify-only`는 저장 관측을 재확인하며 API를 호출하지 않는다. 명령:

```powershell
.venv/Scripts/python.exe -m scripts.check_coverage_availability_20261102 --output outputs/coverage_availability_20261102_<새이름>
```

이 수집기는 server receipt를 검사한다. 독립 SQL 전역 계측·브라우저 UI·인간 의미 채점·연구 정확도를 측정하지 않는다. 누락 execution 필드를 false로 만들지 않으며, 차단 count=0 및 관측 timeout을 성공으로 통과시키지 않는다.

## 검증 상태

- 감사 수집기 보호 테스트 `tests/unit/test_coverage_availability_20261102.py`: 4 passed. missing receipt, 차단 count=0, 관측 오류, 기존 Q4 차단을 가용성 성공으로 오판하지 않는지 확인했다.
- 기존 v3 raw를 read-only 대조하여 S-101 preflight와 문서 정상 receipt를 확인했다. 이는 새 수정의 실제 API 검증이 아니다.
- 실제 API `outputs/coverage_availability_20261102_v2`의 8개 관측과 계약 검사가 모두 통과했다. 기존 개발 Q4 세 표현은 각각 같은 11개 지명을 반환했고, 원천 CSV 1,146행 identity·원천 한정 설명·실행 로그·미확정 전체 건수가 응답에 남았다. 전체성 요구 1건과 미승인 S-101 공간 요청 2건은 차단, 선택영역 누락은 추가입력, Wreck 정의는 문서 응답을 완료했다.
- 부모가 `--verify-only`로 저장된 8개 raw/현재 소스 hash를 재검사했다. 소스 변경 없음. 첫 v1은 재시작 직후 RemoteDisconnected로 실패한 원본을 보존했다. 이후 localhost/127.0.0.1 health 200을 확인하고 v2는 127.0.0.1로 별도 수집했다. 연결 실패를 모델·라우팅 실패로 집계하지 않는다.
- 신규 transaction 테스트 중 발생한 실패는 mock이 place authorization까지 항상 true로 덮은 fixture 오류였다. fixture 수정 후 4개가 통과했고 운영 소스 변경은 없었다. 실제 DB 예외는 성공이나 검색 0건으로 표시되지 않는다.
- S-101 승인 원천 범위 구축은 여전히 미완료다. 부산의 정상 가능한 요청도 이 이유로 차단되므로 정상 오차단 전체 해결로 주장하지 않는다. “전체 데이터에서” 같은 원천 내부 전체성 표현도 현재 보수적으로 차단한다.
- 독립 감사 에이전트가 API 수집까지 수행했으나 마지막 문서 정리 때 모델 capacity 오류로 종료되어, 최종 저장 raw 재검증과 문서 정리는 부모가 수행했다.

## Dataset 검증과 논문 분리

이번 검증은 해양지명 CSV와 운영 relation의 일치다. 항로서지·소형선항만 안내정보 등 임베딩 문서 전체의 지명/위치/좌표 추출 정확성과 공간 객체 연결의 전수 검증을 뜻하지 않는다. 임베딩 완료와 위치 정보 검증 완료를 구분한다.

기존 논문 v6 결과·GOLD·홀드아웃 531파일은 hash가 그대로다. 홀드아웃은 hash 보존 확인만 하고 개발 입력/정답으로 사용하지 않았다. 이번 운영 API 검증으로 기존 v6 점수를 고치지 않으며, 향후 논문 비교는 새 시스템 동결 조건에서 별도 실행해야 한다. 홀드아웃 평가는 최종 시스템 동결 후에만 수행한다.
