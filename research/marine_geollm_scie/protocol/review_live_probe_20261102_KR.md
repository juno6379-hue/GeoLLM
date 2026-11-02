# 초기 LLM 검토 모순 — 실제 개발 probe 검증

2026-11-02 KST. **개발 검증이며 논문 8방법 비교·독립 홀드아웃 결과가 아니다.** 기존 v6 결과를 재채점하지 않았다. 운영 coverage·GIS 실행과 분리해 검토 모델의 초기 판정과 수정안 사용 가능 여부를 관측했다.

## 고정 조건

- 모델 `qwen2.5:1.5b`, digest `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`, seed 42.
- `structured_review_v3_initial_plan_consistency`, 1회/사례, 768 출력 토큰, timeout 180초, temperature 0.2, context 8192, 재시도 0.
- 정상 1개와 CRS·반경·기준 geometry 누락 3개. 개발 입력은 `POINT(129.08 35.08)`, 1500m이며 범위 정보는 합성 개발 입력임을 명시했다. 실제 source coverage의 권위를 검증한 실험이 아니다.
- warmup 없음. 4개 호출 순차 실행, 실패도 전체 분모에 포함. 원본/GOLD/holdout을 입력 생성에 사용하지 않았다.
- 원시 응답·prompt·모델 정보·실행 코드 hash·초기 계획·제안 계획·consistency 결과: `outputs/review_live_development_20261102_v1`.

## 실제 관측

| 개발 사례 | 모델 초기 invalid | 제안 계획의 변경 | 새 검토 계약 결과 | 지연 초 |
|---|---|---|---|---:|
| 정상 | false | 없음 | 사용 가능 | 87.89 |
| CRS 불일치 | false | EPSG:3857→4326, 기준 geometry 삭제 | `REVIEW_UNDECLARED_PLAN_CHANGE`, 사용 불가 | 40.09 |
| 반경 불일치 | false | 4500→1500m | `REVIEW_UNDECLARED_PLAN_CHANGE`, 사용 불가 | 39.74 |
| 기준 geometry 누락 | false | 없음 | 사용 가능, 오류 미검출 | 61.54 |

4개 모두 `completed/stop`이며 289~306 출력 토큰으로 끝났다. timeout·절단 문제는 없었다. 모델 digest와 실행 코드 hash는 전후 일치했다. 모든 초기 검사 항목을 pass로 보고했다.

초기 오류 판정은 **오류 0/3 검출, 정상 1/1 정상 판정**이다. 새 계약은 무보고 수정 2개를 실제 모델 응답에서 차단했지만 이 둘을 LLM 오류 검출 성공으로 바꾸지 않는다. 기준 geometry 누락을 그대로 정상 판정한 응답은 이 구조적 모순 검사로 검출되지 않는다. `review usable`은 실행 허가가 아니며 후단 Deterministic Validator가 여전히 필요하다.

## 결론과 남은 작업

이번에 실제 검증된 것은 **모순된 수정안을 실행에 사용하지 않는 코드 경로**다. LLM 자체의 초기 오류 판정 정확도 개선은 확인되지 않았다. CRS 사례에서는 좌표계 수정 외에 기준 geometry를 삭제하는 추가 문제가 발생했으며 거부된 원문을 보존했다.

새로운 prompt를 같은 4문항에 반복 튜닝하지 않았다. 초기 진단과 수정 생성을 별도 호출로 분리하는 방식은 추후 별도 후보 조건으로 검토할 수 있지만, 호출 수·비용·방법 정의가 달라지므로 현재 공식 비교 조건으로 자동 승격하지 않는다. 다음 전체 비교에서는 원시 오류 판정, 모순 계약 거부, 실제 실행/복구를 각각 보고하고 누락·실패를 분모에서 제외하지 않는다.

재현 명령(실제 모델 4회 호출, 새 출력 경로 필요):

```powershell
.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.development_review_probe --output outputs/review_live_development_NEW --execute
```
