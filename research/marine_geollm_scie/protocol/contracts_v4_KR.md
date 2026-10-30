# 필수 작업 중심 평가계약 초안 v4

18개 승인 참조의 원문과 현재 capability registry 정의만 사용하여 [작업 계약](../benchmark/contracts_v4/task_contracts_DRAFT.jsonl)과 [18개 현황표](../benchmark/contracts_v4/현황_KR.md)를 작성했다. 기존 v3 사용자 승인과 GOLD는 그대로이며, 이 문서의 새 작업 분해·capability 조합·근거 검사 기준은 **DRAFT**다. 모델 실행 결과를 열거나 이에 맞춰 정답을 수정하지 않았다. 기존 파일럿에 노출된 사례이므로 미노출 holdout으로 사용할 수 없다.

## 승인된 값과 새 해석

- `transcribed_approved_values`: v3의 QEC 부분 필드, 공간 oracle, 기대 행동 및 원문 서술을 그대로 복사한다. QEC가 비어 있는 사례의 조건부 텍스트를 자동 실행 슬롯으로 바꾸지 않는다.
- `task_obligations`: 작업 단위의 새로운 구조화 제안이다. `PROPOSED_INTERPRETATION`, 자동 판정식 null로 유지하며 기존 승인과 구분한다. 단일 intent 일치를 정답으로 요구하지 않는다.
- `acceptable_capability_combinations`: 실제 registry ID와 정의를 연결한 조합 후보다. 모든 조합을 열거한 것은 아니며 호출 순서까지 정답으로 고정하지 않는다. 다른 구현도 동일 작업·입출력·근거를 충족하는지 검토할 수 있다. registry 후보 존재는 런타임 지원·데이터 coverage·실행 권한 증거가 아니다.
- `evidence_contract`: 승인된 근거 서술을 보존하되 파일·판·locator·주장 지지 여부 검사는 새 제안으로 분리한다. 기존 null인 필수 인용집합을 임의로 완성하지 않는다.
- `execution_guards`: 원문 조건부 행동을 보존한다. AOI·기본 geometry·반경을 새로 만들지 않는다. 실행 허용은 운영 ExecutionValidator의 별도 역할이다.

`source_provenance`는 원본 파일 SHA256, 사례 ID, JSON pointer, 정확한 문자열, 그 문자열의 SHA256 및 Unicode 문자 오프셋 `[0, len)`을 보존한다. dict/null은 `json_sorted_keys` 직렬화임을 표시하여 원시 파일 바이트 span과 혼동하지 않는다. registry 조합의 각 정의에도 같은 방식의 출처가 있다. 원본 XLSX까지의 경로·해시는 승인 v3 원문에서 추적한다.

## 남은 핵심 결정

| 대상 | 확정해야 할 내용 | 임의 결정하지 않은 부분 |
|---|---|---|
| Q1·Q2 등대 | 구조물과 등화의 조건부 답변·확인 요청을 어느 범위에서 허용할지 | Landmark/Building/Light 후보를 모두 필수 객체로 만들지 않음 |
| Q2 속성 | 필수/선택 속성, 다중도, Feature별 허용값까지 채점할지 | 일반 코드목록을 모든 Feature 허용값으로 간주하지 않음 |
| Q3_01 | nearest의 전국 coverage·시설 중복·동률 정책 | 독도 Q4 anchor 승인을 등대 데이터 완성으로 확대하지 않음 |
| Q3_02 | 부산항 권위 polygon 및 경계 포함 규칙 | 임의 buffer로 항만 영역 대체하지 않음 |
| Q3_03 | 실제 선택 AOI를 제공하는 추가 조건 | 현재 입력에서는 AOI 요구; 임의 영역 생성 없음 |
| Q4 | 공간 결과 외 응답 완결성·근거 표시 기준 | v3 동도 기준점·2022CSV·5000m·11 IDs는 이미 승인됨 |
| Q5 | 두 대상 coverage·부분응답·비교·속성 설명의 충족 기준 | 문서 설명을 공간 실행 성공으로 취급하지 않음 |
| Q6 | 최소 인용집합·edition·locator·주장별 지지의 판정 기준 | 출처명 존재만으로 근거 적합성 정답 처리하지 않음 |

Q4의 원래 검수 메모 중 기준점 미확정 문구는 역사적 원문으로 보존한다. `already_resolved_by_v3`와 현황표에서 이후 사용자 승인으로 해소된 항목을 구분했다. 전체 18건 사용자 승인이 새 v4 의미 판정식을 자동 승인하는 것은 아니다.

## 재현과 검증

생성기: `python -m research.marine_geollm_scie.runners.build_contracts_v4 --output <새 디렉터리>`.
기존 출력 디렉터리는 덮어쓰지 않는다. [JSON Schema](../benchmark/contracts_v4/schema.json) 및 `tests/test_contracts_v4.py`로 18건 고유성, v3 exact 전사, 새 해석의 DRAFT 유지, 근거 span/hash, Q4 외 공간 ID 미생성, registry 후보의 비실행 권한을 검사한다. 생성 manifest에는 v3/registry/생성기/결과 해시를 남긴다. 운영 코드·기존 결과·GOLD에는 쓰지 않는다.

preflight는 계약·데이터 준비상태만 확인할 수 있다. 새 작업 충족 정확도나 전체 의미 정확도를 계산하려면 이 초안의 필수 작업·허용 대안·완결성 기준을 먼저 확정해야 한다.

## FC 원문 기반 답안·근거 구체화

[9개 Q1/Q2/Q6 답안 후보 표](../benchmark/contracts_v4/근거답안후보_KR.md)와 [근거 객체 JSONL](../benchmark/contracts_v4/evidence_reference_candidates.jsonl)을 추가했다. `extract_fc_reference_candidates.py`는 FC XML SHA256와 metadata의 판·일자·제품명을 확인한 뒤 definition, 직접 attribute/feature/information binding, 다중도, binding 허용값과 전역 code label을 분리하여 추출한다. 복합 attribute 참조는 재귀적으로 포함한다. 이 객체들은 원문 검증 완료이며, 특정 질의에 이 원문을 선택하는 해석과 최소 정답집합의 완결성은 별도 AI 초안이다. DCEG 본문은 이 XML 추출로 검증했다고 주장하지 않는다.

확인된 예로 Landmark/Building colour binding은 13개지만 LightAllAround는 8개이며, LightSectored는 sectorCharacteristics → lightSector의 colour binding을 따라간다. Wreck의 정의·기하·직접 속성 binding은 기존 parsed FC와 재검산했다. 검증 테스트 4개 통과. 초기 geometry 추출에서 반복 `permittedPrimitives` 요소를 자식목록으로 읽는 오류를 테스트가 검출했고 수정했다. 실패 산출물은 `outputs/scie_fc_candidate_initial_failed_validation_20261030/`에 보존했으며 현재 후보 파일은 수정 후 재생성본이다.

재현: `python -m research.marine_geollm_scie.runners.extract_fc_reference_candidates --output <새 디렉터리>`. 기존 candidate JSONL을 덮어쓰지 않는다. 이 추출은 실제 객체 인스턴스, 공간 정답, 문서 밖 사실 또는 GOLD 승인을 생성하지 않는다.
