# PDF 미검증 청크 후속 검증 — 2026-11-02

운영 snapshot의 미검증 PDF 2,654청크(공백 차이 2,644, 기호 차이 9, 대체문자 차이 1)를 전수 재대조했다. 논문·홀드아웃을 열람하거나 모델 호출·DB 변경을 하지 않았다.

## 결과와 보완 범위

- 별도 PyMuPDF 1.26.7 엔진으로 지정 페이지를 다시 추출하고, 숫자 lexeme와 모든 문자·단어 경계가 일치하는 유일 구간을 찾았다. **30청크**를 확인했으며 본문 변경이 없어 이 30개는 새 임베딩이 필요하지 않다. 현재 감사 포인터 반영은 부모 통합 단계다.
- 나머지를 포함한 전체 2,654개에 대해 pypdf 6.18.0 원문 페이지와 원 추출기 `parts(size=1100/2200, char_offset)`를 재현했다. 저장 본문과 같은 결과는 0개다. 공백이 달라진 원문 구간 2,632개를 찾았고 22개는 기호·대체문자·다중 구간 등의 추가 검토 대상으로 남았다.
- **387개는 숫자 lexeme 배열이 달라 자동 교체 대상에서 제외**했다. 숫자 사이 공백을 지워 서로 다른 값을 합치는 일을 허용하지 않는다.
- 기존 확인 30개를 제외한 **2,215개의 숫자 보존·원문 substring 재추출본**을 새 ID와 이전 ID/본문 해시를 포함한 적용 준비 패키지로 만들었다. `requires_new_embedding=true`, 실제 DB CAS 및 원본 전체 행·벡터 보존 조건이 있으며 **아직 임베딩·DB 적용은 0개**다.
- 따라서 현재 이 작업만으로 원문 확인된 것은 30개이고, 2,624개를 검증 완료로 승격하지 않는다. 2,215개 준비본 적용 후에도 409개는 추가 검토가 필요하다.

## 원인 조사와 한계

원문 파일 해시는 동일하다. 저장 본문과 현재 추출 본문 사이에서 기관명과 전화번호 사이, 단어 사이에 공백이 삽입되는 현상을 실제 재현했다. 표본 `0010702b82ddd97171e75499006d0a7f46b9ce5d81c135482feb4084947113fe`의 pypdf 6.16.2·6.18.0·6.19.0 재현은 모두 불일치했다. 과거 추출 환경의 버전 기록이 없어 특정 버전 하나를 확정 원인으로 주장하지 않는다. 단순 공백 제거 일치는 후보 구간을 찾는 데만 사용했고, 기존 본문 검증 통과 근거로 사용하지 않았다.

PDF skill에 따라 Poppler 150dpi로 실제 원문 3페이지를 렌더링하여 확인했다.

| 자료·물리 페이지 | 제목과 좌표의 원문 연결 | 확인 경계 |
|---|---|---|
| NORTH KOREA_KOR.pdf 39쪽(인쇄31쪽) | 신포항 — 40°02.0′N, 128°12.0′E | 제목 바로 아래 좌표 표기 일치 |
| NORTH KOREA_ENG.pdf 18쪽(인쇄98쪽) | SEOSURA HANG — 42°16.3′N, 130°36.0′E | 제목 바로 아래 좌표 표기 일치 |
| 한국연안항로지 국문 동해안남부 12쪽(인쇄46쪽) | 주문진항 — 37°53.5′N, 128°49.8′E | 제목 바로 아래 좌표 표기 일치 |

이는 AI 시각검토 3표본이며 전수 시각검수나 현실 객체 ID·CRS·현행성 확인이 아니다. 원문 제목과 좌표의 연결은 별도 공간 연결 담당에게 전달했다.

## 재현·보존

- `scripts.verify_dataset_pdf_followup` — 독립 엔진·exact token span 대조.
- `scripts.prepare_dataset_pdf_reextraction` — 원 추출 재현과 raw span/숫자 차이 분리.
- `scripts.package_dataset_pdf_revisions` — 숫자 보존 신규 revision 준비; DB 쓰기 없음.
- `tests/unit/test_verify_dataset_pdf_followup.py` — 9 passed. 숫자 합침·단어 합침·기호 치환·중복 구간·대체문자 및 신규 ID/본문 보존을 검사했다.
- 첫 D: 출력은 2,359개 checkpoint 뒤 디스크 부족(OSError28)으로 실패했다. 부분 결과를 완료로 쓰지 않고 원본 보존 후 C: 새 경로에서 전체 재실행했다. `first_attempt_failure.json`에 기록했다.
- PyMuPDF는 host venv에만 설치했다. pypdf 대조 버전은 C:의 별도 deps 폴더에 설치했으며 운영 컨테이너·lock은 변경하지 않았다.

산출물 루트: `C:/Users/최준오/.codex/geollm-audit/20261102/pdf/`

- `mupdf_complete/receipts.jsonl`: SHA256 `88e517d95bf59eaa897bf355ec07ac33013918c279ae14af16e250573452f4b0`.
- `reextraction618/candidates.jsonl`: SHA256 `659c4bb12aab934ec6a6badace8b5ba975e131b8622a50ef44662c381d8cca9a`.
- `numeric_preserving_revision_plan.json`: 2,215개, SHA256 `3479046d06e13e0e2c46eeb662a0d57e4bfb027b5d8753faf33b49ab113abb60`.
- `visual_verification.json`, `visual/coordinate_0.png`~`coordinate_2.png`, `extractor_diagnostic.json`, `mupdf_complete/span_readback_verification.json`.
- UI용 현재 상태: `outputs/dataset_unverified_followup_20261102/pdf/status.json`.

독립 엔진의 저장 page text를 다시 읽어 30개 모두 joined text hash, 실제 span offset, substring hash 및 숫자 lexeme가 일치함을 검증했다. 페이지 파일의 Windows 줄바꿈은 `read_text()`로 복구한 문자열을 기준으로 span/hash를 검사한다. receipt 파일 자체의 해시는 실제 바이트 기준이다.
