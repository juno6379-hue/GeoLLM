# GOLD v2 8방법 v4 실행 조건

운영 `eb8856a`, 연구 `5accd72` 이후 새 전체 비교다. 기존 v3 결과와 immutable GOLD v2는 변경하지 않는다. v4의 관측 완료 여부는 실제 status.json과 완료 gate를 따른다.

- run: `runs/20261101_gold_v2_eight_k1_v4`
- snapshot: `outputs/scie_gold_v2_eight_snapshot_20261101_v4`
- 계약: `eight_execution_contract_v4.json`, `structured_review_v2.json`, `baselines/tool_contract.py`
- Qwen2.5:1.5b/bge-m3 기존 digest, 768출력토큰·180초·seed42 등 이전 조건 유지. 별도 Qwen7B 개발 후보를 이 비교에 혼합하지 않는다.
- B3 생성에서 도구 인자 type/enum을 강제하고 예시 설명문 복사를 줄인다. 같은 최초 계획을 B3/B4/P0/H에 제공하고 B4/H는 동일 검토를 공유한다. P0 누락값 자동추론·계획 교정 금지.
- 검토 initial_checks는 모델이 작성한 판단이다. fail과 invalid=false의 자기모순은 계약 실패/미측정으로 보존하고 프로그램이 검출 성공으로 바꾸지 않는다. 공통 ESR v3 정의와 동일5공간case 분모는 유지한다.
- 운영은 요청 revision 전달과 shadow 표시 점수 계약을 보완했다. shadow 선택은 실행 권한이 아니다. 양자화 점수는 확률·보정된 정확도가 아니다.

개발 한계: 1.5b 검토4건은 형식 통과지만 오류3건 모두 정상으로 판단했다. typed B3 개발2건도 의미 오류를 남겼다. 따라서 이 변경을 의미 정확도 개선으로 미리 선언하지 않는다. 실제 비어 있지 않은3feature 엔진 통제는 모델 생성 성공이 아니다. v3 실패를 보고 개선했으므로 같은 benchmark는 개발 비교이며 독립 holdout 주장을 하지 않는다. 인간 GOLD와 반복 변동성은 미완료다.

8방법144관측+별도fault27을 실패 포함해 수집하고 최종 `report_with_faults/comparison_KR.md`를 검증한다. 실행 중 frozen source/모델/예산/입력/GOLD 변경·추가 모델/운영API 호출 금지. 소스 변경이 필요하면 원본을 보존하고 새 전체 run을 사용한다.
