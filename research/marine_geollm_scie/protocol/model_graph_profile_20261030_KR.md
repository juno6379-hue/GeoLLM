# 모델 활성화 연구 graph 프로파일

기존 P_current_production_no_llm을 보존하며 새 방법명은 P_current_production_model_enabled_restricted다. 실제 운영 orchestrator_graph를 읽기전용 코드에서 호출한다. 운영 API나 운영 DB를 실행 대상으로 사용하지 않는다.

- 전체 원문18문항을 K1로 실행한다. baseline planning18/90행과 입력 예산·prompt가 같다고 주장하지 않는다.
- Qwen2.5:1.5b와 bge-m3:latest의 full digest를 model_profile.json으로 고정한다. embedding_ready=true와 embedding_model_digest 일치 및 LOADED_VERIFIED scie_model_v3 manifest가 필요하다.
- 모델 요청은 전용 proxy를 거친다. graph는 internal network 하나, proxy만 bridge+internal의 두 network를 가진다. proxy는 host Ollama만 사용하고 API endpoint/model 역할을 allowlist한다. 모델 pull/create/delete나 외부 임의 URL을 허용하지 않는다. 호스트 port를 publish하지 않는다.
- 원본 production prompt, temperature, num_ctx/max_tokens/timeout을 유지하고 proxy에서 실제 요청·prompt SHA256·응답·latency·digest를 기록한다. thinking/reasoning_content는 저장하지 않는다. 임베딩 응답은 벡터 자체 대신 count/dimension/hash를 저장한다.
- semantic answer cache는 매문항 비우고 checkpoint thread UUID를 새로 만든다. 다른 production 읽기캐시는 process warm 상태를 재사용한다. 초기화 모델호출은 IMPORT_WARMUP으로 분리한다.
- 문항deadline600초, launcher 전체13000초. 실패/미실행/부분완료를 원시상태대로 남긴다. model 호출이 없는 deterministic path도 구분한다.
- `model_calls.jsonl`은 실제 호출 관측, `production_rows.jsonl`은 최종 full state/QEC/evidence/receipt/tool trace, manifest는 source/model/image/benchmark/snapshot 조건이다. 실행승인은 성공률이나 의미정답이 아니다.
- source .env를 빈 파일로 가리고 dotenv를 비활성화한다. source mount는 RO, feedback/logs는 연구용tmpfs, 결과만 새 run 폴더에 쓴다. DB는 scie_model_v3로 고정하고 transaction read-only를 적용한다.

실행 명령: `python -m research.marine_geollm_scie.runners.launch_model_graph --output <새절대경로> --snapshot <새snapshot_manifest.json> --profile <model_profile.json>`.

필수 model_profile 예: model_digests에 qwen2.5:1.5b와 bge-m3:latest의 64자리 digest, embedding_ready=true, embedding_model_digest에 후자의 동일digest. 실제 모델과 embedding 준비는 부모 담당자가 검증하며 준비 전에는 실행하지 않는다.

구현 단위검사8 passed. 현재 이 문서 작성 시점에는 실제 모델 graph 실행을 시작하지 않았으며 결과는 별도 run 관측 후 추가한다.


추가 실행 gate: profile.snapshot_manifest_sha256이 실제 snapshot manifest 해시와 일치해야 한다. proxy readiness와 모델digest 확인이 실패하거나 worker exit가0이 아니면 stage 실패다. 원문18개의 중복/누락이나 불명 관측 상태도 실패다. 모든18행이 관측됐다는 상태는 EXECUTION_OBSERVED이며 모든 질의 성공을 뜻하지 않는다. proxy는 클라이언트 timeout/연결종료를 감지하면 Ollama upstream socket을 닫아 기존 caller의 취소조건을 보존한다. 비정상/timeout 로그를 유지하고 전체 timeout시 연구 worker와 proxy를 정리한다.


## 기능 범위 제한

중단 직전 준비 코드에서는 GEOLLM_CAPABILITY_PGVECTOR=true로 변경했다. 운영 원천의 knowledge.capability_embeddings 21행/21벡터를 읽기 전용으로 확인했고, 새 scie_model_v3 snapshot 생성 시 여섯 번째 관계로 복사하도록 준비했다. loader/launcher는 전체행·1024차원 검증을 요구한다. 새 snapshot 생성과 실제 capability 검색은 아직 실행하지 않았으므로 완료로 간주하지 않는다. 문서 검색·Qwen 호출 및 capability 후보검색의 실제 실행 검증은 재개 후 수행한다. 전체18문항과 실제 graph entry를 실행한다는 의미와 모든 production 의존성을 갖췄다는 의미를 구분한다. 방법명은 P_current_production_model_enabled_restricted로 고정하고 ablation/full P 완성 또는 baseline과 동일계산량을 주장하지 않는다.
