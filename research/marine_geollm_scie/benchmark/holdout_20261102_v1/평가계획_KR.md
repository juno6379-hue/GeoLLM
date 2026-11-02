# 예약 홀드아웃 — 최종 동결 후 평가 계획

개발 18문항과 별도 ID·질의·동등군으로 분리한 신규 18문항, 통제 오류 9+정상3=12사례, 복구 8사례를 준비했다. 모델 호출·실제 평가를 실행하지 않았다. 새 GOLD는 AI 작성·원본 근거 검증 단계이며 기존 개발 GOLD의 인간 승인을 자동 상속하지 않는다.

## 원본 근거 및 공간 검산

FC 2.0.0 실제 Feature 정의/geometry/attribute binding을 직접 추출했다. CSV 전체 행의 DMS를 파싱하고 6개 입력 좌표와의 WGS84 거리를 READ ONLY PostGIS ST_Distance와 별도 Vincenty로 비교했다. 허용 오차 0.01m, 원천 행 ID·거리·SQL·원본 hash를 보존한다. 범위는 2022 CSV 기록으로 한정하며 법적/실세계 완전성이나 운영 APPROVED coverage를 만들지 않는다.

## RQ별 실행

- RQ1: 신규 18문항×8방법. 질의 조건별 과업·근거·인간 의미 정확도를 분리한다.
- RQ2: 12계획×B4/P0/H, 동일 초기 계획/검토 hash. 정상3 사례를 False Block 분모에 포함한다.
- RQ3: 6개 독립 좌표/조건별 공간 Oracle. 실행 성공·객체집합/거리 정답·silent failure를 분리한다.
- RQ4: 복구8사례×B4/H. 명시된 요청만 복원 가능; 원요청에서도 source/reference가 없는 2사례는 질문하고 미실행해야 한다. 실제 비어 있지 않은 source-bound 객체집합과 의미 보존을 동시에 검사한다.
- RQ5: latency/token/tool/SQL·False Ready/False Block. 공유 생성 비용과 단독 비용을 구분한다.

## 실행 전 필수 gate

1. 새 홀드아웃 GOLD를 인간 검수하고 결과·검수자·일시를 별도 기록한다.
2. 개발 수정 후 코드/model/prompt/data/evaluator hash와 동결일을 기록한다. freeze_artifact_paths의 실제 파일 SHA와 검증된 model_receipt_path/digest를 확인하며 임의 64자리 문자열만으로 통과하지 않는다.
3. final_freeze_receipt_TEMPLATE.json을 별도 경로로 복사해 채운다. benchmark manifest hash와 연결한다.
4. `python -m tools.scie_results_ui.prepare_holdout --verify --receipt <path>`가 실패하면 실행 금지. 이 CLI는 검증만 하며 평가 worker를 시작하지 않는다.
5. 동결 receipt를 소비하는 전용 실행 harness와 데이터 주입/채점 계약 통합 검증 후 새 run에서 8방법·fault·recovery를 실행한다. 기존 개발 runner의 18문항 이름만 바꿔 실행하면 안 된다.
6. 평가 후 변경은 새로운 개발 실험으로 분류하며 노출된 홀드아웃을 재사용해 독립 성능으로 주장하지 않는다.

## 독립성 제한

원천 FC/CSV와 일반 오류 유형은 개발셋과 공유한다. 독립성이란 현재 모델 평가·튜닝에 쓰지 않도록 예약한 질의/객체/조건 단위이며 새로운 원천·완전한 도메인 독립·인간 블라인드 설계를 뜻하지 않는다. 과거 전체 질의 corpus에 대한 중복 감사는 미완료다. 작성 에이전트는 내용을 보았으므로 후속 개발자/튜닝 프롬프트에 질의·GOLD를 전달하지 말고 UI에는 수량·상태만 표시한다. 같은 원천 Feature의 정의와 속성 문항은 상관성이 있어 독립 표본으로 단순 합산하지 않는다.
