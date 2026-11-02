# 운영 미검증 원문 위치·파생 설명 후속 감사

2026-11-02. 논문 및 홀드아웃을 열람·수정하거나 모델 비교를 실행하지 않았다. 이 문서는 원문 위치·생성 설명 담당 에이전트의 결과이며, 부모의 최종 운영 적용·API 검증과 구분한다.

## 최종 분류

미검증 3,819 중 PDF 표현 차이 2,654를 제외한 **1,165청크**를 검사했다.

| 판정 | 수 | 의미 |
|---|---:|---|
| VERIFIED_TEXT | 112 | 원문 해시와 유일한 본문 구간 일치. 문자 중간 절단 여부는 별도 기록 |
| VERIFIED_DERIVED_FIELDS | 450 | 원문·등록부·현재 운영 DB 필드를 기반으로 생성 설명 재현. 원문 전체·법률 현행성·좌표 현실 정확도와 다름 |
| INCOMPLETE_DERIVED_FIELDS | 401 | FC 302 + XLSX 저장 XML 추출 99. 현재 설명의 제한·재추출 필요 |
| UNVERIFIED | 202 | DOCX 제어문자 49 + 현재 원천 없는 legacy DB 152 + 원문 요약 미일치 1 |

최종 결과는 `C:/Users/최준오/.codex/geollm-audit/20261102/locator/v5/results.jsonl`이다. SHA256: `f755e91425a097cce55974a2fd1d2140b2fd21647e7ca96f90ca9f25b898db04`. `v2`~`v4`와 최초 실패 관측은 보존했다. 부모의 최종 독립 검수 결과가 해당 분류의 운영 승격 여부를 결정한다.

## 원문 연결과 발견한 결함

- FC 468 중 166은 생성 필드가 일치했다. 302는 정의의 앞부분이 모두 일치하지만 attribute 112의 열거값 code가 생략되고 feature 190의 binding이 `not parsed from XML`로 남았다. 원본 XML 직접 필드 6,773개와 고유 code 노드·element hash로 확인했다. 거짓 정의라고 단정하지 않고 **불완전한 파생 설명**으로 분리한다.
- 기존 XLSX 추출기 세 곳은 `sharedStrings` 인덱스·수식·날짜 serial을 XML node text 그대로 이어 붙였다. 처음 본문 일치로 분류한 5개와 추가 복구한 94개, 총 99개를 본문 검증 승격에서 제외했다. `xlsx_source_text.py`로 shared string을 실제 문자열에 연결하고 cell 주소·타입·style, 수식·cached value·merge 범위를 명시한다. Excel 수식을 계산하지 않고 날짜 표시 형식을 추정하지 않는다.
- DOCX 79 중 독립 검사에서 49는 `tab`, `br`, `cr`, nonbreaking hyphen을 보존한 원문과 맞지 않았다. `docx_source_text.py`와 생성기/감사 어댑터에서 제어문자를 보존하도록 수정했다. 기존 청크·벡터를 이 코드 수정만으로 검증 완료 처리하지 않는다.
- `gbhd_s101` 현재 DB를 REPEATABLE READ/READ ONLY로 재집계했다. 기존 파생 설명 137개 본문과 집계 source hash 모두 일치했고 feature/geometry/value count 차이는 0이었다. 기존 `S100_dev` 설명 152개는 현재 연결 서버에 해당 DB가 없어 재확인할 수 없다. 연구 DB로 대체하지 않았다.
- CSV·archive 소개와 사고 집계, 법적 등록부 설명은 원문 literal과 구분했다. 사고 요약의 공간화 개수는 기존 DMS 숫자 존재 기준 생성 규칙 재현이며, 해당 사고의 현실 좌표 검증을 의미하지 않는다. 법적 등록부 11개 일치는 공식 법령 원문/최신판 검증을 의미하지 않는다.

## 재색인 준비

FC 새 후보 302개는 모든 XML code/ref를 포함하도록 작성했다. 기존 생성기의 40 binding/80 listed value 제한을 후보에 적용하지 않았다. 새 ID는 content/source/locator에 결합하며 기존 source ID·제목·문서유형·조회 메타데이터를 유지한다. 최대 본문은 3,597자다.

- 후보: `C:/Users/최준오/.codex/geollm-audit/20261102/locator/fc_revision_candidates_v3.json`
- SHA256: `722a52450a15486ba72f504617fd33a1a7707f5da324bf9662839c7e7e90cf49`
- 직접 XML 모든 필드 재검산: 302/302. 실제 기존 벡터의 전체 행 export는 부모의 별도 실행이 필요하다.
- 생성기: `scripts/package_fc_field_revisions.py`
- 단계별 실행기: `scripts/repair_source_document_revisions.py`

실행기는 원본 full row/vector 보존→원문 재검산→고정 bge-m3/1,024차원/truncate=false 새 임베딩→검토된 artifact SHA→운영 DB CAS/transaction/archive→롤백을 분리한다. 실제 DB 연결은 기존 `gbhd_s101` 필수 guard를 사용한다. apply 직전 원본 파일 full SHA도 다시 확인한다. 개별 임베딩 checkpoint는 준비계획·본문·모델 hash가 모두 맞아야 재사용한다. 동일 출력의 중복 worker는 lock으로 거부하며 강제 종료 잔여 lock을 자동 탈취하지 않는다.

이 에이전트는 모델 호출·DB apply·rollback을 실행하지 않았다. 부모가 실제 수행한 단계는 최종 보고서를 따른다.

## 검증과 실패 보존

- 자체 관련 테스트 **17 passed**: 숫자 결합 방지, 유일 원문 구간, XLSX shared string/수식/스타일/merge, DOCX 제어문자, 계획·모델·입력 변조 차단, 원본 열 보존, checkpoint 재개, 실패 lock 해제, PDF 실제 span·숫자 변경 차단.
- 별도 에이전트가 XLSX/DOCX 추출 결함을 발견해 승격을 철회했다. worker에서 PDF 숫자 helper의 잘못된 import 및 apply 이전 원본 SHA 재검사 누락도 교차검토 후 수정했다.
- 최초 D 드라이브 공간 부족으로 FC 183개 adapter error와 DB export 저장 실패가 발생했다. 원본 실패 파일을 보존하고 C 드라이브의 새 버전으로 재실행했다. 저장 실패를 원천 데이터 오류로 합산하지 않았다.
- 추출기 보완으로 기존 임베딩 내용이 자동 수정되지는 않는다. DOCX/XLSX는 원문 재추출·새 벡터·원본 보존 교체를 별도로 수행해야 한다. 모든 semantic/coordinate authority는 false로 유지했다.
