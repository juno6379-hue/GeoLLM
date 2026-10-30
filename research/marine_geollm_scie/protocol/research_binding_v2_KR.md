# 연구 데이터 연결 v2 — 2026-10-30

## 범위와 분리

논문 다음 우선 작업으로 평가계약과 연구용 원천 연결을 보완했다. 운영 소스·운영 DB에는 쓰지 않는다. 기존 연구 DB `scie_pilot`도 그대로 보존하고, 연구 컨테이너 `marine-scie-pilot-db`의 새 DB `scie_binding_v2`에 복사했다. 현재 연결은 본실험 full P 완료가 아니다.

## 데이터 구성

| 관계 | 원천 행 수 | 선택 범위 |
|---|---:|---|
| knowledge.document_chunks | 23,215 | 원천 관계 전체; embedding 포함 |
| serving.marine_gazetteer_current | 1,146 | 2022 해양지명 관계 전체 |
| serving.navigation_aid_current | 314 | 현 원천 관계 전체; 전국 항로표지 완전성 아님 |
| serving.island_gazetteer_current | 1,140 | 현 원천 관계 전체 |
| projection.s101_feature_current | 25,300 | 이전 동결 부산권 subset 재사용 |

문서 중 벡터가 있는 행은 17,593개, 없는 행은 5,622개다. 원천 ID/hash 누락은 0개이며 운영 기본 S-101 metadata 조건에 맞는 문서는 1,401개다. 이 수치는 전체 임베딩 완료나 검색 결과의 관련성을 뜻하지 않는다.

원천은 REPEATABLE READ·READ ONLY transaction으로 COPY했다. 대상 적재 후 같은 정렬 순서로 COPY 재출력하여 행 수와 SHA256를 대조한다. 기존 DB를 DROP/TRUNCATE하거나 원본 row/ID를 재작성하지 않는다. 구조·원천·좌표 범위와 미완료 상태는 snapshot manifest에 보존한다.

## 평가계약

- [18사례 작업 계약](../benchmark/contracts_v4/현황_KR.md): 필수 작업, capability 대안, 원문 span과 승인값 전사를 분리.
- [FC 원문 9문항 근거·답안 후보](../benchmark/contracts_v4/근거답안후보_KR.md): 원 XML 정의, binding, 다중도, 허용값, 판·XPath·hash 직접 확인.
- 원문 추출 검증과 답안 선택의 정답성은 다른 판단이다. 새로운 해석은 DRAFT이고 기존 사용자 승인 v3의 18개 행과 Q4 정답은 변경하지 않았다.

## 실행 조건과 제한

실제 graph smoke는 기존 실행기와 같은 `P_current_production_no_llm` 조건으로 수행한다. 이 조건은 임베딩 API를 차단한다. 문서 relation binding이 정상이어도 Standard RAG의 모델/임베딩 준비 검사는 실패할 수 있다. 이를 모델 오답이나 정상 검색 0건으로 바꾸지 않는다. 저장 벡터를 이용한 self-distance probe는 pgvector 연산 무결성 검사이며 자연어 검색 정확도가 아니다.

공간 범위가 부산권인 S-101 subset으로 독도 Wreck 부재를 증명하지 않는다. Q4의 지명 조회만 사용자 승인 CSV snapshot/기준점과 연결된다. AOI 없는 selected-area 요청과 전국 nearest 요구도 별도 조건으로 유지한다.

## 재현

```text
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.binding_snapshot --output outputs/<새 snapshot 이름>
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.binding_probe --snapshot outputs/scie_binding_snapshot_20261030_v1/snapshot_manifest.json --output outputs/<새 probe 이름>
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.launch_production --session --repeats 1 --database scie_binding_v2 --snapshot-manifest outputs/scie_binding_snapshot_20261030_v1/snapshot_manifest.json --output-dir research/marine_geollm_scie/runs/<새 graph 이름>
```

snapshot 생성은 고정 새 DB명이 이미 존재하면 거절한다. 재실행 때문에 기존 DB를 삭제하지 말고 다음 snapshot 버전의 DB명을 명시적으로 분리한다. 진행 중 실패는 원본을 보존하고 manifest 상태를 확인한다. preflight는 준비검사이며 논문 정확도를 생성하지 않는다.

## 다음 실행 순서

1. 실제 적재/검색 probe와 noLLM graph 관측을 먼저 대조한다.
2. 새 평가계약의 남은 범위와 최소 답안·근거 조건을 확정한다.
3. 임베딩 원천 profile/digest와 검색 대상의 임베딩 누락을 확인한 뒤 연구 전용 모델 접근 조건을 설계한다. noLLM 결과와 모델 연결 결과는 다른 run으로 비교한다.
4. 독도·부산항의 필요한 공간 coverage와 AOI/중복/경계 정책을 확보한다.
5. 동결된 기준으로 실행형 baseline/full P·오류주입·복구·ablation을 수행한다. 미노출 holdout과 독립 검수는 별도로 마련한다.

## 최종 실제 검증

LOADED_VERIFIED: 다섯 관계 51,115행의 원본·재출력 hash 전부 일치. DB probe5개 완료, 별도 실제 bge-m3 질의검색9/9 각3개 후보 반환, noLLM graph6행은 완료2/부분1/차단3이었다. source 파일/hash의 실행 전후 불변 확인. 연구 테스트117 passed. 최초 Windows 상대 mount 실패와 FC 기하 파서 테스트실패는 수정하고 과거 기록을 보존했다. [통합 결과](../latest_binding/report_KR.md)와 [준비검사](../latest_binding/preflight_KR.md)를 먼저 확인한다.
