# GOLD v2 8방법 v3 재실행 조건

기존 v2 관측144건과 통제 오류27건은 보존한다. GOLD v2 질문·답안계약은 변경하지 않는다. 운영 Validator와 연구 검토·평가 코드가 변경됐으므로 저장 답변 재채점으로 대체하지 않고 P1을 포함한 전체 실험을 새로 실행한다.

## 수정의 분리

- 운영: 명시된 원요청과 계획의 CRS·대상 Feature·대상 확장·반경을 대조한다. 새로운 추론이나 계획 자동교정은 하지 않는다. 영어 수심/높이 길이와 공간 반경을 구분하며, 차단 사유와 검증 receipt를 실제 API 응답에 보존한다. 별도 운영 문서와 API 원본을 확인한다.
- 연구: B3 계획을 먼저 동결하고 B4/H가 동일한 구조화 검토 결과를 공유한다. P0는 원래 질의·공간 문맥을 별도로 캡처하고 무손실 QEC 컴파일 후 운영 Validator를 호출한다. GOLD·문항 ID를 검증 입력으로 사용하지 않는다.
- LLM 검토: JSON schema를 생성 요청에 적용하고 종료 사유·구조를 엄격히 검사한다. 실패 응답을 임의 포장하거나 재시도하지 않는다. 개발 호출3건은 형식3/3 통과했지만 정상 사례 오차단과 누락 geometry 미검출이 있었다. 형식 개선을 의미 정확도 개선으로 주장하지 않는다.
- 평가: 모든 방법에 `spatial_execution_semantics_v3`를 적용한다. 완료된 관측에서 실제 SQL 미실행은 성공 false, 누락·모순 계측은 null이다. 실행 성공과 공간 정답을 분리하고 같은 GOLD 공간평가 대상 집합으로 분모를 고정한다. 조건부 성공률과 미측정도 별도로 보고한다.

## 신규 동결과 실행

- 실행 폴더: `runs/20261101_gold_v2_eight_k1_v3`
- snapshot: `outputs/scie_gold_v2_eight_snapshot_20261101_v3`
- immutable GOLD: `benchmark/gold_v2_immutable_20261101_v1`
- 연구DB 6개 관계를 실제 재추출하여 부모 snapshot과 hash 일치를 검사한다. 실행 소스와 검토 schema·평가 계약도 새로 동결한다.
- 8방법 각18건=144관측, 별도 동일 fault9건×3방법=27관측, K1이다. 768토큰·180초 검토 상한과 재시도0을 유지한다.
- 완료 gate는 관측 수 외에 8방법 실행 성공 의미 버전과 공간평가 case 집합·분모 일치도 검사한다. 미측정 결과를 제거하여 gate를 통과시키지 않는다.

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.supervise_eight --output research/marine_geollm_scie/runs/20261101_gold_v2_eight_k1_v3 --snapshot-output outputs/scie_gold_v2_eight_snapshot_20261101_v3 --include-faults
```

상태는 실제 `status.json`, 부모·자식 PID와 단계별 로그를 따른다. 실행 중 소스·모델·GOLD·예산 변경 및 추가 Ollama/운영 API 호출을 금지한다. 실패 원본을 보존하고 코드 변경이 필요하면 새 run으로 전체 재실행한다. 최종 보고서는 `report_with_faults/comparison_KR.md`다.

## 한계

명시된 단일 제약 검사이며 자연어 전체 의미 보존 검증이 아니다. 여러 거리의 하위 작업 대응과 복합 작업 전체 합집합 완결성은 미측정이다. 운영 경로의 원문 전용 fallback과 연구 경로의 원문·문맥 캡처를 구분한다. 승인 coverage·nearest·canonical polygon·복합 비교 전체 구현과 revision/shadow 문제는 별도 미완료다. 독립 인간 GOLD는 미수령이며 K1 결과로 반복 변동성이나 전체 시스템 완성을 주장하지 않는다.
