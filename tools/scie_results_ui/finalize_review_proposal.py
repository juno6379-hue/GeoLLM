"""Prepare named review proposals; never attest human review or mutate GOLD."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
R = ROOT/'research/marine_geollm_scie'
PRE = R/'review/20261102_gold_v2_ai_prereview_v1'
OUT = R/'review/20261102_gold_v2_AAA_BBB_final_proposal_v2'
ATTACHMENT = Path('C:/Users/최준오/Downloads/검수자A_18문항_AI보조검수_작성본_KR.md')
GOLD = R/'benchmark/gold_v2_immutable_20261101_v1'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def link(p,label=None):return f'[{label or p.name}](<{p.resolve().as_posix()}>)'
def main():
    if OUT.exists():raise SystemExit('Existing output preserved.')
    before={str(p):sha(p) for folder in (PRE,GOLD) for p in folder.iterdir() if p.is_file()}
    text=ATTACHMENT.read_text(encoding='utf-8-sig');attachment_hash=sha(ATTACHMENT)
    sections={m.group(1):m.group(2) for m in re.finditer(r'^## (PILOT_Q\d_\d+) — [^\n]+\n(.*?)(?=^## |\Z)',text,re.M|re.S)}
    packets=[json.loads(s) for s in (PRE/'case_evidence_packets.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(sections)==len(packets)==18
    OUT.mkdir(parents=True)
    saved=OUT/'첨부원본_AI보조검수_A.md'
    shutil.copyfile(ATTACHMENT,saved)
    evidence=OUT/'사례별_원본근거_객체ID_거리_해시_최종_KR.md'
    proposal=OUT/'AAA_BBB_합의검토_최종제안본_KR.md'
    header=['# AAA·BBB 합의검토 최종 제안본','',
            '**문서 작성 완료 · AI 보조 검토 · 실제 인간 합의/승인 대기**','',
            '- 검수자 A 표시명: **AAA** / 검수자 B 표시명: **BBB** (사용자 지정).',
            '- AAA란은 제공된 AI 보조 작성본을 연결한다. BBB란은 기존 AI 반례·근거 검토를 연결한다. BBB가 직접 작성한 별도 검수 기록은 제공되지 않았다.',
            '- 첨부의 “승인/조건부 승인”은 AI 초안의 판단 표현이며 AAA·BBB의 서명·인간 승인으로 승격하지 않는다.',
            '- 최종은 문서 편집본의 상태다. `human_approval=false`, `independent_human_review_complete=false`. 이름 지정만으로 검수 완료를 의미하지 않는다.',
            '- 기존 GOLD v2·실험 결과·평가 점수는 변경하지 않았다. 검토 후 변경은 별도 GOLD 버전으로 관리한다.','',
            f'첨부 원본: {link(saved)} · SHA256 `{attachment_hash}`',
            f'기준 GOLD: {link(GOLD/"manifest.json")} · SHA256 `{sha(GOLD/"manifest.json")}`',
            f'근거 상세: {link(evidence)}','',
            '## 18사례 제안 요약','', '| 사례 | AAA 연결 초안 | 최종 제안 상태 |', '|---|---|---|']
    records=[];blocks=[]
    ed=['# 사례별 원본 근거·객체 ID·거리·해시 — 최종 편집본','',
        '검수자 표시명 AAA·BBB. AI 보조 합의제안의 근거자료이며 독립 인간 검수 완료 문서가 아니다. 공간 Oracle을 다시 실행하지 않고 동결 원본과 기존 검산 산출물을 연결했다. 거리 원값은 아래 표에 보존한다. 시설 단위 중복 제거를 새로 적용하지 않는다.', '',
        f'합의 제안: {link(proposal)} · 첨부: {link(saved)} · SHA256 `{attachment_hash}`', '',
        '## 해석 및 동기화 규칙','',
        '- 첨부의 spatial_source_condition=null을 그대로 정답 부재로 읽지 않는다. Q3-02/Q5-02에는 고정 부산항 polygon·원천 snapshot·객체 집합을 아래에 연결했다.',
        '- Q3-01/Q5-01/Q5-03은 범위 밖: 공간 GOLD null. Q3-03은 영역 누락: 미실행. Q3-02의 빈 집합은 이 고정 snapshot/predicate에 한한 유효 Oracle다.',
        '- Q5-02는 polygon 자체와 대상 geometry의 최소 거리다. polygon 외곽선만의 거리가 아니므로 내부/교차 객체의 0m는 가능하다. 동결 SQL을 변경하지 않는다.',
        '- 정박지 3개는 snapshot 기록 3개이며 독립 실재 시설 3개로 해석하지 않는다. 연구 경계를 법적 부산항 전체 경계로 일반화하지 않는다.',
        '- 원본 Oracle의 상태나 과거 승인 문자열은 원본 생성 당시의 기록이다. 현재 인간 승인 증거로 사용하지 않는다.','']
    def field(body,label):
        m=re.search(r'^- '+re.escape(label)+r': (.*)$',body,re.M)
        return m.group(1) if m else '첨부에 항목 없음'
    for p in packets:
        cid=p['case_id'];body=sections[cid];judgement=field(body,'판단 및 근거')
        cond=judgement.startswith('조건부 승인')
        status='조건 유지·사람 확인 대기' if cond else '기준 유지 제안·사람 확인 대기'
        header.append(f'| {cid} | {"조건부 승인(AI)" if cond else "승인(AI)"} | {status} |')
        sp={k:p.get(k) for k in ['reference_geometry','spatial_gold','spatial_reference','expected_spatial_behavior','coverage_reference','spatial_predicate','distance_mode','object_identity_policy']}
        rec={'case_id':cid,'query':p['query'],'reviewer_A_name':'AAA','reviewer_B_name':'BBB','review_mode':'AI_ASSISTED_FINAL_PROPOSAL',
             'reviewer_A_material_origin':'USER_SUPPLIED_AI_DRAFT','reviewer_B_material_origin':'PRIOR_AI_COUNTER_REVIEW_NOT_HUMAN_SUBMISSION',
             'attachment_sha256':attachment_hash,'attachment_locator':cid,'A_provisional_judgement':judgement,
             'A_acceptable_answer':field(body,'허용 답안과 대안'),'B_provisional_review':p['ai_counter_review'],
             'proposed_answer':p['ai_recommended_answer'],'spatial_source_condition':sp,'evidence':p['evidence'],
             'actual_human_disagreement':None,'human_approval':False,'independent_human_review_complete':False,
             'reviewer_A_signed_at':None,'reviewer_B_signed_at':None,'adjudicated_at':None,'status':'FINAL_PROPOSAL_PENDING_HUMAN_REVIEW'}
        records.append(rec)
        blocks += [f'## {cid} — {p["query"]}','',
                   f'**AAA 담당란 — 첨부 AI 보조 의견:** {judgement}', '',
                   f'- 허용 답안: {field(body,"허용 답안과 대안")}',
                   f'- 필수 근거: {field(body,"반드시 포함할 근거")}',
                   f'**BBB 담당란 — AI 대조 검토 제안:** {p["ai_counter_review"]}', '',
                   f'**합의안 제안:** {p["ai_recommended_answer"]}',
                   f'- 제안 상태: {status}. 실제 두 검수자의 일치/불일치는 아직 기록되지 않음.',
                   f'- 추가 입력: {field(body,"추가 입력 필요 여부와 이유")}',
                   f'- 공간 정답/미확정: {field(body,"공간 정답 또는 미확정 사유")}',
                   f'- 재현 근거: {link(evidence,cid+" 근거")} 해당 절. GOLD JSONL {p["evidence"]["jsonl_line"]}행.',
                   '- AAA 최종 의견·서명·일시: ____________________',
                   '- BBB 최종 의견·서명·일시: ____________________',
                   '- 합의 판단(수용/수정/보류)·수정 근거·합의일: ____________________', '']
        ed += [f'## {cid} — {p["query"]}', '',
               f'- GOLD 계약: {link(GOLD/"answer_contracts.jsonl")} JSONL {p["evidence"]["jsonl_line"]}행',
               f'- 정규화 JSON record SHA256: `{p["evidence"]["contract_record_sha256"]}` (UTF-8, sort_keys, compact separators)',
               f'- AAA 연결 의견: {judgement}',f'- BBB 검토 쟁점: {p["ai_counter_review"]}','']
        for f in p['document_definitions']:
            ed += [f'### FC {f["code"]}',f'- 원문: {f.get("definition")}',f'- geometry: {f.get("permitted_primitives")}',f'- locator: `{f.get("locator")}`','']
        if p['attribute_bindings']:
            ed += ['| 소유/속성 | 다중성 | 연결된 코드와 명칭 |','|---|---|---|']
            for b in p['attribute_bindings']:
                labels={v['value']:v['label'] for v in b.get('global_listed_values',[])}
                vals=', '.join(v+': '+labels.get(v,'') for v in b['permitted_values']) or '복합/수치 등, 코드목록 없음'
                ed += [f'| {b["owner"]} → {b["attribute"]} | {b["lower"]}..{"*" if b["unbounded"] else b["upper"]} | {vals} |']
        if p['reference_geometry']:
            ed+=['','### 고정 기준기하 (첨부 null 보완)','```json',json.dumps(p['reference_geometry'],ensure_ascii=False,indent=2),'```']
        if p['spatial_gold'] is not None:
            for feature,sg in p['spatial_gold'].items():
                ed += ['',f'### {feature}: {len(sg["object_ids"])}개 snapshot 기록',f'- 원천 snapshot SHA256: `{sg["source_snapshot_sha256"]}`',f'- 전체 ID: `{", ".join(sg["object_ids"]) or "[] (유효 빈 집합)"}`',
                       '| 객체 ID | 기준 polygon 최소 거리(m) | dataset / version |','|---|---:|---|']
                for obj in sg['objects']:ed += [f'| {obj["id"]} | {obj.get("harbour_distance_m","해당 없음")} | {obj.get("dataset_name")} / {obj.get("dataset_version_id")} |']
                ds=[o['harbour_distance_m'] for o in sg['objects'] if 'harbour_distance_m' in o]
                ed += [f'- 거리 최소/최대: {min(ds) if ds else "해당 없음"} / {max(ds) if ds else "해당 없음"} m.']
        if p['spatial_reference']:
            sr=p['spatial_reference']
            ed += ['','### 동도 기준점·CSV 지명 거리', f'- 기준점: `{json.dumps(sr["reference_geometry_source"],ensure_ascii=False)}`',
                   f'- 정책: {sr["distance_policy"]}',f'- CSV SHA256: `{sr["dataset_snapshot_sha256"]}`',f'- Oracle SHA256: `{sr["oracle_sha256"]}`',
                   '| 원본 객체 ID | 지명 | CSV 행 | PostGIS 거리(m) | Vincenty 거리(m) |','|---|---|---:|---:|---:|']
            for o in sr['objects']:ed += [f'| {o["object_id"]} | {o["name"]} | {o["csv_line"]} | {o["distance_postgis_m"]} | {o["distance_vincenty_m"]} |']
        if p['expected_spatial_behavior']:ed += ['','### 범위 밖 정답 행동','```json',json.dumps(p['expected_spatial_behavior'],ensure_ascii=False,indent=2),'```']
        ed += ['',f'- predicate: `{p["spatial_predicate"]}` / 거리 정책: `{p["distance_mode"]}`',
               '### 파일·locator 검증 기록','```json',json.dumps(p['evidence'],ensure_ascii=False,indent=2),'```','']
    manifest1=json.loads((PRE/'manifest.json').read_text(encoding='utf-8'))
    ed+=['## 이번 편집 시 재확인한 원본 해시','']
    verified=[]
    for src in manifest1['source_files']:
        path=Path(src['path']);actual=sha(path);assert actual==src['sha256'],str(path)
        verified.append({'path':str(path),'sha256':actual})
        ed += [f'- {link(path)} — `{actual}`']
    proposal.write_text('\n'.join(header+['']+blocks),encoding='utf-8')
    evidence.write_text('\n'.join(ed),encoding='utf-8')
    (OUT/'AAA_BBB_합의제안_18사례.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    assert all(sha(Path(p))==v for p,v in before.items())
    assert sha(ATTACHMENT)==attachment_hash==sha(saved)
    for file in (proposal,evidence):
        s=file.read_text(encoding='utf-8');assert len(re.findall(r'^## PILOT_',s,re.M))==18
        for target in re.findall(r'\]\(<([^>]+)>\)',s):assert Path(target).is_file(),target
    manifest={'status':'FINAL_DOCUMENT_PROPOSAL_PENDING_HUMAN','reviewers':{'A':'AAA','B':'BBB'},'case_count':18,
              'human_approval':False,'independent_human_review_complete':False,'attachment_sha256':attachment_hash,
              'source_gold_unchanged':True,'prior_draft_unchanged':True,'spatial_sql_rerun':False,'verified_sources':verified,
              'outputs':[{'path':p.name,'sha256':sha(p)} for p in OUT.iterdir() if p.is_file()]}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'folder':str(OUT),'cases':18,'verified_source_files':len(verified),'human_approval':False},ensure_ascii=False))

if __name__=='__main__':main()
