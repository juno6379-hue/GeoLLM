# 02. 해양공간 지능분석 플랫폼 아키텍처 (Platform Architecture)

## 1. 12계층 (Layers) 정의

본 플랫폼은 책임과 역할을 철저히 분리하기 위해 다음 12개의 계층(Layer)으로 구성됩니다.

1. **Data Source Layer**: 플랫폼에 데이터를 공급하는 원천 (Oracle MDC, PostGIS gbenc, 센서 등).
2. **Data Ingestion and Processing Layer**: 원천 데이터를 수집하고 공간정보(CRS) 및 메타데이터를 정제하는 파이프라인.
3. **Metadata and Knowledge Layer**: 정제된 데이터를 바탕으로 카탈로그, 벡터 임베딩(pgvector), 공간 지식 그래프를 구성하는 저장소.
4. **Marine GeoLLM Intelligence Layer**: 프롬프트 레지스트리와 도메인 튜닝된 LLM/VLM 모델이 질의를 분석하는 AI 코어.
5. **Orchestration Layer**: (LangGraph 기반) 사용자 질의의 의도를 파악하고, DAG를 생성하여 에이전트의 생명주기와 전이를 제어.
6. **Specialized Agent Layer**: 공간 분석, RAG, 비전, 시계열 등 특정 도메인 로직을 책임지는 자율 마이크로서비스 집합.
7. **Tool and Model Layer**: 에이전트가 호출하는 실제 실행 모듈 (PostGIS Query 템플릿 등 Registry 화 된 안전한 도구 모음).
8. **Validation and Human Review Layer**: 최종 결과를 배포하기 전, 시스템적 교차 검증 및 전문가(HITL)가 개입하여 승인하는 방어 계층.
9. **Map, Report and Application Layer**: 클라이언트(프론트엔드)가 시각화할 수 있도록 데이터를 `MapLayerSpecification` 등으로 규격화하는 계층.
10. **Security and Governance Layer**: OAuth2 인증, ABAC/RBAC 권한 제어, 데이터 접근 감사 로그 및 LLM 보안(프롬프트 인젝션 방어).
11. **Infrastructure and Data Platform Layer**: 런타임 컴퓨팅(Docker/K8s), 분산 스토리지, Message Broker 등 인프라 자원.
12. **Operations, MLOps and LLMOps Layer**: CI/CD 배포, OpenTelemetry 기반 옵저버빌리티, 토큰 모니터링 및 AI 모델 재학습 운영.

---

## 2. 논리 아키텍처 (Logical Architecture)

논리 아키텍처는 데이터와 제어의 흐름, 서비스 간의 계약(Contract)을 명세합니다.

### 2.1 논리적 데이터/제어 흐름도
```mermaid
flowchart TD
    subgraph 9_Map_Report_App_Layer[9. Map, Report & App Layer]
        UI[Web/GIS Client]
    end

    subgraph 10_Security_Layer[10. Security & Governance Layer]
        Auth[API Gateway / Auth]
    end

    subgraph 5_Orchestration_Layer[5. Orchestration Layer (LangGraph)]
        Orchestrator((Orchestrator))
    end

    subgraph 4_LLM_Intelligence_Layer[4. Marine GeoLLM Intelligence]
        Router[Model Router]
        Prompt[Prompt Registry]
    end

    subgraph 6_Specialized_Agent_Layer[6. Specialized Agent Layer]
        DataAgent[Data Discovery Agent]
        SpatialAgent[Spatial Analysis Agent]
        RAGAgent[Standard RAG Agent]
    end

    subgraph 7_Tool_Model_Layer[7. Tool and Model Layer]
        ToolReg[Tool Registry]
    end

    subgraph 8_Validation_Review_Layer[8. Validation & Review Layer]
        ValAgent[Validation Agent]
        HITL[Human-in-the-Loop]
    end

    subgraph 3_Metadata_Knowledge_Layer[3. Metadata & Knowledge Layer]
        VectorStore[(Vector Store)]
        Catalog[(Data Catalog)]
    end

    UI -->|Query| Auth
    Auth -->|AgentRequest| Orchestrator
    
    Orchestrator <--> Router
    Router <--> Prompt
    
    Orchestrator -->|Task| DataAgent
    Orchestrator -->|Task| SpatialAgent
    Orchestrator -->|Task| RAGAgent
    
    DataAgent --> Catalog
    SpatialAgent --> ToolReg
    RAGAgent --> VectorStore
    
    SpatialAgent --> ValAgent
    ValAgent --> HITL
    HITL -->|AgentResult / MapLayerSpec| Orchestrator
    Orchestrator -->|Response| UI
```

### 2.2 논리 관점 상세 명세
- **서비스 간 계약 (Contract)**: 모든 서비스(Orchestrator $\leftrightarrow$ Agent)는 `shared/schemas/agent.py`의 `AgentRequest`, `AgentResult` Pydantic 모델을 통해서만 비동기로 통신합니다.
- **실행 흐름 (Execution Flow)**: Orchestrator가 전체 19개 상태머신(State Machine)을 제어하며, 각 Agent는 Stateless하게 작업을 수행한 후 결과를 반환합니다.
- **권한 및 검증 흐름**: 
  - 권한 흐름: API Gateway에서 주입된 `SecurityContext`가 끝단 DB 쿼리(Tool)까지 전달되어 Row-level 데이터 접근을 필터링합니다.
  - 검증 흐름: Agent 결과는 항상 Validation Layer를 거치며, 기준치 미달 시 LangGraph 체크포인터를 통해 실행이 중단(Interrupt)되고 관리자 리뷰를 대기합니다.

---

## 3. 물리 아키텍처 (Physical Architecture)

물리 아키텍처는 컨테이너 배치, 네트워크 분리, 데이터베이스 구성을 명세합니다.

### 3.1 확정안 (현재 개발/검증 환경)
현재 소스코드 및 도커 환경에 기반하여 구현된 단일 서버 기준의 물리 아키텍처입니다.

```mermaid
flowchart LR
    Client[Web Browser / Leaflet UI] --> APIServer[FastAPI Server (Docker)]
    Client -.-> |WMS Tiles| S100WMS[S-101 WMS Server\nlocalhost:8657]
    
    subgraph Server [Single Node Server]
        APIServer
        LLM[OpenAI API / Local LLM]
        
        subgraph DB_Tier [Database Tier]
            LocalPG[(Local PostGIS)]
            Oracle[(Remote Oracle MDC\nconfigured by ORACLE_URL)]
            S100PG[(Remote gbenc PostGIS\nconfigured by GBENC_DB_* env)]
        end
    end
    
    APIServer -.-> LLM
    APIServer --> LocalPG
    APIServer --> Oracle
    APIServer --> S100PG
```

### 3.2 권고안 (프로덕션 운영 환경)
대용량 해양 공간 데이터 처리 및 고가용성(HA)을 보장하기 위해 Kubernetes 기반으로 스케일아웃(Scale-out)이 가능한 프로덕션 권고 아키텍처입니다.

```mermaid
flowchart TD
    Internet((Internet)) --> WAF[WAF / Load Balancer]
    
    subgraph DMZ [DMZ (External Network)]
        API_GW[API Gateway / Auth Server]
    end
    
    WAF --> API_GW
    
    subgraph Private_Network [Private Network (K8s Cluster)]
        API_GW --> Message_Broker{{Kafka / Redis MQ}}
        
        subgraph Compute_Nodes [Agent Compute Nodes]
            Orchestrator_Pod[Orchestrator Pods]
            Spatial_Pod[Spatial Agent Pods]
            RAG_Pod[RAG Agent Pods (GPU)]
        end
        
        Message_Broker <--> Orchestrator_Pod
        Message_Broker <--> Spatial_Pod
        Message_Broker <--> RAG_Pod
        
        subgraph Storage_Tier [Storage Tier]
            PG_Cluster[(PostGIS HA Cluster)]
            Vector_DB[(Vector DB)]
            MinIO[(S3 Object Storage)]
        end
        
        Spatial_Pod --> PG_Cluster
        RAG_Pod --> Vector_DB
        Spatial_Pod --> MinIO
    end
```

### 3.3 물리 인프라스트럭처 권고 사항
- **메시지 브로커 (Kafka/Redis)**: 공간 연산(Tool)은 수 분 이상 소요될 수 있으므로 HTTP 동기 통신 대신 MQ 기반의 비동기 워커 구조가 필수적입니다.
- **네트워크 분리 (DMZ vs Private)**: 보안을 위해 API Gateway(인증) 기능만 외부망(DMZ)에 노출하고, LLM과 통신하는 Agent Pod 및 DB 자원은 100% Private 망으로 격리해야 합니다.
- **오브젝트 스토리지 (S3/MinIO)**: 대규모 GeoJSON 산출물은 DB나 인메모리에 담지 않고 오브젝트 스토리지에 파일 형태로 적재 후 URI만 반환하는 구조를 유지해야 합니다.
