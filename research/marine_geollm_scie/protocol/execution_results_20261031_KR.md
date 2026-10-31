# 2026-10-31 전체 18문항 K1 실행 비교 결과

## 완료 범위

- 원천 문서 임베딩23,215/23,215, NULL0, 차원1024. 새 연구DB scie_model_v3 여섯 관계 snapshot 검증.
- 운영 graph18문항 + B0–B4 각18문항(90조건) 실행 및 사후 보고서 생성 완료(04:39KST).
- 원시 결과: `../runs/20261030_full_execution_v5/`. 비교 보고서: [comparison_KR.md](../runs/20261030_full_execution_v5/report/comparison_KR.md).
- 원본 실행·실패를 보존하며 아래 수정으로 사후 교체하지 않는다.

## 관측과 해석

Graph 상태는 COMPLETED10, BLOCKED4, NEEDS_CLARIFICATION3, PARTIAL1이다. 상태는 정답이 아니다. baseline은 schema completed84/invalid_response6이며 후자는 JSON 파싱 실패4건과 필수필드 누락2건이다. 도구 반환과 입력계약 통과 역시 의미정답이 아니다.

구성요소 전체 검사통과는 B1의1행, B0/B2/B3/B4는0행이다. 각 방법3행은 미측정을 포함한다. P18행은 평가용 구조 매핑이 없어 미측정이며 이를 0점으로 비교하면 안 된다. 독립 human GOLD/holdout이 없고 내부 검색·호출예산이 달라 모델우열/전체 의미정확도를 주장하지 않는다.

## 중요한 오류

1. P의 Qwen generate11회가 semantic prior 기본2.5초 제한으로 전부 timeout/client disconnect했다. 문항 임베딩22회 성공과 구분한다. 모델활성화 설정이 성공생성이나 모델효과 검증을 의미하지 않는다. 연구용 timeout을 명시한 별도 조건·새run이 필요하다.
2. 정의/속성 질의의 지명/반경 fast path 오진입 및 불필요 원천장애 전파.
3. 공개 S-101 제한코드 설명을 제한구역 키워드만으로 비공개로 차단.
4. AOI 없는 공간 intersects가 문서검색으로 완료되고, 등대+Wreck 복합이 Wreck만 실행하고 완료됨.
5. AnchorageArea 부분문자열 정규화 결함. 해당 사례는 원문 대체경로로 FC 답변이 나와 최종 실패와 구분해야 한다.

Q4 세 동등표현은 각각5km/11건을 반환했다. 연구 원천의 부산권 S-101 subset은 독도 위험객체 coverage를 증명하지 않는다. 원천누락과 구현오류, 입력확인 요청의 타당성을 각각 검토한다.

## 후속

별도 에이전트가 연구 timeout 조건과 정책오차단 수정을 담당한다. 기존 운영 기본timeout과 원본K1은 보존한다. 수정 후 새 실행과 실제API 정상/부정 확인이 필요하다. 나머지 fast path/공간의무/복합coverage 및 K5·독립holdout·recovery·ablation은 미완료다. 본논문 실험 전체 완료로 간주하지 않는다.
