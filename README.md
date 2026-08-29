# Marine Geospatial Intelligence Platform (An_GeoLLM)

해양공간 지능분석 플랫폼은 사용자의 자연어 질의를 분석하여 **해양 공간 분석**, **데이터 카탈로그 탐색**, **표준/법령 RAG 질의**를 수행하는 Multi-Agent 기반 지능형 백엔드 시스템입니다.

## 🌐 Platform Scope & Boundaries

본 플랫폼(An_GeoLLM)의 핵심 철학은 **"지능형 오케스트레이션과 분석 에이전트에 집중하고, 데이터 서빙 및 단순 시각화는 기존/외부 전문 시스템에 위임한다"** 입니다. 이에 따라 플랫폼 내부 개발 범위와 외부 연동 범위를 명확히 분리합니다.

### 🏢 플랫폼 내부 범위 (Internal Scope)
플랫폼 내재화 및 신규 개발이 진행되는 마이크로서비스 및 에이전트 목록입니다.
- **Core 인프라**: API Gateway, 인증 및 권한(Auth), Task Service, Orchestrator
- **Registry & Ops**: Agent Registry, Tool Registry, Model Registry, Dataset Registry, Layer Registry, MLOps, LLMOps, Observability
- **전문 분석 Agents**: Data Discovery Agent, Standard·RAG Agent, Spatial Analysis Agent, AIS Analysis Agent, Vision·EO Agent, Time-Series Agent, Time-Series Forecast Agent, Situation Interpretation Agent, Validation Agent
- **연계 및 후처리**: Map Agent Adapter, Review Service, Report Service, Notification Service, Audit Service

### 🔗 외부/기존 시스템 연동 범위 (External Integration Scope)
플랫폼 내부에서 데이터를 직접 구축하지 않고, 외부 연동(Multi-DB 커넥션 또는 API)을 통해 참조하는 기존 시스템들입니다.
- **S-100/S-101 전자해도 (ENC) 시스템**: `gbenc` 데이터베이스 (전자해도 메타데이터, Feature 공간 객체, Portrayal Rule 조회용)
- **해양관측 시스템**: MDC DB (`ocean_web` Oracle DB, 조위관측소 및 해양관측부이 실시간 데이터 조회용)
- **Map Agent Web Viewer**: S-100 렌더링에 특화된 기존 프론트엔드 웹 뷰어 (플랫폼은 Adapter를 통해 GeoJSON 및 레이어 제어 메시지만 전달)

---

## 🏗️ System Architecture
graph TD
    Client[Client / Frontend] -->|POST /api/v1/query| API[FastAPI Orchestrator Router]
    API --> Intent[LangGraph: Intent Parser]
    
    Intent -->|SPATIAL_SEARCH| SpatialAgent[Spatial Analysis Agent]
    Intent -->|DATA_DISCOVERY| DiscoveryAgent[Data Discovery Agent]
    Intent -->|SEARCH| RAGAgent[Standard RAG Agent]
    
    SpatialAgent -->|Execute Tool| DB_Spatial[(PostGIS Database)]
    DiscoveryAgent -->|Extract Schema| Catalog[(Mock Registry / External APIs)]
    RAGAgent -->|Cosine Similarity| DB_Vector[(pgvector Database)]
    
    DB_Spatial -->|Filter by Clearance| SpatialAgent
    DB_Vector -->|Filter by Clearance| RAGAgent
    
    SpatialAgent --> Validator[LangGraph: Validator & Formatter]
    DiscoveryAgent --> Validator
    RAGAgent --> Validator
    
    Validator --> API
    API -->|GeoJSON / Evidence| Client
```

## 🔒 Security Principles (보안 및 거버넌스)

- **LLM 환각 차단**: LLM은 직접 SQL이나 Python 코드를 생성하여 실행하지 못합니다. Pydantic으로 정의된 엄격한 스키마(Tool Parameter)만 추출하며, 실제 데이터베이스 조회는 사전에 정의된 `SQLAlchemy text()` 템플릿만이 수행합니다.
- **Row-level Access Control (행 수준 접근 통제)**: `PUBLIC`, `RESTRICTED`, `SECRET` 계층에 따라 DB 응답 최하단에서 데이터가 필터링됩니다. 권한 밖의 접근 시도는 `shared/observability/audit_logger.py`에 의해 추적됩니다.
- **이중 Fallback 안전망**: OpenAI API Key 누락이나 데이터베이스(PostgreSQL) 연결 실패 시에도 시스템이 크래시되지 않도록, Rule-based 파서와 내장 Mock 데이터로 Graceful Degradation 되도록 설계되었습니다.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 15+ (with `PostGIS` and `pgvector` extensions)
- Poetry 또는 pip (의존성 관리)

### 2. Environment Variables
프로젝트 루트 경로에 `.env` 파일을 생성하고 아래 값들을 채워넣습니다. (`.env.example` 참조)

```env
# LLM Configuration
OPENAI_API_KEY="sk-..."

# Database Configuration (Optional: 미입력 시 내부 Mock 데이터로 동작)
POSTGRES_URL="postgresql+psycopg2://user:password@localhost:5432/marine_db"

# Observability (OpenTelemetry)
OTEL_SERVICE_NAME="marine-geollm"
```

### 3. Installation & Run
```bash
# 의존성 설치
poetry install

# FastAPI 서버 실행 (uvicorn)
poetry run uvicorn main:app --reload --port 8000
```

### 4. API Endpoints
- **Swagger UI**: `http://localhost:8000/docs`
- **Health Check**: `GET http://localhost:8000/health`
- **지능형 질의 (Main Endpoint)**: `POST http://localhost:8000/api/v1/query`

## 🗂️ Project Structure

- `main.py`: FastAPI 엔트리포인트 및 OpenTelemetry 초기화
- `services/orchestrator/`: LangGraph 기반 워크플로우 제어, LLM 라우팅, 프론트엔드 포맷 어댑터(GeoJSON)
- `services/spatial_analysis_agent/`: 해양 공간 연산(ST_DWithin, ST_Intersects) 담당
- `services/standard_rag_agent/`: pgvector 코사인 유사도 기반 문서 검색 담당
- `services/data_discovery_agent/`: 데이터 카탈로그 매칭 및 외부 API 파라미터 파싱 담당
- `shared/`: 공통 스키마(Pydantic), 보안/권한 컨텍스트 제어, Audit/Logger 유틸리티
- `data/`: SQLAlchemy Connection Pool 및 세션 관리
