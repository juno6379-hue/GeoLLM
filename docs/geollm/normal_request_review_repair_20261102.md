# 정상 요청 오차단·LLM 초기 판정 모순 보완 인계

2026-11-02 KST. 사용자 요청에 따라 운영 보완, 연구 검토 계약 보완, 독립 감사를 분담했다. **새 8방법 비교는 다음 접속에서 시작하며 이번에는 실행하지 않았다.**

## 운영 보완과 아직 남은 사항

S-101의 검증된 원천 목록에 한정한 검색을 허용하는 `s101_exact_inventory_v1` 계약을 추가했다. 서버에 고정된 inventory bytes/hash, 전체 객체 ID·속성·EWKB, snapshot hash와 현재 DB를 비교한다. 원천에 명시된 DataCoverage polygon이 검색 영역 전체를 포함해야 한다. 원천 객체의 bbox를 coverage로 만들지 않는다.

일반적인 bounded 검색도 서버 계약의 `default_inventory_listing=true`가 있을 때만 SOURCE_CORPUS로 허용한다. 전체성·최근접 요청은 이 경로로 축소하지 않는다. UNKNOWN/범위 밖/변조/미등록 원천은 계속 차단한다. 결과는 원천 목록 기준임을 표시하고 실세계 완전성이나 부재를 보증하지 않는다.

**실제 registry/원천 manifest는 등록하지 않았다.** 실제 DataCoverage와 live DB의 대조를 끝내지 못했기 때문이다. 따라서 현재 서비스의 정상 S-101 요청 오차단이 해결됐다고 주장할 수 없다. 연구의 ResearchBindingAdapter 또한 별도 범위 권위 경로 연결이 필요하며, 운영 generic 코드 추가만으로 연구 CONTROL의 False Block이 없어지지 않는다.

Docker Desktop은 기동을 시도했지만 `Docker/run/dockerInference` 소켓 파일에 접근하지 못해 실패했다. 이동도 실패했고 삭제 작업은 자동 승인 검토가 `blocked by policy`로 거부했다. 우회 삭제·DB/컨테이너 초기화는 하지 않았다. Docker/DB/API 복구 후 실제 정상·부정 질의 검증이 다음 필수 단계다.

## 연구 검토 계약 보완

초기 판정을 false로 반환하면서 실행·계약 필드를 수정한 응답을 사용 불가로 처리한다. 원시 verdict와 checks, 원본·제안 계획 hash, JSON 변경 경로를 보존한다. B4/H는 같은 실패 receipt를 공유하며 수정안을 실행하지 않는다. 이를 invalid=true나 LLM의 오류 검출 성공으로 바꾸지 않는다.

기존 v6의 9개 검토를 읽기 전용 재현한 결과 무보고 수정 3건(CRS·음수 반경·잘못된 반경)을 확인했다. 나머지 5개 오류를 LLM이 정확히 판단하게 됐다는 증거는 없다. 모델 호출·GOLD 변경·과거 결과 재채점 없이 코드 경로와 계약을 검증했다. 실제 모델 개선은 새 동결 비교에서 측정한다.

새 prompt/version/protocol과 평가계약은 동결에 포함해야 한다. 이전 v6 run/GOLD/snapshot 513개 파일이 독립 해시 검사에서 유지됐다. 홀드아웃 내용은 개발에 사용하지 않았다.

## 중단된 PDF 작업

실제 worker가 없음을 확인했다. 2,215개 중 948개 checkpoint는 계획·입력·모델 digest·1024차원 검증에 통과했고 1,267개가 남았다. 최종 embedded.json은 없다. worker.lock은 이전 계획 hash와 일치하지만 현재 worker 부재를 다시 확인한 뒤 안전하게 보존·재개해야 한다. 이번에는 모델 호출을 재개하지 않았다.

증거: `outputs/coverage_review_repair_20261102_independent/`. 기존 FC 적용 후 새 receipt current 게시도 아직 남아 있다.

## 다음 접속

[새 동결 v7 실행 절차](../../research/marine_geollm_scie/protocol/eight_execution_v7_next_session_KR.md)를 우선 확인한다. 순서는 Docker 복구 → 원천·현재 DB 검증/등록 → 운영 대표·부정 API → 연구 scope 연결 검증 → 진행 중 데이터 revision 정리 → 새 동결 8방법 전체 비교다. gate를 통과하기 전에는 새 실험을 시작하지 않는다.

관련 코드와 테스트는 운영/연구를 나누어 로컬 커밋한다. 이번 요청에는 추가 GitHub push가 없으므로 이전 게시 커밋과 구분한다.

최종 부모 통합검사: 운영 관련 205개, 전체 연구 449개 통과. 독립·부분 실행 수치와 중복 합산하지 않는다. 독립 감사에서 원천 polygon CRS/좌표 범위, 미완성 receipt의 빈 결과 보호 우회 문제를 찾아 수정·회귀검증했다. 새 실행 계약 v5가 review protocol v3를 참조하며 양쪽 파일 hash와 실제 런타임 version/schema/budget이 다르면 profile 준비 단계에서 차단한다.
