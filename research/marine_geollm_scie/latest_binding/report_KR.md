# 다음 우선 작업 결과 — 2026-10-30

**연구용 데이터 연결과 실제 검색 관측을 완료했다. 전체 논문 비교실험은 아직 NOT_READY다.**

- 작업 중심 평가계약 18건을 작성하고 승인 v3와 새로운 해석을 분리했다. 기존 GOLD는 변경하지 않았다.
- 정의·속성·출처 9문항에 FC 2.0.0 원 XML의 정의, 기하, binding, 다중도, 허용값, XPath·hash를 연결했다.
- 별도 연구 DB scie_binding_v2에 5관계 51,115행을 적재했다. 원본/적재 재출력 5개 CSV의 SHA256가 모두 일치했다. 운영 DB 쓰기 없음, 이전 연구 DB 보존.
- 문서 23,215개 중 embedding 17,593개/미완료 5,622개. 기본 S-101 metadata 조건은 1,401개다. 미완료를 전체 벡터화 완료로 표시하지 않는다.
- READ ONLY 실제 DB probe 5개: 문서 통계, 저장벡터 자기거리 0, Wreck 원문 발췌3개, 독도 5km 지명11개, 부산권 S-101 coverage 확인.
- 원문 문서질의9개에 실제 bge-m3 임베딩 후 연구 DB에서 각3개 문서를 반환했다. 모델 digest 불변을 확인했다. 저장벡터 생성모델 profile은 미검증이며 유사도·3건 반환을 근거 정확도로 표시하지 않는다. 일부 결과에는 DCEG·portrayal·S-158 문서가 섞여 있어 질의별 표준 근거 적합도 검수가 필요하다.

| 실제 noLLM graph 사례 | 결과 | 해석 |
|---|---|---|
| Q1_03 / Q2_03 | BLOCKED | 문서 relation binding은 해소. 임베딩 차단 profile로 벡터검색 불가 |
| Q3_03 | BLOCKED | selected AOI 부재인데 문서 경로 선택. 별도 수정 backlog |
| Q4_01 | COMPLETED / 11개 | 연구 DB의 실제 해양지명 공간검색 |
| Q5_03 | PARTIAL / 공간0개 | 속성설명 미충족. 독도 Wreck coverage가 없어 0건의 공간정확성 미확정 |
| Q6_03 | COMPLETED / 문서3개 | FC/DCEG exact·lexical 경로. DCEG2개 DB 원문·hash 확인. 정규화의 식별자 내부치환 결함은 별도 |

noLLM graph와 별도 임베딩 검색 component를 합쳐 full P라고 부르지 않는다. Windows 상대 bind 경로로 실패한 최초 graph_v2 run은 보존하고 resolve 수정 후 graph_v2_ready를 새로 실행했다. 신규 FC 추출기의 기하 읽기 오류도 테스트에서 발견해 수정하고 초기 실패 산출물을 보존했다.

## 확인할 문서

- [18문항 계약](../benchmark/contracts_v4/현황_KR.md)
- [9문항 실제 근거·답안 후보](../benchmark/contracts_v4/근거답안후보_KR.md)
- [데이터 구성·재현·다음 작업](../protocol/research_binding_v2_KR.md)
- [독립 오류 감사](../issues/research_data_binding_audit_20261030.md)
- [준비검사](../protocol/research_preflight_KR.md)

## 남은 우선순위

1. 새 작업계약·최소답안/필수근거 범위 검수 및 확정.
2. 연구 전용 모델/embedding profile 고정과 full graph 연결. 기존 noLLM 실험과 분리.
3. selected AOI 요청의 오경로 및 표준식별자 내부 사전치환을 별도 시스템 수정 에이전트가 재현·보완.
4. 공간 과업의 coverage/AOI/시설중복·경계 정책 확보 후 같은 원천에서 공간 oracle 확장.
5. matched baseline/full P, 오류주입·bounded recovery·ablation 및 미노출 평가.

## 최종 검증

연구 테스트 **117 passed**. 준비검사 v2는 193개 검사를 실행했으며 원천·관계·적재·관측 연결은 확인했지만 신규 계약 승인/저장벡터 profile/AOI·coverage가 미확정이므로 NOT_READY다. [준비검사 상세](preflight_KR.md). 기존 실패/이전 run과 Results/latest는 보존했다.
