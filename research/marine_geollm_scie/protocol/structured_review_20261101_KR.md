# 연구용 LLM Review 응답 계약 수정

기존 v2 fault의 9회는 timeout이 아니라 HTTP 완료/stop 뒤 최상위 plan만 반환한 형식 실패였다. `invalid, reason, plan`을 요구했지만 전송은 `format="json"`으로 JSON 문법만 지정했다. 중첩 plan schema를 본 모델이 plan 자체를 출력한 원문을 보존했으며, 원인 중 전송 제약 부족을 보완한다. 모델 내부 판단 원인을 확정하는 주장은 아니다.

새 `structured_review_v1.json`은 연구 전용 계약이다. [Ollama generate 문서](https://docs.ollama.com/api/generate)와 [structured outputs 문서](https://docs.ollama.com/capabilities/structured-outputs)가 지원하는 JSON schema 객체를 format에 전달한다. 프롬프트도 동일 wrapper를 명시한다. 완료 조건은 done=true/stop과 엄격한 JSON/schema 검증이며 bare plan, 잘못된 boolean, 누락·추가 필드, 비유한 수, 절단은 실패로 남긴다. 사후 wrapper·verdict 생성과 재시도는 없다.

main 비교와 fault 비교 모두 같은 helper를 사용한다. B4/H는 각 사례당 단 한 번 생성한 검토·계획을 공유한다. 최초 B3 생성 조건과 P0 무손실 컴파일은 바꾸지 않는다. 검토 예산은 기존과 동일하게 768 출력 토큰, 180초, temperature 0.2, context 8192, retries 0이다. schema/hash/version/budget/prompt/원응답/토큰/시간을 기록한다. main reviewer에는 최초 계획의 동일 공개 입력·근거·도구 계약을 제공하고 GOLD 답안은 제공하지 않는다.

## 개발 검증과 제한

`outputs/structured_review_development_20261101_v1`에 독립 개발 호출 3개와 원본 v2 9개 hash 감사를 보존했다. 세 호출 모두 schema 통과/stop: CONTROL 174토큰 48.867초, UNIT_TYPED 119토큰 19.784초, MISSING_GEOMETRY 222토큰 36.087초. 각 사례 한 번만 호출했다.

형식 개선은 정확도 개선과 다르다. 모델은 정상 control을 invalid=true, 누락 geometry를 invalid=false로 답했다. 이 오류를 고치기 위한 재시도·정답 주입·사후 verdict 변경을 하지 않았다. 단위 오류 invalid=true 하나로 의미 검토 능력을 일반화하지 않는다. 개발 입력은 최소 공개 context이며 본 실험 전체 source profile과 같지 않으므로 논문 비교 결과로 재사용하지 않는다.

이후 새 source/profile/schema를 동결하고 8방법 전체를 다시 실행해야 한다. 이전 v2 결과와 원문은 덮어쓰지 않는다. 운영 Qwen 정책 변경이나 독립 인간 GOLD 완료를 의미하지 않는다.
