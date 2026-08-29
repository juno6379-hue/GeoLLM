# 14. 보안 아키텍처 (Security Architecture)

## 1. 개요
해양 공간 데이터는 기관의 핵심 자산이며, 국가 안보 및 군사적 민감성을 띨 수 있습니다. 따라서 인증, 권한, LLM 특화 보안 등 다계층의 강력한 보안 통제가 필수적입니다.

## 2. 인증 및 인가 (Authentication & Authorization)
- **OAuth2 / OIDC 기반 인증**: Keycloak이나 기존 기관의 IdP(Identity Provider)를 통한 싱글 사인온(SSO).
- **JWT 토큰**: API Gateway에서 토큰 무결성을 검증하고 사용자 정보(기관, 직급, 클리어런스 레벨)를 추출하여 Orchestrator의 `Security Context`로 주입.
- **RBAC (Role-Based) & ABAC (Attribute-Based)**: 
  - 역할 기반: 일반 사용자, 분석가, 관리자, 전문가(검토자).
  - 속성 기반: 소속 기관(예: 해경, 해수부, 해양조사원)과 데이터 등급(기밀, 대외비, 공개) 간 매칭.

## 3. 데이터 보안 (Data Security)
- **레이어별 접근 권한**: Dataset Registry에 정의된 `security_level`을 기반으로, 사용자의 클리어런스 레벨이 낮으면 Data Discovery Agent 단계에서 해당 데이터 조회를 차단(BLOCKED).
- **Row-Level Security (RLS)**: PostGIS에 저장된 군사 구역 등 특정 Feature는 DB 레벨의 RLS 정책을 적용하여, Tool 쿼리 실행 시 사용자 토큰의 Session 변수를 기준으로 자동 필터링됨.
- **개인정보/민감정보 마스킹**: AIS 선박 정보(MMSI, 선박명 등)나 보고서 내용 중 민감한 부분은 Report Agent에서 마스킹 처리하여 외부 반출 차단.

## 4. LLM 및 AI 특화 보안 (LLM Security)
- **임의 코드 실행 차단**: LLM은 Python REPL, 쉘 커맨드, Raw SQL을 절대로 직접 실행할 수 없습니다. 사전 정의된 Tool Registry의 Template만 매개변수를 바인딩하여 실행합니다. (SQL Injection 방어)
- **Prompt Injection 방어**: 
  - 시스템 프롬프트를 엄격히 고정.
  - 사용자의 입력 질의는 안전한 길이로 제한하며, 악의적 지시문(예: "Ignore previous instructions")을 탐지하는 가벼운 필터링 층(LLM 래퍼 또는 룰 베이스) 배치.
- **Tool Injection 방어**: LLM이 Tool 호출 파라미터를 조작하여 권한 밖의 작업을 지시하지 못하도록, Tool 실행 전 Orchestrator(또는 Tool Executor)에서 `execution_context.allowed_tool_scopes`와 대조하는 검증 로직 추가.

## 5. 인프라 및 운영 보안
- **Secret 관리**: API 키, DB 비밀번호, LLM API 키는 HashiCorp Vault 또는 클라우드 Secret Manager에 보관. 코드나 설정 파일에 하드코딩 금지.
- **감사 로그 (Audit Logging)**: 누가, 언제, 어떤 데이터와 툴을 사용하여 어떤 결과를 도출했는지(provenance) 모든 내역을 위변조 불가능한 스토리지에 보관.
- **Rate Limiting**: 특정 사용자의 무분별한 API 호출로 인한 자원 고갈 및 과금 폭탄 방지. API Gateway 레벨 적용.
