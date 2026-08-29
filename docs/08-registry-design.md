# 08. 레지스트리 설계 (Registry Design)

## 1. 개요
분산된 멀티 에이전트 환경에서 각 컴포넌트의 메타데이터, 버전, 가용성을 중앙에서 관리하기 위해 4가지 핵심 Registry를 설계합니다.

## 2. Agent Registry
Agent의 식별 정보, 지원하는 분석 기능(Capability), 상태를 관리합니다.
- **주요 필드**: `agent_id`, `agent_name`, `version`, `description`, `endpoint_url`, `supported_intents`, `health_status`, `cost_weight`
- **활용**: Orchestrator가 작업 계획을 세울 때 가용한 Agent를 탐색하는 데 사용.

## 3. Tool Registry
Agent가 호출할 수 있는 함수, DB 프로시저, 서드파티 API 등을 관리합니다.
- **주요 필드**: `tool_name`, `tool_version`, `capability`, `input_schema`, `output_schema`, `timeout`, `security_scope`, `owner`
- **활용**: LLM이 Tool을 선택할 때 시스템 프롬프트(Context)로 주입하기 위한 Tool Description을 제공.

## 4. Model Registry
LLM, 임베딩, 비전 검출, 시계열 예측 등 각종 AI/ML 모델을 관리합니다.
- **주요 필드**: `model_id`, `model_name`, `model_version`, `task_type`, `framework` (PyTorch, vLLM, ONNX), `endpoint`, `security_level`, `evaluation_metrics`
- **활용**: Model Router가 작업 유형 및 보안 등급에 맞춰 프롬프트를 전송할 모델 엔드포인트를 선택. 외부 API(OpenAI, Claude) 및 내부 구축 모델(Local LLM) 통합 관리.

## 5. Dataset Registry (Data Catalog)
사용 가능한 해양 공간/시계열/속성 데이터셋의 메타데이터를 관리합니다.
- **주요 필드**: `dataset_id`, `logical_name`, `physical_location` (S3/DB Path), `crs`, `spatial_extent` (BBOX), `temporal_extent`, `update_cycle`, `security_level`, `license`, `dataset_version`, `quality_level`
- **활용**: Data Discovery Agent가 질의와 관련된 데이터를 찾을 때 사용하며, Orchestrator는 이 정보를 기반으로 데이터 접근 권한을 확인.

## 6. DB 스키마 개요
Registry는 관계형 DB(PostgreSQL)에 구현하며, 스키마(Schema) 구조가 동적으로 변할 수 있는 `input_schema`, `output_schema` 등은 `JSONB` 컬럼을 사용하여 유연하게 관리합니다.
