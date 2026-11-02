# Source/Data 안정화 1단계 — 실제 검증과 잔여 작업

사용자 지정 [9단계 순서](development_k1_nine_stage_20261102.md)의 첫 단계다. 운영 데이터 작업이며 새 논문 비교나 홀드아웃 평가가 아니다.

## 완료한 연결

- FC 수정302건의 원본 XML 필드·임베딩 artifact·source validation 및 현재 DB 전후604행 hash를 재검증했다. 실제 stored23,523/active23,215이며 전체 본문의 새로운 재수출 검증을 뜻하지 않는다.
- baseline+FC delta receipt의6개 hash를 확인하고 `data/source_verification/20261102_v3_fc`로 게시했다. 기존v1/v2를 보존했다. 포인터 SHA는 `0407bbfb721b595027e6b350db57763c08c1853cac3cc69a378d6490555dc75a`다.
- 서버 내부에서 현재 FC302건의 derived field 검증 표시 및 XLSX MISMATCH99건 제외를 확인했다. 의미·좌표 권위는false다.
- 실제 HTTP `/api/v1/dataset-evidence` lexical 조회: categoryOfAnchorage 문서5건/FC derived label·새manifestSHA 일치, 없는문서0건, 둘 다HTTP200. 새 모델 호출·DB 변경 없음. 산출물 `outputs/stage1_parent_20261102_v2/publication_verification.json`.
- 최초 동일FC 요청은60초관측timeout. 서버로그상69.389초후HTTP200이었고 최초본문은수신하지못했다. v1 원본을보존하고120초관측한도로v2를별도실행했다. 서버timeout/모델조건변경이나지연해결로해석하지않는다. 자원경합가능성은있지만단계별원인은미확정이다.

## 임베딩은 아직 적용 완료가 아니다

`outputs/stage1_source_audit_20261102_v1/audit.json` 재검증 시 PDF1,432/2,215 checkpoint가 입력·계획·고정모델·1024차원·유한벡터 검사를 통과했다. 잔여783/invalid0, 최종embedded파일은미생성이다. 이는확인시점수치이며워커가계속진행한다. 앞선1,324개관측과합산하지않는다.

당시 모델tags 재조회는15초timeout으로 현재digest확인은null이다. 앞선별도조회성공을현재확인으로대신하지않았다. 완료후worker의사후모델검사와원문/벡터전체검증이필요하다. PDF409개는수치·읽기순서대조보류이며2,215개재임베딩집합밖이다.

## XLSX 오류99개 수정 후보

`scripts/verify_xlsx_source_revision.py`로5개workbook의비어있지않은셀16,477개를302개새본문후보에빠짐·중복없이연결했다. 셀주소/타입/style/수식/cached값/hidden/merged정보와ZIP·member·elementhash를보존한다.

- 기존99개본문·source·chunk ID를원본snapshot/receipt와대조했다.
- 같은document_id를공유하는정상PDF등61청크는별도ID/hash보존목록이다. document_id전체를치환하면안된다.
- workbook별many-to-many lineage이며기존one-to-one적용기와호환되지않는다. `SOURCE_CANDIDATES_ONLY`, `apply_ready=false`다.
- 실제개발중범위검사/비워크시트관계오인/동일ZIP복사본신규ID충돌을발견·수정했다. v1–v3산출물보존후v4를생성했다. 과거runner코드자체는동결하지않았다는제한을기록했다.
- 최종후보 `C:/Users/최준오/.codex/geollm-audit/20261102/xlsx_revision_v4/candidates.json`, SHA `a3b2332e2312c6b8b3640fe3d4bf61467c8adc4323bd901eaca2ae17e5feeb3f`. 독립원본대조는같은폴더 `independent_baseline_verification.json`.
- 수식재계산/Excel날짜표시/단위의미를추정하지않았다. 새임베딩·DB적용·receipt완료가아니다.

## 다음 실행

DOCX 추가 감사(`outputs/stage1_docx_audit_20261102_v2`)는 baseline 대상79개 중 원문 유일 span30개를 재확인하고49개를 미검증으로 남겼다. 현재 게시본과 대조하면30개 모두 이미 확인된 청크이므로 **신규 확인은0개**다. 원본/snapshot 사후 hash, receipt의 chunk/source/content 일치, 문단·표 XPath를 검사했다. 남은49개는 원본 hash 오류가 아니라 `NO_LITERAL_NORMALIZED_SPAN`이며 주로 S-111 문서다. 유사 의미를 근거로 완료 처리하지 않았다.

1. PDFworker완료검증→최종artifact/hash·원문·모델·벡터검토→archive/CAS전후행검증→PDF delta receipt→실제본문조회.
2. XLSX live full row/vector export와명시99개대상·61개보존조건을갖춘many-to-many적용기검증→고정모델임베딩→CAS/archive→receipt·검색검증. 기존 `scripts/xlsx_source_text.py`의비워크시트관계검사도별도보완필요.
3. DOCX locator 대조와PDF409/legacy DB152등미검증원천을완료·보류·격리로정확히구분. 파생근거나문자열일치를현실좌표·의미정확성으로승격하지않음.
4. 정상coverage/연구snapshot권위연결이후RQ계측단계진행. 1단계미완료상태에서새DevelopmentK1을시작하지않음.

통합 대시보드의부산항입구질의오류는사용자추가지시에따라별도운영에이전트가수정·검증하며데이터워커와연구원본을분리한다.
