# 23. RAG Embedding Dataset Review

## 기준 경로

검토 기준:

```text
G:\내 드라이브\An_GeoLLM\Dataset
```

현재 파일 구성:

```text
.zip  | 70 files
.pdf  | 11 files
.csv  | 11 files
.docx | 4 files
.xls  | 1 file
```

Embedding 실행 전에는 `DATASET_ROOT`를 위 경로로 지정한다.

```powershell
$env:DATASET_ROOT = "G:\내 드라이브\An_GeoLLM\Dataset"
```

## 우선순위 1: S-101 2.0 필수 embedding

GeoLLM의 주 기준은 S-101 2.0이므로 아래 자료는 반드시 embedding 대상이다.

| Source | 역할 | 처리 방식 |
|---|---|---|
| `S-101_ENC_Product_Specification_Ed_2.0.0.pdf` | S-101 제품 사양 근거 | PDF body chunk |
| `S-101_Annex_A_DCEG_Ed_2.0.0.pdf` | feature/attribute 사용 지침 | PDF body chunk |
| `101_Feature_Catalogue_2.0.0.xml.signature.zip` | S-101 2.0 Feature Catalogue 원천 | XML 추출 후 structured chunk |
| `101_Portrayal_Catalogue_2.0.0.zip.signature.zip` | S-101 2.0 portrayal rule 근거 | Lua/XML/rule 파일 추출 후 rule chunk |
| `S-158-101_Validation_Checks_Ed_1.1.0.zip` | S-101 검증 rule | PDF/XLSX validation chunk |
| `gbhd_s101.projection.s101_feature_current` | 실제 S-101 2.0 DB profile | DB summary chunk |
| `gbhd_s101.projection.s101_feature_valid` | valid geometry serving profile | DB summary chunk |
| `gbhd_s101.serving.accident_s101_relation_current` | 사고-S101 관계 근거 | DB summary chunk |

주의: S-101 개별 geometry row 전체를 embedding하지 않는다. geometry는 PostGIS에서 검색하고, RAG에는 feature type, attribute profile, validation rule, relation summary만 넣는다.

## 우선순위 2: S-100 공통 기반

S-101 해석에는 S-100 공통 개념이 필요하다.

| Source | 역할 | 처리 방식 |
|---|---|---|
| `S-100_5.2.0_Final_Clean.pdf` | S-100 기반 표준 | PDF body chunk |
| `S-158-100_Validation_Checks_Ed_1.0.0.zip` | S-100 공통 검증 | PDF/XLSX validation chunk |
| `S100BPC (Lua_XSLT).zip` | 기본 portrayal 처리 참고 | Lua/XSLT 파일명 및 rule 요약 chunk |

중복 파일은 제외한다.

- `S-100_5.2.0_Final_Clean (1).pdf`
- `S-100_5.2.0_Final_Clean (2).pdf`
- `S-158-100_Validation_Checks_Ed_1.0.0 (1).zip`
- `S100BPC (Lua_XSLT) (1).zip`

## 우선순위 3: 관련 S-100 제품군

S-101 단독 답변 이후 수위, 조류, 항행경보 연계를 위해 유지한다.

| Product | Source | 처리 방식 |
|---|---|---|
| S-104 | `S-104_Water_Level_Information_For_Surface_Navigation_Ed_2.0.0.pdf` | PDF body chunk |
| S-104 | `S-158-104_Validation_Checks_Ed_1.0.0.zip` | validation chunk |
| S-111 | `S-111_Surface_Currents_Ed_2.0.0.pdf` | PDF body chunk |
| S-111 | `S-111_Surface_Currents_Ed_2.0.0_Clean.docx` | DOCX body chunk |
| S-111 | `111_Feature_Catalogue_2.0.0.xml.signature.zip` | XML catalogue chunk |
| S-111 | `111_Portrayal_Catalogue_2.0.0.zip.signature.zip` | portrayal catalogue summary chunk |
| S-111 | `S-158-111_Validation_Checks_Ed_1.0.0.zip` | validation chunk |
| S-124 | `S-124_Navigational_Warnings_Product_Specification_Ed_2.0.0.pdf` | PDF body chunk |
| S-124 | `S-124_Annex_A_DCEG_Ed_2.0.0.pdf` | PDF body chunk |
| S-124 | `124_FC_2.0.0.xml.signature.zip` | XML catalogue chunk |
| S-124 | `124_PC_2.0.0.zip.signature.zip` | portrayal catalogue summary chunk |

중복 S-124 자료는 제외한다.

- `S-124_Navigational_Warnings_Product_Specification_Ed_2.0.0 (1).pdf`
- `S-124_Navigational_Warnings_Product_Specification_Ed_2.0.0_Redline (1).docx`
- `S-124_Navigational_Warnings_Product_Specification_Ed_2.0.0_Redline (2).docx`
- `124_FC_2.0.0.xml.signature (1).zip`
- `124_PC_2.0.0.zip.signature (1).zip`

## 우선순위 4: 법령, 사고, 용어

질의 답변의 설명 근거로 embedding한다.

| Source | 역할 | 처리 방식 |
|---|---|---|
| `한국해양교통안전공단_선박법령정보현황_20250925.csv` | 선박 법령 근거 | CSV row/semantic chunk |
| `해양수산부_행정규칙_20240909.csv` | 행정규칙 근거 | CSV row/semantic chunk |
| `해양수산부_항만 관련 법령_20210913.csv` | 항만 법령 근거 | CSV row/semantic chunk |
| `SOLAS.pdf` | 국제 안전협약 근거 | PDF body chunk |
| `용어사전.xls` | 한국어 해양 용어 보강 | XLS row chunk |
| `해양경찰청_해상조난사고 상세데이터 현황_20251231 (1).csv` | 사고 이벤트 설명/통계 | row summary chunk + PostGIS |
| `해양경찰청_해상조난사고  유형별 사고 척수_20251231.csv` | 사고 유형 통계 | CSV summary chunk |
| `해양경찰청_해상조난사고 해역별 사고 척수_20251231.csv` | 사고 해역 통계 | CSV summary chunk |
| `행정안전부_사고발생 현황_20231231.csv` | 일반 사고 비교 지표 | 선택 chunk |
| `해양수산부_해양안전종합정보시스템_사고정보(중앙해양안전심판원)_20230630.csv` | 사고 보조 근거 | 선택 chunk |

## PostGIS 적재 대상

아래 자료는 geometry/시계열/대용량 grid가 중심이므로 embedding 주 대상이 아니다. PostGIS, raster/grid store, 또는 별도 serving table에 적재하고 RAG에는 schema, layer 설명, 필드 사전, 요약 통계만 넣는다.

| 분류 | 자료 |
|---|---|
| 항로/교통 | `AIS항로분석.zip`, `AIS주요통항로분석.zip`, `V-PASS항로분석.zip`, `V-PASS주요통항로분석.zip`, `일반항로.zip`, `통항분리경계선.zip` |
| 위험/제한 구역 | `속도제한구역.zip`, `정박금지(투묘금지).zip`, `진입제한.zip`, `주의경계해역.zip`, `낚시제한구역.zip`, `낚시금지구역.zip`, `보호수역.zip` |
| 항만/정박/시설 | `정박지(면).zip`, `정박지(점).zip`, `소형선항만 안내정보.zip`, `선박안전교통관제구역.zip`, `대형계선부표(점).zip`, `항로표지정보 CSV` |
| 해저/장애물 | `간출암,암암,세암(점).zip`, `어초.zip`, `준설지역.zip`, `갯골(상세).zip`, `와류.zip` |
| 수위/조류/예측 | `수치조류도_국내연안2025.zip`, `조석예보.zip`, `예측조위.zip`, `바다갈라짐예측정보_*.ZIP` |
| 사고 공간 레이어 | `선박사고(해양안전심판원).zip`, `선박사고(해양경찰서)_20250813.zip`, `인명사고(25년).zip` |
| 행정/지명 | `도서지명.zip`, `해양수산부_공동활용체계_해양지명_20221231.csv`, `해양경찰서관할구역.zip`, `직선영해기선.zip` |

## 현재 스크립트와 차이

`scripts/build_document_rag_chunks.py`는 이제 `DATASET_ROOT` 환경변수를 지원한다. 그러나 현재 처리 범위는 PDF, DOCX, S-158 ZIP, 법령 CSV 중심이다.

보완 필요:

1. `101_Feature_Catalogue_2.0.0.xml.signature.zip`에서 XML을 직접 추출해 S-101 catalogue chunk 생성
2. `101_Portrayal_Catalogue_2.0.0.zip.signature.zip`에서 portrayal rule 요약 chunk 생성
3. `용어사전.xls` row chunk 지원
4. 사고 유형/해역 통계 CSV chunk 지원
5. 공간 ZIP의 `.qmd`, `.xlsx`, `.shp.xml`, DBF field schema를 layer metadata chunk로 생성
6. 중복 파일 제외 정책을 manifest에 기록

## 권장 embedding 실행 단위

1. `s101_core`
   - S-101 Product Specification
   - S-101 DCEG
   - S-101 Feature Catalogue XML
   - S-101 Portrayal Catalogue
   - S-158-101 validation checks
   - `gbhd_s101` DB profile
2. `s100_foundation`
   - S-100 5.2.0
   - S-158-100
   - S100BPC
3. `safety_context`
   - 사고 상세/통계
   - 법령/SOLAS
   - 용어사전
4. `external_layer_metadata`
   - 공간 ZIP 원본의 layer schema/metadata만

이 순서로 적재하면 S-101 2.0 질의가 가장 먼저 완성되고, 이후 사고/법령/외부공간 레이어를 단계적으로 붙일 수 있다.
