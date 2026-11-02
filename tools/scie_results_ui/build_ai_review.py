"""Create non-independent AI review drafts without modifying frozen GOLD."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / 'research/marine_geollm_scie'
G = R / 'benchmark/gold_v2_immutable_20261101_v1'
T = R / 'review/20261031_independent_gold_v3'
OUT = R / 'review/20261102_gold_v2_ai_prereview_v1'

NOTES = {
'Q1_01': ('등대를 단일 Lighthouse 코드로 단정하지 않고 구조물 Landmark/Building과 등화 LightAllAround/LightSectored의 조건부 모델을 구분한다.', '네 코드를 모두 한 시설의 필수 구성으로 요구해서는 안 된다. 설명을 위한 대안 목록과 실제 객체 매핑을 구분한다.'),
'Q1_02': ('정박지는 AnchorageArea로 설명하고 FC 정의·point/surface 허용 geometry와 출처를 연결한다.', '일반 정박 행위와 데이터 객체의 존재를 혼동하지 않는다. 정의 질의에는 공간 실행이 필요하지 않다.'),
'Q1_03': ('Wreck의 정의와 point/surface 표현을 FC 근거로 설명한다.', '침선 개념 설명을 실제 침선 위치 검색으로 바꾸지 않는다. 원문과 동등한 의역도 의미 검수 대상이다.'),
'Q2_01': ('구조물 colour와 등화 colour를 구분한다. Landmark/Building은 1~13, LightAllAround와 lightSector는 FC에 연결된 1,3,4,5,6,9,10,11을 제시한다.', 'LightSectored→sectorCharacteristics→lightSector→colour 경로를 확인한다. 전역 colour 코드 목록을 모든 Feature의 허용값으로 복사하지 않는다.'),
'Q2_02': ('RestrictedArea의 restriction과 categoryOfRestrictedArea를 구분하여 Feature별 연결·다중성·허용 코드를 설명한다.', '구역 종류 코드와 실제 제한 행위 코드는 다른 속성이다. 공개 FC 설명을 실제 구역의 법적 허가 또는 비공개 자료 요청으로 해석하지 않는다.'),
'Q2_03': ('Wreck에 실제 연결된 속성 목록·정의·다중성·허용값을 제시한다. waterLevelEffect와 surroundingDepth의 필수 다중성을 확인한다.', 'FC 속성 정의와 특정 침선의 실제 속성값은 별개다. 전역에 존재하는 속성을 Wreck에 연결된 것으로 추정하지 않는다.'),
'Q3_01': ('현재 부산권 snapshot으로 독도 최근접 등대를 확정할 수 없으므로 DATA_OUT_OF_SCOPE/BLOCKED_DATA와 원천 범위 부족을 설명한다. 공간 객체 GOLD는 없다.', '전국 최근접 계산의 정답이나 실세계 0건으로 만들지 않는다. 단순 UNSUPPORTED_OPERATOR 차단은 올바른 coverage 판단 전체를 충족하지 않는다.'),
'Q3_02': ('고정 부산항 polygon과 ST_Covers(reference,target)를 사용한 snapshot 내 AnchorageArea 정답은 빈 집합이다. 원천·범위와 검사 조건을 함께 공개한다.', '유효한 빈 Oracle과 미실행/누락은 다르다. 이 polygon은 연구용 고정 경계이며 법적 항계 전체와 동일하다고 단정하지 않는다.'),
'Q3_03': ('선택 영역이 없으므로 NEEDS_USER_INPUT, MISSING_REFERENCE_GEOMETRY를 반환하고 execution_attempted/started/tool_called/sql_executed=false여야 한다.', '임의 viewport나 기준점으로 대체하지 않는다. 안내 문구만으로 미실행을 인정하지 말고 실행 로그를 확인한다.'),
'Q4_01': ('승인 동도 기준점·2022 CSV·WGS84 지오데식 거리 5000m 이하로 고정한다. 원본 ID 44~54의 11개 지명을 반환하고 출처를 연결한다.', '원천 corpus의 정답이며 독도 주변 실세계 지명의 완전목록이 아니다. S-101 ID와 CSV 원본 ID를 혼용하지 않는다.'),
'Q4_02': ('5000m를 Q4-01의 5km와 같은 조건으로 해석한다. 동일 기준점과 동일 11개 원본 ID 집합이 정답이다.', '단위 변환은 허용되지만 반경·기준점·원천은 변경하지 않는다. 세 표현을 독립 공간 문제로 합산하지 않는다.'),
'Q4_03': ('영어 5 km 질의도 Q4-01·02와 같은 기준점·원천·11개 ID를 사용한다.', '언어 차이만으로 공간 의미나 coverage를 바꾸지 않는다. 개발 노출된 동등 표현군이며 독립 holdout이 아니다.'),
'Q5_01': ('독도 5km의 Lighthouse와 Wreck 두 공간 하위작업 모두 coverage 부족으로 BLOCKED_DATA다. 표준 정의는 별도 부분응답으로만 허용한다.', '한 대상만 처리하고 전체 완료로 선언하거나 두 빈 집합을 실세계 부재로 제시하면 안 된다. 대상별 상태·근거가 필요하다.'),
'Q5_02': ('고정 부산항 polygon과 geometry 간 최소 지오데식 거리 2000m 이하인 AnchorageArea/RestrictedArea 객체 집합을 각각 반환하고 수·거리·정의·원천 범위를 비교한다.', '표현상 polygon 경계 거리와 ST_DWithin(polygon,target)의 내부거리 0은 다를 수 있다. 동결 계약의 실제 predicate를 우선 보존하고 사람이 의미를 확인한다. ID는 snapshot 기록이며 중복 시설 제거 결과가 아니다.'),
'Q5_03': ('독도 Wreck 공간 부분은 BLOCKED_DATA, 실제 object attribute value는 확정하지 않는다. FC 속성 설명은 별도 문서 부분응답으로 가능하다.', 'FC 정의만으로 실제 Wreck 객체 속성값을 만들어서는 안 된다. 추후 in-scope 객체 과제는 object value↔FC definition 연결을 따로 평가해야 한다.'),
'Q6_01': ('Wreck 정의 원문과 FC 2.0.0 판·SHA256·Feature locator를 함께 제시한다.', '원문 인용 정확성과 의미 설명 정확도를 별도로 판단한다. 검색 문서 존재만으로 최종 답변에 인용됐다고 인정하지 않는다.'),
'Q6_02': ('조건부 구조물/등화 모델과 대표 부유표지 LateralBuoy를 FC 정의로 비교한다.', 'LateralBuoy는 부표 전체의 대체가 아닌 한정 대표다. 원질의의 일반 부표 비교를 이 한정 범위로 평가하는 것이 적절한지 사람이 확인해야 한다.'),
'Q6_03': ('AnchorageArea 정의를 뒷받침하는 FC 2.0.0 원문·판·hash·locator를 연결한다.', '원천 제목만 제시하거나 모델의 일반 지식을 인용 근거로 대신하지 않는다. 실제 공간 검색은 요구되지 않는다.'),
}

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def readlines(p): return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def dump(obj): return json.dumps(obj, ensure_ascii=False, indent=2)
def writejson(p, obj): p.write_text(dump(obj), encoding='utf-8')
def link(p, label=None): return f'[{label or p.name}](<{p.resolve().as_posix()}>)'
def compact(obj):
    if isinstance(obj, dict): return {k:compact(v) for k,v in obj.items() if k not in ('geometry_ewkb','geometry_wkt')}
    if isinstance(obj, list): return [compact(v) for v in obj]
    return obj

def main():
    if OUT.exists(): raise SystemExit('Existing draft preserved; use a new version for regeneration.')
    OUT.mkdir(parents=True)
    frozen = {str(p):sha(p) for p in G.iterdir() if p.is_file()}
    originals = {str(p):sha(p) for p in T.iterdir() if p.is_file()}
    contracts = readlines(G/'answer_contracts.jsonl')
    templates = {role: {r['case_id']:r for r in readlines(T/f'reviewer_{role}_blank.jsonl')} for role in ('A','B')}
    consensus = {r['case_id']:r for r in readlines(T/'adjudication_blank.jsonl')}
    fc = ROOT/'outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml'
    tree = ET.parse(fc)
    def locator_check(loc):
        match = re.search(r"local-name\(\)='([^']+)'\]\[\*\[local-name\(\)='code' and text\(\)='([^']+)'",loc)
        if not match: return {'locator':loc,'status':'NOT_EVALUATED'}
        tag,code = match.groups()
        hits = [e for e in tree.iter() if e.tag.split('}')[-1]==tag and any(ch.tag.split('}')[-1]=='code' and ch.text==code for ch in e)]
        return {'locator':loc,'matched_nodes':len(hits),'status':'MATCHED' if len(hits)==1 else 'REVIEW_REQUIRED'}
    source_registry = {}
    def source(p, expected=None):
        p=Path(p);p=p if p.is_absolute() else ROOT/p
        key=p.resolve().as_posix(); actual=sha(p) if p.is_file() else None
        rec={'path':key,'sha256':actual,'expected_sha256':expected,'status':'MISSING' if actual is None else ('HASH_MISMATCH' if expected and actual!=expected else 'HASH_VERIFIED' if expected else 'PRESENT_HASH_RECORDED')}
        source_registry[key]=rec;return rec
    for p in G.iterdir():
        if p.is_file():source(p)
    for p in T.iterdir():
        if p.is_file():source(p)
    fc_rec=source(fc,'2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc')
    q4=contracts[9]['spatial_reference'];q4oracle=Path(q4['oracle_path'])
    oracle_rec=source(q4oracle,q4['oracle_sha256'])
    oracle=json.loads(q4oracle.read_text(encoding='utf-8'))
    csv_rec=source(oracle['source_snapshot']['path'],oracle['source_snapshot']['sha256'])
    snap=ROOT/'outputs/scie_gold_v2_eight_snapshot_20261102_v6/snapshot_manifest.json'
    snapshot=json.loads(snap.read_text(encoding='utf-8'));source(snap)
    for rel in snapshot['relations']:
        if rel['relation'] in ('serving.navigation_aid_current','projection.s101_feature_current'):
            source(snap.parent/rel['csv_path'],rel['sha256'])
    packets=[]; reviewers={'A':[],'B':[]}; adjs=[]
    for i,c in enumerate(contracts,1):
        cid=c['case_id'];a,b=NOTES[cid.removeprefix('PILOT_')]
        doc=c.get('document_scope') or {}; ev=doc.get('evidence_requirements') or {}
        locators=list(ev.get('locators',[]))
        bindings=[]
        for check in c.get('machine_checks',[]):
            if check['id']=='attribute_binding_contract':
                bindings=check['expected']
                locators += [x[k] for x in bindings for k in ('owner_locator','attribute_locator') if x.get(k)]
        evidence={'contract_file':str(G/'answer_contracts.jsonl'),'jsonl_line':i,'contract_record_sha256':hashlib.sha256(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                  'FC_source':fc_rec if doc else None,'locator_checks':[locator_check(l) for l in dict.fromkeys(locators)],
                  'spatial_oracle_file':str(G/'oracle_checks.json'),'source_checks_file':str(G/'source_checks.json'),
                  'Q4_original_csv':csv_rec if c.get('spatial_reference') else None,'Q4_calculation':oracle_rec if c.get('spatial_reference') else None}
        packet={'case_id':cid,'query':c['query'],'ai_recommended_answer':a,'ai_counter_review':b,'evidence':evidence,
                'document_definitions':doc.get('features',[]),'attribute_bindings':bindings,
                'spatial_gold':compact(c.get('spatial_gold')),'spatial_reference':compact(c.get('spatial_reference')),
                'reference_geometry':compact(c.get('reference_geometry')),'expected_spatial_behavior':c.get('expected_spatial_behavior'),
                'machine_checks':c.get('machine_checks',[]),'required_tasks':c['required_task_obligations'],
                'spatial_predicate':c.get('spatial_predicate'),'distance_mode':c.get('distance_mode'),
                'object_identity_policy':c.get('object_identity_policy'),'coverage_reference':c.get('coverage_reference'),
                'scope_notes':c.get('scope_notes',[]),'equivalence_group':c['equivalence_group']}
        packets.append(packet)
        for role in ('A','B'):
            row=templates[role][cid].copy()
            row.update(review_status='AI_PRE_REVIEW_PENDING_HUMAN',independent_human_review=False,independent_expert_review_complete=False,
                       human_approval=False,ai_candidates_seen_before_initial_judgement=None,
                       ai_pre_review={'prepared_by':'AI assistant; A/B are review perspectives, not independent humans','focus':'답안·작업 계약' if role=='A' else '근거·반례·평가 범위',
                                      'recommendation':a if role=='A' else b,'supporting_analysis':b if role=='A' else a,'packet_case_id':cid,'evidence':evidence,
                                      'clarification_required':cid=='PILOT_Q3_03','source_checked_by_ai':True,'source_check_scope':'Local file hash and FC locator checks; stored spatial Oracle inspected, SQL/GIS not rerun',
                                      'decision':'PROVISIONAL_REFERENCE_WITH_REVIEW_POINTS','model_answers_used_to_define_gold':False})
            reviewers[role].append(row)
        ar=consensus[cid].copy(); ar.update(review_status='AI_SYNTHESIS_PENDING_HUMAN',independent_human_review=False,human_approval=False,
            ai_proposed_answer=a,ai_review_points=[b],actual_human_disagreement=None,
            ai_synthesis='두 관점의 AI 초안을 대조한 제안이며 실제 A/B 인간 검수나 합의가 아닙니다.',
            evidence=evidence,ai_proposed_contract_reference={'path':str(G/'answer_contracts.jsonl'),'line':i,'case_id':cid})
        for role in ('A','B'):
            ar['ai_reviewer_'+role+'_record_sha256']=hashlib.sha256(json.dumps(reviewers[role][-1],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        adjs.append(ar)
    for name,items in [('reviewer_A_ai_prereview.jsonl',reviewers['A']),('reviewer_B_ai_prereview.jsonl',reviewers['B']),('adjudication_ai_proposal.jsonl',adjs),('case_evidence_packets.jsonl',packets)]:
        (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items),encoding='utf-8')
    for role,label in [('A','검수자A'),('B','검수자B'),('C','합의검토')]:
        lines=[f'# {label} — GOLD v2 18사례 AI 사전검토본', '', '**AI 작성 · 사용자 검토 대기 · 독립 인간 검수 미완료**', '',
               'A/B는 동일 AI의 서로 다른 검토 관점입니다. 두 명의 독립 검수 또는 실제 합의를 수행했다고 주장하지 않습니다. 기존 GOLD를 제안 근거로 노출하므로 이를 읽은 후의 검토는 AI 보조 검수로 기록하십시오.', '',
               '인간 검수자: ______　검수일: ______　검토 방식(독립 초기 판단/AI 초안 대조): ______', '',
               f'기준: {link(G/"manifest.json")} · {link(OUT/"원본근거_사례별대조_KR.md")} · {link(OUT/"검토안내_KR.md")}', '']
        for packet in packets:
            cid=packet['case_id'];rec=next(c for c in contracts if c['case_id']==cid)
            lines += [f'## {cid} — {packet["query"]}', '',
                      f'- **AI 답안 제안:** {packet["ai_recommended_answer"]}',
                      f'- **{"A의 보완 확인" if role=="A" else "B의 비판 검토" if role=="B" else "합의 전 확인 쟁점"}:** {packet["ai_counter_review"]}',
                      f'- 필수 작업: {", ".join(packet["required_tasks"])}',
                      f'- 추가 입력: {"선택 영역이 필요함. 확보 전 GIS 실행 금지." if cid=="PILOT_Q3_03" else "현재 동결 입력 기준으로 추가 입력을 정답의 필수조건으로 새로 만들지 않음. 원천 범위 부족은 사용자 입력 누락과 구분."}',
                      f'- 평가군: `{rec.get("evaluation_stratum")}` / 동등 표현군: `{packet["equivalence_group"]}`',
                      f'- 원본 계약: {link(G/"answer_contracts.jsonl")} — JSONL {packet["evidence"]["jsonl_line"]}행, `{cid}`',
                      f'- 계약 record SHA256: `{packet["evidence"]["contract_record_sha256"]}`',
                      f'- 상세 원문·locator·객체 ID·거리: {link(OUT/"원본근거_사례별대조_KR.md",cid+" 근거 부록")}의 해당 절',
                      '- **AI 잠정 판단:** 기존 기준을 검토용 제안으로 유지. 위 쟁점은 인간 확인 전 확정하지 않음.',
                      '- 인간 판단(수용/수정/보류): ______', '- 인간 수정 답안·이유·직접 확인한 locator: ______',
                      '- 실제 A/B 불일치·해결 근거: ______' if role=='C' else '- AI 초안 열람 전 독립 답안을 작성했는지 및 원본 위치: ______',
                      '- 인간 검수자·일시·승인: ______', '']
        (OUT/f'{label}_18사례_AI사전검토_GOLDv2_KR.md').write_text('\n'.join(lines),encoding='utf-8')
    lines=['# 원본 근거와 사례별 대조', '', '해시는 이번 로컬 파일에서 재계산했다. FC locator는 해당 XML 노드의 유일 존재를 확인했다. 공간 결과는 보존된 SQL/GIS Oracle을 인용하며 이번 작업에서 DB 질의나 거리 계산을 다시 수행하지 않았다. 인간의 의미 판단·원천 범위 승인과는 다르다.', '']
    for packet in packets:
        lines += [f'## {packet["case_id"]}', '', packet['query'], '', packet['ai_recommended_answer'], '', f'**사람이 확인할 점:** {packet["ai_counter_review"]}', '']
        for feature in packet['document_definitions']:
            lines += [f'### {feature["code"]}', f'- FC 원문: {feature.get("definition")}', f'- 허용 geometry: {feature.get("permitted_primitives")}', f'- locator: `{feature.get("locator")}`','']
        if packet['attribute_bindings']:
            lines += ['| 소유 객체/속성 | 다중성 | Feature 연결 허용값 |','|---|---|---|']
            for b in packet['attribute_bindings']:
                lines += [f'| {b["owner"]} → {b["attribute"]} | {b["lower"]}..{"*" if b.get("unbounded") else b.get("upper")} | {", ".join(b.get("permitted_values",[])) or "코드 목록 없음/복합 또는 수치 속성"} |']
        for title,key in [('공간 GOLD','spatial_gold'),('지명 객체·거리·원본 행','spatial_reference'),('기준 geometry identity(geometry 본문 제외)','reference_geometry'),('기대 공간 행동','expected_spatial_behavior'),('원본 및 locator 확인','evidence')]:
            if packet[key] is not None:lines += ['',f'### {title}', '```json',dump(packet[key]),'```']
        lines += ['',f'- 공간 predicate: `{packet["spatial_predicate"]}`; 거리 정책: `{packet["distance_mode"]}`',f'- 객체 동일성 정책: `{packet["object_identity_policy"]}`','']
    lines += ['## 파일 무결성 목록','']
    for v in source_registry.values():lines += [f'- {link(Path(v["path"]))} — `{v["status"]}` — SHA256 `{v["sha256"]}`']
    (OUT/'원본근거_사례별대조_KR.md').write_text('\n'.join(lines),encoding='utf-8')
    (OUT/'검토안내_KR.md').write_text('''# GOLD v2 AI 사전검토 묶음

18개 사례 각각의 A(답안·작업), B(근거·반례), 합의 제안을 작성했다. 기존 독립 검수 빈 양식은 보존한다. 이 묶음은 AI 초안을 사용자가 검토하기 위한 자료다.

- AI 사전검토 완료와 독립 인간 검수 완료는 다르다. human_approval=false, independent_human_review=false를 유지한다.
- A/B는 서로 다른 인간이나 독립 에이전트 판단이 아니라 동일 AI의 두 검토 관점이다. 실제 인간 간 불일치·합의·서명은 빈칸이다.
- 독립 검수를 원하면 이 초안을 보기 전에 기존 빈 양식으로 각각 판단을 보존한다. 이미 본 경우 노출 사실을 기록하고 AI 보조 검수로 표시한다. 합의 검토는 독립 판단과 별도 절차다.
- 문서에서 AI 제안을 수정한 뒤 인간 이름·일시·확인 출처·판단을 채운다. 이 파일을 승인해도 독립 검수 여부가 자동 true가 되지 않는다.
- 원본 GOLD v2와 이전 실험 결과·채점은 변경하지 않았다. 확정 수정은 별도 GOLD 버전으로 저장하고 비교가능성을 다시 판단해야 한다.
- 18문항은 개발에 노출됐으며 검수 후에도 독립 holdout이 아니다. 모델별 답변이나 v6 점수를 정답 작성 근거로 사용하지 않았다.
- 주요 쟁점: Q3-02 빈 Oracle의 유효성, Q5-02 polygon 거리 의미와 snapshot 객체 중복, Q6-02 대표 부표 범위, 독도 범위 밖 중단과 문서 부분응답 분리.
- FC 원본 hash와 XPath 대응 노드 존재를 확인했다. 공간 Oracle 원본 hash를 대조했지만 이번 작업에서 독립 SQL/GIS를 재실행하지 않았다. 원천 범위의 실세계 완전성은 미승인이다.

각 검토 파일의 사례별 원본 계약 링크와 근거 부록을 함께 읽는다. JSONL은 검수 시스템 연결용이며 인간 입력 필드는 null/false 상태로 보존한다.
''',encoding='utf-8')
    assert len(contracts)==18 and set(NOTES)=={c['case_id'].removeprefix('PILOT_') for c in contracts}
    assert all(sha(Path(p))==h for p,h in {**frozen,**originals}.items())
    checks=[x for p in packets for x in p['evidence']['locator_checks']]
    manifest={'status':'AI_PRE_REVIEW_COMPLETE_PENDING_HUMAN','independent_human_review':False,'independent_expert_review_complete':False,'human_approval':False,
              'case_count':18,'roles':['A','B','AI_SYNTHESIS'],'source_gold':str(G),'gold_manifest_sha256':sha(G/'manifest.json'),
              'blank_templates_preserved':True,'frozen_gold_preserved':True,'spatial_sql_rerun':False,'model_outputs_used_to_define_gold':False,
              'fc_locator_checks':len(checks),'fc_locator_unresolved':[x for x in checks if x['status']!='MATCHED'],
              'source_files':list(source_registry.values()),'outputs':[{'path':p.name,'sha256':sha(p)} for p in OUT.iterdir() if p.is_file()]}
    writejson(OUT/'manifest.json',manifest)
    print(dump({'output':str(OUT),'cases':18,'fc_checks':len(checks),'unresolved':manifest['fc_locator_unresolved'],'source_issues':[v for v in source_registry.values() if v['status'] in ('MISSING','HASH_MISMATCH')]}))

if __name__=='__main__':main()
