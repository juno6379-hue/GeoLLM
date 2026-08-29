# 00. 현재 시스템 분석 (Current System Analysis)

## 1. 개요
본 문서는 해양공간 지능분석 플랫폼 구축을 위한 Phase 0 단계로, 현재 작업 환경 및 기존 시스템 상태를 분석한 결과를 담고 있습니다.

## 2. 작업 공간(Repository) 상태
- **경로**: `d:/An_GeoLLM`
- **상태**: 현재 저장소는 빈 디렉토리로 확인됨. 코드가 초기화되지 않은 상태이므로 스크래치(Scratch)부터 플랫폼 아키텍처 및 기본 구조를 설계해야 함.

## 3. 기존 Map Agent 및 해양공간정보 표출 기능 분석
사용자의 요구사항에 따르면, **"현재 전자해도 및 해양공간정보를 표출하는 Map Agent 또는 지도 가시화 기능은 일부 구현되어 있다"**고 명시되어 있습니다.
저장소에 코드가 없으므로, 기존 Map Agent는 별도의 저장소나 서비스 형태로 존재한다고 가정합니다.
- **예상 구조**: MapLibre GL JS 또는 OpenLayers 기반 프론트엔드와, WMS/WFS/Vector Tile 등을 제공하는 GeoServer(또는 OGC API) 백엔드로 구성되었을 확률이 높음.
- **연계 방안**: 기존 Map Agent를 직접 수정하는 대신, `Map Agent Adapter`를 신규 개발하여 Orchestrator 및 전문 Agent의 분석 결과를 기존 Map Agent가 이해할 수 있는 표준 규격(`MapLayerSpecification`)으로 변환 후 전달.

## 4. 기존 전자해도 및 S-100/S-101 기능
- S-57 및 S-101 데이터는 ISO 8211 인코딩, GML, GeoJSON 등 다양한 형태로 존재 가능.
- 기존 시스템에서 이를 어떻게 파싱하고 렌더링하는지에 대한 세부 코드는 없으나, 플랫폼에서는 S-100 제품 사양(표준)에 대한 RAG 검색과 전자해도 데이터를 분석용 Vector(PostGIS)로 변환/로딩하는 파이프라인을 구축(또는 기존 파이프라인 연계)하여 분석에 활용.

## 5. 데이터베이스와 데이터 소스
- **RDBMS / GIS**: PostgreSQL + PostGIS (v3 이상) + pgvector (LLM 임베딩용).
- **시계열/위성**: Object Storage(S3 호환, MinIO)에 Xarray/NetCDF/Zarr 또는 STAC 형태로 저장.
- **기존 데이터 접근**: 직접 DB를 조회하거나, 기존에 구축된 OpenAPI를 통해 데이터를 수집하여 처리 계층(Data Processing Layer)을 통해 표준화 및 인덱싱.

## 6. 재사용 가능한 코드와 신규 개발 범위
- **재사용 범위**: 
  - 기존 지도 렌더링 UI (Map Agent)
  - 기존 전자해도 데이터 서빙 인프라 (WMS/WFS)
- **신규 개발 범위**:
  - Orchestrator, LLM 엔진 및 라우터 (LangGraph/Temporal 기반)
  - 10여 종의 전문 Agent(Data, RAG, Spatial, AIS, Vision, TS, Forecast, Interpretation, Validation)
  - 공통 Registry(Agent, Tool, Model, Dataset)
  - Map Agent Adapter 및 Report Agent
  - Human-in-the-Loop 및 MLOps/LLMOps 인프라

## 7. 시스템 경계 (System Boundaries)
- **플랫폼 (신규)**: 사용자 질의 해석, 분석 계획 수립, Agent 실행, 데이터 융합, 결과 검증 및 요약, Adapter를 통한 결과 변환.
- **외부 연계 (기존/외부)**: 기존 Map Agent UI, 해양 공공데이터 API, 외부 위성 영상 제공처, 기존 인증 체계(IdP).

## 8. 결론
본 프로젝트는 빈 저장소에서 MSA/모듈형 기반으로 플랫폼을 처음부터 적절히 구조화(Scaffolding)하는 것으로 시작합니다. 모든 신규 컴포넌트는 기존 시스템과의 낮은 결합도(Loose Coupling)를 위해 잘 정의된 공통 계약(Contract)을 통해 상호 작용하도록 설계합니다.
