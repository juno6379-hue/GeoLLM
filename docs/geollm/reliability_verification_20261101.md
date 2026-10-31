# 신뢰성 정책 구현과 통합 검증

운영/논문 분리 기준은 [delivery policy](reliability_delivery_policy.md), 전 사례 감사는 [구현 감사](../../research/marine_geollm_scie/reliability/IMPLEMENTATION_GAP_AUDIT.md), 논문 결과 위치는 [결과 안내](../../research/marine_geollm_scie/RESULTS_INDEX_KR.md)를 따른다.

세 에이전트가 정책·사례 레지스트리, 운영 감사/수정, 연구 동결 검사 구현을 나누어 수행했다. 주 에이전트가 코드 diff, 40개 사례 ID 일치, 감사 소스 hash, immutable GOLD manifest hash, 단위 회귀와 실제 API를 다시 검증했다.

## 이번 구현

- 연구용 40개 신뢰성 사례와 30개 대표 fault/control 명세, 정책 YAML·한글 판단표·감사 JSON. 30개는 NOT_EXECUTED 명세이며 모델 실험 30회가 아니다.
- immutable bundle의 파일 집합/사례/hash 검증 및 외부 manifest hash 고정 지원. 기존 bundle 불변, manifest SHA256 `feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c`.
- 연구 결과 검사 함수: 8방법 관측 집합, 같은 실행 조건, shared plan/review, P0/H lossless, B0 도구 미사용. 실제 runner/report 연결은 아직 남았으며 이 함수 자체를 RQ 완료로 해석하지 않는다.
- 운영 radius/bbox에서 coverage 미검증 0행을 확정 빈 결과로 내보내던 후처리 수정. `PARTIAL/NO_EVIDENCE`, `UNKNOWN`, `count/total_count=null`; 실제 조회는 `observed_total_count=0`, `query_execution_succeeded=true`로 보존. client의 임의 VERIFIED flag는 무시한다. 실행 전 coverage 차단 구현은 아니다.

## 주 에이전트 검증

운영 관련 162 passed(21.52초), 연구 관련 39 passed(8.60초). 별도 에이전트 회귀57개와 중복되므로 합산하지 않는다. 최초 운영 회귀에서 기존 0행 SUCCESS_EMPTY 기대 2곳을 새 의미 계약에 맞춰 갱신했다. 양성·빈 페이지·반환 객체수 회귀는 유지했다.

실제 backend 재기동 후 `/health` HTTP200, 컨테이너 수정 소스 hash 일치 확인. 최초 준비 전 health 오류는 준비 이후 정상화됐으며 전체 서비스 SLO 검증은 아니다.

| 실제 SSE 사례 | 결과 | 판단 |
|---|---|---|
| POINT(150 0), 1km, 최초 v1 | FAILED / DB_TIMEOUT, 73.735초 | 미통과 원본 보존. 0건으로 바꾸지 않음 |
| POINT(129.075 35.075), 1m, v2 | PARTIAL / NO_EVIDENCE, observed_total_count=0, 확정 total=null, 20.672초 | 미확인 coverage와 관측 0행 구분; 본문/claims/하위작업 확인 |
| 같은 부산 좌표, 1km, v2 | COMPLETED / SUCCESS, 25건, 22.5초 | 정상 결과 보존 |
| 같은 좌표, 60km, v2 | BLOCKED, 11.032초 | 상한 초과 비승인 |

원본 `outputs/reliability_empty_runtime_20261101_v1`, `outputs/reliability_empty_runtime_20261101_v2`. v2 검사는3/3, source_unchanged=true. v1 시간초과는 별도 잔여 오류이며 v2 성공으로 해결됐다고 주장하지 않는다. 브라우저 화면 조작은 이번 검증에 포함되지 않았다.

후속 읽기전용 DB 진단(`v1/read_only_diagnosis.json`): 실제 원천은 materialized view이며 geometry GiST 인덱스가 존재한다. 축약 공간 predicate는 부산1m 0행/0.183초, 최초 실패 좌표1km도 0행/0.056초의 Index Scan이었다. 실제14종 코드 사전검증은 56쌍/1.051초로 반환했다. 이 진단에서는 시간초과가 재현되지 않았고 원본에 실패 statement 계측이 없으므로 정확한 원인은 미상이다. 먼 좌표의 전역 스캔으로 단정하지 않는다. DB·인덱스·timeout 변경은 하지 않았다.

재현:
```powershell
.venv/Scripts/python.exe -m scripts.check_spatial_empty_coverage_runtime --output outputs/reliability_empty_runtime_NEW --empty-geometry 'POINT(129.075 35.075)' --empty-distance 1
```

## 남은 작업과 다음 실행

1. DB_TIMEOUT의 정확한 SQL 단계·실행계획 재현. 위치와 무관한 Feature/code 전체 view 검증 쿼리도 있으므로 좌표만 원인으로 단정하지 않는다.
2. 권위 coverage 원천(대상/공간/시간/판) 검증과 실행 전 Validator gate. 현재 UNKNOWN인 결과를 충분한 원천 확인 없이 SUCCESS_EMPTY로 되돌리지 않는다.
3. geometry/경계/default/시설 dedup·복합 evidence·recovery 의미 보존 계약을 운영 전 경로로 확장하고 각각 실제 API 검증.
4. 변경된 production source를 포함한 새 동결 실행 조건으로 GOLD v2 8방법 전체 실행. 기존 K5 raw를 재사용하지 않는다. 동일 fault/recovery 실행 및 RQ1~RQ5 분석·독립 GOLD 검수는 미완료다.

**이번 완료는 정책 체계·감사·특정 빈 결과 오류 수정과 검증이다. 전체 운영 시스템 또는 논문 실험 완료가 아니다.**
