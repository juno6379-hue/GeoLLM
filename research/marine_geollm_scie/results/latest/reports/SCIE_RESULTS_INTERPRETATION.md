# SCIE Results 해석 — NOT_READY

## 가장 강한 연구발견 5개
확정 연구발견은 0개다. 대신 검증 가능한 관측 5개를 구분한다.
1. 계획 출력과 실제 GIS 실행은 다른 실험이다.
2. 명시적 실행 성공과 공간정답의 일치 여부는 별도로 측정해야 한다.
3. DRAFT fault label에 대한 진단은 승인 오류검출 정확도가 아니다.
4. 비용 측정은 제공된 token·latency만 사용하며 미제공값을 0으로 만들지 않았다.
5. 현재 개발 노출 사례는 독립 holdout을 제공하지 않는다.

## 가장 예상 밖의 결과 3개
전체 방법 성능의 예상 대비 차이를 판정할 수 없다. 감사상 중요한 세 제한은 완전한 의미·근거·fault 정답 미확정, 공간 oracle의 제한된 대상 범위, P0/P1/H와 recovery 대조군 부재다.

## 실패 사례 유형
timeout/error 원본 행을 보존했다. 생성 성공, JSON schema 통과, GRAPH_RETURNED, SQL 일관성을 의미·공간정답으로 바꾸지 않았다.

## Reviewer가 공격할 가능성이 높은 한계
계획 표본은 영어5·한국어1의 편의 부분집합, K=3, holdout=0, 사후 조건 라벨이다. 작은 equivalence-group 수 때문에 CI가 불안정하다. 서로 다른 snapshot·하드웨어·component 범위를 합친 우열 비교는 불가능하다.

## 추가 실험 필요 여부
필요하다. 현재 승인 범위를 넘어 완전한 의미·실행계약·근거·fault 평가 참조를 확정하고, K=5 matched B0–B4/P0/P1/H, 독립 holdout, recovery 전후 의미·공간 oracle, 실패유형별 ablation을 확보해야 한다.

## 현재 결과로 주장 가능한 문장
기존 파일럿의 관측 비용과 결측 및 component 범위를 재현 가능한 RQ 형식으로 대조하였다. 확보된 사용자 승인 공간 참조는 그 대상·snapshot에 한정해 내부 비교하였다. 완전한 참조와 matched 비교조건·holdout이 없어 전반적인 기술 효과 판정은 유보하였다.

## 현재 결과로 주장하면 안 되는 문장
Ontology가 RAG보다 우수하다. P1이 silent failure를 줄였다. Recovery가 의미를 보존한다. 한글 의도분류 정확도나 holdout 성능이 입증되었다. 표 생성만으로 논문 Results가 완료되었다.


## 이번 분석의 승인 수준
사용자 승인 AI보조 참조 18건 / 독립 전문가 승인 참조 0건
사용자 승인은 AI 기원·파일럿 노출·불확실성을 없애지 않는다. 공간 참조는 일치하는 snapshot과 oracle hash가 있을 때만 비교한다.

확보한 공간 객체 참조는 3개 사례이며 Q4 동등질의군 범위이다. 그 밖의 공간 정답 coverage는 미확정이다. 확정 의미 label 집합 0건, 부분 QEC 필드 8건, 필수 근거 집합 0건이며 전체 의미·계획·근거 정확도로 대체하지 않는다.

## 실제 내부 공간 대조 관측
- LIVE_Q4_AFTER_LOCATION_FIX: 실행 3/3, SCR=1.0, CGE=1.0, SSFR=0.0, 독립 equivalence group=1.
- LIVE_Q4_BEFORE_LOCATION_FIX: 실행 2/3, SCR=0.6666666666666666, CGE=1.0, SSFR=0.0, 독립 equivalence group=1.
이는 승인된 고정 원천과의 내부 대조이다. 영어 표현의 실행 중단은 silent spatial failure와 다르다. 한 동등질의군의 표현별 결과로 방법 전체의 신뢰성 향상이나 통계적 유의성을 주장하지 않는다. 개발자의 코드 수정 후 재실행은 runtime bounded recovery의 성공 사례가 아니다.
