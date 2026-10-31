# 동일 데이터·새 실행 코드의 연구 snapshot 파생

K5 v1은 추론 초기화 전에 기존 snapshot의 `query_normalizer.py` 해시 불일치로 중단됐다. 원본 snapshot의 `files` 목록은 데이터·사전·KG 산출물뿐 아니라 실행 코드 두 파일도 함께 동결한다. 따라서 정상화 코드 수정 후 기존 manifest로 실행하면 거부되는 것이 올바른 gate 동작이다.

`derive_execution_snapshot.py`는 기존 `verify_files`를 우회하거나 부모 manifest를 수정하지 않는다. 새 출력 폴더에 다음 검증을 수행한다.

1. 부모가 `LOADED_VERIFIED`이며 지정 연구 DB의6관계를 모두 포함하는지 확인한다.
2. 부모의6개 CSV hash와 모든 비코드 mounted 파일 hash가 여전히 일치해야 한다.
3. 명시적으로 지정한 실행 코드만 새 hash로 기록한다. allowlist는 `query_normalizer.py`와 `graph_rag_retriever.py` 두 파일뿐이다. 데이터·사전·KG hash 변경은 허용하지 않는다.
4. 현재 `marine-scie-pilot-db/scie_model_v3`의6관계를 정적 allowlist SQL과 관계별 `REPEATABLE READ READ ONLY` transaction으로 전체 CSV 재추출한다. 각각의 전체 바이트 hash가 부모 CSV와 같아야 한다. DB 적재·수정은 없다.
5. 부모 manifest·CSV·비코드 파일과 새 코드 hash를 다시 확인하고, 파생 manifest에 기존 `verify_files`를 그대로 적용한다. 모두 통과할 때만 새 `LOADED_VERIFIED`로 확정한다.

부모 manifest 경로/hash, 실행코드 이전·이후 hash, DB 재추출6개 hash, 검증시각과 데이터/coverage/GOLD 미승격을 lineage에 기록한다. 각 관계의 재추출은 각각의 transaction이며 하나의 전역 transaction이라고 주장하지 않는다. 모든 관계가 동일한 불변 부모 내용과 같다는 점을 검증한다. 이후 DB 변경을 영구 방지하는 기능은 아니며 실제 실행은 계속 읽기전용이다.

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.derive_execution_snapshot --parent outputs/scie_model_snapshot_20261030_v3/snapshot_manifest.json --output outputs/scie_model_snapshot_20261031_execution_v1 --refresh-code services/orchestrator/query_normalizer.py
```

원본 약520MB를 새로 추출하므로 디스크 공간과 수십 초~수분이 필요할 수 있다. 실패 시 `DERIVATION_FAILED`와 부분 export를 보존하고 기존 출력 덮어쓰기를 거절한다. 실행 프로파일은 새 폴더의 manifest 경로/hash를 양쪽 baseline/P에 동일하게 연결해야 한다. 프로파일의 모델·예산·원천 coverage는 바꾸지 않는다. 원본 K5 v1 실패는 보존하고 파생 snapshot 검증 후 새 K5 실행 폴더를 사용한다.
