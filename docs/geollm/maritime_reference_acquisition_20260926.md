# 해양수산부 정답 근거 자료 로컬 확보

2026-09-26. 사용자가 GitHub push와 로컬에 없는 해양수산부 관련 근거 자료 다운로드를 요청했다. 기존 커밋 7개를 `origin/main`에 push했고 원격 HEAD `453b58a75123ef50ef272d46f074eb0f11812901`을 확인했다. 아래 자료 수집 코드·메타데이터·문서는 후속 커밋으로 기록한다.

## 실제 저장 결과

저장 위치: `Dataset/authoritative_references/mof/20260926-v1/`.
공식 첨부 원문 **12개**(PDF 4, HML 5, HWPX 3), 출처 HTML snapshot **7개**, 실패 **0개**다. 원문과 HTML은 분리해 집계한다. 각 파일의 URL·응답 형식·다운로드 시각·크기·SHA-256·판 검수 상태를 `manifest.json`에 기록했다. 다운로드 날짜를 문서 발행일로 사용하지 않는다.

| 자료 | 보관 원문 | 출처 및 적용 범위 |
|---|---|---|
| 해양수산 용어사전 | PDF 359쪽 | [공식 용어사전](https://www.mof.go.kr/dictionary/selectDictionaryList.do?menuSeq=928), 발행 판은 추가 확인 필요 |
| 해양수산 전문용어 표준화 홍보물 | PDF 2쪽 | 같은 공식 용어사전 페이지, 별칭·순화어 근거 후보 |
| 해양공간특성평가 지침 제정 | HML·PDF 50쪽 | [2019-76 제정 게시물](https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=35&docSeq=26403&menuSeq=885), PDF 판 불일치 검수 필요 |
| 해양공간적합성협의 업무처리규정 일부개정 | HML·HWPX | [2022-160 개정 게시물](https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=35&docSeq=47512&menuSeq=885), 현행 통합본과 구분 |
| 항로표지 장비·용품 기능 및 규격 기준 | HML·HWPX 2개 | [2025-23 개정 게시물](https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=35&docSeq=60520&menuSeq=886), 개정문·본문·별표를 보관 |
| 제주 신도리 해양보호구역 지정 | HML | [2025-57 지정 게시물](https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=9&docSeq=61209&menuSeq=375), 경계·제외구역·적용 조건 포함 |
| 부산 및 인근 EEZ 해양공간관리계획 | HML·PDF 220쪽 | [2020-11 고시 게시물](https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=35&docSeq=30244&menuSeq=886), 2020 판으로 고정 |

기존 S-101 제품사양·DCEG, FC/PC 서명 ZIP 및 FC XML, 해양사고 통계·사례집 등 **12개**는 다시 받지 않고 기존 파일 경로와 hash를 목록화했다. 기존 파일의 최초 다운로드 출처·기관 서명 검증을 이번에 완료한 것은 아니다. 목록의 `PREEXISTING_ORIGIN_NOT_REVERIFIED`가 이를 구분한다.

## 검증 및 발견 사항

19개 다운로드 파일의 SHA-256을 재검증했다. PDF는 pypdf로 페이지 트리와 첫 3쪽 텍스트를 읽었고, HML/HWPX는 XML 본문을 파싱했다. 전체 PDF 시각 검수나 모든 조항의 법적 유효성 검증은 하지 않았다. 재실행에서는 기존 snapshot의 hash를 확인하고 원문 재다운로드 없이 12/7/12, 실패 0을 유지했다.

다운로드 오류 HTML 거부, 잘린 PDF 거부, HWPX 패키지 식별, 기존 원문 덮어쓰기 방지 회귀 테스트 **4 passed**. 운영 코드 변경이 없어 기존 100개 API 평가는 반복하지 않았다.

- 중요한 예외: 공식 지침 제정 게시물의 PDF 표지에 `제2019-xx호`, `2019.4`가 남아 있다. 동반 HML에는 2019-76과 2019-06-12가 표시된다. 원본은 그대로 보존하고 **GOLD_APPROVAL_BLOCKED**로 별도 검수 목록에 기록했다. 공식 호스트에서 받았다는 이유만으로 최종 고시 내용이라고 승인하지 않는다.
- 전문용어 홍보물은 2017-01-18 시행 고시를 언급한다. 홍보물과 실제 고시 원문을 구분하며 최신 법적 기준으로 승격하지 않는다.
- 제주 신도리 고시에는 외곽 좌표 외에도 제외 사업구역·지적경계 우선 조건·토지 제외가 있다. 외곽 좌표만 PostGIS에 넣으면 적용 공간이 잘못될 수 있으므로 geometry 자동 적재는 하지 않았다.
- 부산 계획은 2020 판이다. 일부 표지 숫자는 텍스트 추출 시 제어문자로 나타나므로 그 값을 날짜·수치 정답으로 사용하지 않는다.

세부 검수 상태는 `configs/evaluation/maritime_reference_acquisition_review.json`, 실제 파일 목록과 hash는 `configs/evaluation/mof_reference_inventory_20260926.json`을 따른다. `UNREVIEWED`는 다운로드 실패가 아니라 gold 미승인 상태다.

## 재현과 다음 작업

```powershell
python scripts/archive_maritime_references.py --snapshot 20260926-v1
```

설정은 `configs/evaluation/maritime_reference_downloads.json`이다. 동일 snapshot의 파일이 바뀌면 덮어쓰지 않고 실패하며, 원천 개정 수집 시 새 snapshot ID를 사용한다. HTML 오류 응답을 PDF/HML로 저장하지 않는다. 버전 통제를 위해 config가 변경되면 새 snapshot을 요구한다.

원본은 기존 `.gitignore`의 Dataset 정책에 따라 로컬 보관한다. GitHub에는 수집 스크립트·선정 목록·hash 메타데이터·검수 문서를 올린다. 사용자 요청은 로컬 보관이며 외부 문서 전체의 공개 재배포는 별도 수행하지 않았다. 사용자 피드백 JSONL은 이번 커밋에 포함하지 않는다.

다음은 현행 법령 통합본·후속 개정 대조, 판 불일치 해소, 조항/페이지/용어 locator 작성, 원문과 canonical ID 연결, 독립 human gold 승인이다. 원문 확보만으로 RAG/DB 적재 또는 평가셋 승인이 완료된 것은 아니다. 현재 운영 라우팅·DB를 변경하지 않았으며 QLoRA는 계속 DEFER다.
