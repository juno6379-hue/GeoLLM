# 해양 근거 연결·정규화 보강·Qwen 혼합 비교 후속

2026-09-26. 이번 작업은 다운로드한 원문을 추적 가능한 근거로 만들고 기존 의미 연결과 평가기에 연결했다. 해양수산부 자료 전체의 ontology 자동 생성이나 human gold 승인이 완료된 것은 아니다.

## 실제 구현

- `index_maritime_references.py`: 다운로드 manifest hash를 확인한 MOF 원문 12개, 기존 S-101 FC 2.0.0 및 DCEG 2.0.0을 총 **6,090개** 단위로 색인했다. PDF는 실제 파일 페이지 번호(1부터), HML/HWPX는 원문 문단 순번, FC는 Feature/속성 코드를 locator로 사용한다. 문단 순번을 법령 조항 번호로 표시하지 않는다.
- 각 단위에 원천 hash, 텍스트 hash, locator, 판, 출처 검수 상태를 보존한다. FC는 XML의 productId와 versionNumber가 S-101/2.0.0인지 확인한다. 서명 검증 완료를 주장하지 않는다. DCEG 원문 hash와 추출 결과는 별도 snapshot에 기록한다.
- PDF 추출 과정에서 fontTools 미설치에 따른 경고 340개 단위를 발견했다. 평가용 경로 `outputs/reference-tools/fonttools-4.60.1`에 해당 버전을 설치한 뒤 재추출해 경고를 해소했다. 서비스 전역 패키지를 변경하지 않았다. 최종 pypdf 6.19.0 / fonttools 4.60.1을 index manifest에 기록했다. 남은 빈 텍스트 22개·제어문자 4개와 판 승인 보류 50쪽은 gold로 자동 승인하지 않는다.
- `reference_evaluation.py`: index 파일 hash, unit identity, 원천·판·locator·텍스트 hash·인용문 일치, 검수자와 claim/applicability 필드를 검사한다. 승인 보류 자료, 추출 결함, 검증되지 않은 현행법 적용을 거부한다. CLI gold 평가는 `--reference-index`를 필수로 요구한다. 검수자 ID 문자열만으로 실제 검수자 신원·의미적 타당성을 입증할 수는 없다.
- 모델 출력 없는 100개 개발 검수 양식에 근거 후보·원문 표현·개념 ID·기존 KG seed·registry hash를 연결했다. 18개에 근거 후보가 있다. 나머지를 틀린 질문으로 판정하지 않는다. 위치·실시간 자료·시스템 진단에는 별도 DB/실행 근거가 필요하다. 후보와 승인된 `reference_bindings`는 별도 필드다.

## query 정규화와 온톨로지의 현재 범위

기존 Kiwi·원문 span·수량 정규화·부정 조건·KG 타입 계약은 유지한다. `marine_lexicon.py`에서 기존 해양 사전과 S-101 사전을 함께 읽도록 하여, 사전에는 있지만 의미 연결에서 빠졌던 **정박지 → AnchorageArea**를 수정했다. 다중 후보는 임의로 하나를 선택하지 않으며 FC에 없는 코드와 NEEDS_REVIEW 항목을 신규 바인딩에 사용하지 않는다. 원문 query를 덮어쓰지 않는다.

실제 API에서 `정박지는 S-101에서 어떤 Feature야?`는 원문 span `[0,3]`, `AnchorageArea`, 기존 KG seed `feature:anchoragearea_anchoragearea` 및 타입 검증 관계를 반환했다. 참조 양식에서는 FC의 AnchorageArea 코드와 DCEG PDF 413쪽을 연결한다. Obstruction은 DCEG 304쪽, Wreck은 299쪽이 우선 후보로 검색됐다. 이는 PDF 파일 기준 쪽수이며 내용 전체가 gold 승인됐다는 의미는 아니다.

해양수산부 전문용어 홍보물에서 잠제→수중 방파제, 물양장→소형선 부두, 예선→끌배, 선유장→소형선 정박장 **4개 검수 후보**를 만들었다. `build_mof_normalization_review.py`가 원문 페이지의 두 표현·인접 구간과 hash를 확인한다. 관계는 `recommended_korean_label`이며 `owl:sameAs`, S-101 Feature 매핑 또는 실행 의도로 승격하지 않았다. 공식 순화어를 곧바로 모든 문맥의 동의어로 치환하면 중의성·범위 차이를 잃을 수 있기 때문이다.

새 문서에서 상하위·관련 관계를 자동 승인해 운영 KG에 적재하는 기능은 미완료다. 현재는 기존 ontology 연결 보강과 출처가 붙은 후보 구축 단계다.

## Qwen 포함 비교

기존 Qwen2.5 1.5B / Qwen3.5 4B의 같은 10문항 원시 응답을 새 평가기로 재집계했다. 신규 모델 호출은 하지 않았다. 동일 snapshot뿐 아니라 문항 ID·query·input hash·prompt·추론 설정이 같아야 paired 비교를 허용한다.

| 항목 | Qwen2.5 1.5B | Qwen3.5 4B |
|---|---:|---:|
| 구조·원문·슬롯 계약 통과 | 2/10 | 3/10 |
| 유효 Qwen 순위와 규칙 1위 불일치 | 0/2 | 1/3 |
| 기존 실행의 지연 p50 | 29.855초 | 95.835초 |
| 의미 accuracy/F1 | 미측정 | 미측정 |

규칙, Qwen, 50:50 혼합, 기존 75:25 혼합, registry/context 혼합을 분리했다. 기존 키 `calibrated_mix`는 호환성을 위해 남지만 보고서에 **UNFITTED_TEMPERATURE_1_FIXED_WEIGHTS_NOT_VALIDATED**를 명시한다. 현재 가중치는 학습·검증된 calibration이 아니다. 실패를 규칙 성공으로 몰래 대체하지 않으며 전체 10문항 분모를 유지한다.

4B의 79번은 PLACE_LOOKUP에서 DATASET_PROVENANCE로 1위가 바뀌었다. 추가 질문 gate까지 적용한 혼합은 이 사례를 실행 추천으로 승인하지 않는다. 이 변화만으로 실제 pgvector 진단이 완결되거나 정확도가 개선됐다고 판단하지 않는다. 의도 순위만 혼합했으므로 mixed 슬롯·작업 계획 점수는 null이다. 운영은 계속 `used_for_execution=false`, QLoRA DEFER다.

## 검증·재현·남은 작업

관련 단위 최초 실행은 Kiwi 비활성 환경 변수 때문에 1개 실패/57개 통과였다. 실제 Kiwi 활성 테스트를 별도로 재실행해 1개 통과했다. 최종 근거·혼합·사전 테스트는 제외 조건 회귀를 포함해 22개 통과했다. 앞선 실행과 중복되므로 통과 수를 합산하지 않는다.

backend 재시작 직후 readiness 전에 시작한 API 검사 v1은 0/8이었다. 준비 완료 뒤 v2는 8/8, 정박지 사례와 readiness 대기를 추가한 **v3는 9/9** 통과했다. 실패 원본도 보존한다. 실제 침선 반경 검색과 부정/위치/기간 조건을 포함하며 전체 서비스 의미 정확도가 아니다.

원본·산출물 경로:

- `outputs/maritime-reference-index/v3/{manifest.json,units.jsonl}`
- `outputs/maritime-reference-index/mof-normalization-review-v1.jsonl`
- `outputs/korean-intent-shadow/development-reference-review-v5.jsonl`
- `outputs/korean-intent-shadow/paired-reference-contract-v4.json`
- `outputs/korean-intent-shadow/live-reference-contracts-v{1,2,3}.jsonl`

색인 재현 시 Python module path에 `/app`과 평가용 fonttools 경로를 넣고 `scripts/index_maritime_references.py --archive <로컬 원문 폴더> --review configs/evaluation/maritime_reference_acquisition_review.json --fc <FC XML> --dceg <DCEG PDF> --output <새 폴더>`를 실행한다. 입력 원문은 MOF 수집 manifest와 로컬 S-101 파일을 유지한다. 검수 양식은 `export_korean_review_pack.py --reference-index <units.jsonl>`로 생성한다.

법령센터의 2019-76 본문 경로(`https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000179241`)에서 해당 고시·시행일을 확인했지만, 전체 최신 개정 이력과 첨부 최종본 대조는 완료하지 못했다. 지침 PDF의 `2019-xx` 보류를 해제하지 않았다. 다음은 현행 통합법령·판 불일치 확인, 용어/관계 검수 확대, 승인된 정규화의 운영 반영, 독립 gold, 원문 선택 방식 Qwen adapter·지연 보강이다. portrayal 실제 산출물과 복합/부정 조건 실행 P0도 남아 있다.
