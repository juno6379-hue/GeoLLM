"""Prepare blinded answer review and import actual human labels without fabricating them."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
from collections import Counter
from datetime import date
from research.marine_geollm_scie.runners.report_eight import verify_raw
from research.marine_geollm_scie.evaluation.v2_observations import normalize

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research/marine_geollm_scie'
RUN=R/'runs/20261102_gold_v2_eight_k1_v6'
GOLD=R/'benchmark/gold_v2_immutable_20261101_v1'
OUT=R/'review/20261102_answer_semantic_review_v1'
DIMENSIONS=('meaning_correct','required_tasks_complete','evidence_supported','no_unsupported_claims')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rows(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(p,x):p.write_text(''.join(json.dumps(a,ensure_ascii=False)+'\n' for a in x),encoding='utf-8')
def display_projection(value):
    if isinstance(value,dict):
        value=dict(value)
        if value.get('document_answers')==[value.get('document_answer')]:value.pop('document_answers')
        return {k:display_projection(v) for k,v in value.items() if k not in ('geometry','geometry_ewkb','geometry_wkt','coordinates','tool_receipts')}
    if isinstance(value,list):return [display_projection(v) for v in value]
    return value

def empty_label(item,reviewer):
    return dict(answer_id=item['answer_id'],answer_sha256=item['answer_sha256'],
        gold_manifest_sha256=item['gold_manifest_sha256'],display_sha256=item.get('display_sha256'),reviewer=reviewer,
        author_type='HUMAN',human_completed=False,independent_review_confirmed=False,
        reviewed_at=None,dimensions=dict.fromkeys(DIMENSIONS),rationale='',
        answer_evidence_quote='',gold_evidence_locator='',human_label_source='')

def validate_labels(labels,items,reviewer):
    by_id={i['answer_id']:i for i in items};found={};complete={}
    for x in labels:
        aid=x.get('answer_id')
        if aid not in by_id or aid in found:raise ValueError('Unknown or duplicate answer ID')
        found[aid]=x
        item=by_id[aid]
        if x.get('reviewer')!=reviewer:raise ValueError('Reviewer identity mismatch')
        for k in ('answer_sha256','gold_manifest_sha256','display_sha256'):
            if x.get(k)!=item.get(k):raise ValueError('Label source hash mismatch')
        if x.get('human_completed') is not True:continue
        if x.get('author_type')!='HUMAN' or x.get('independent_review_confirmed') is not True:
            raise ValueError('Human independent answer review attestation required')
        try:date.fromisoformat(x.get('reviewed_at',''))
        except (ValueError,TypeError):raise ValueError('Actual review date required')
        ds=x.get('dimensions',{})
        if set(ds)!=set(DIMENSIONS) or any(type(ds[k]) is not bool for k in DIMENSIONS):
            raise ValueError('Four explicit boolean semantic judgments required')
        for k in ('rationale','answer_evidence_quote','gold_evidence_locator','human_label_source'):
            if not isinstance(x.get(k),str) or not x[k].strip():raise ValueError('Per-answer evidence and human label provenance required')
        # No natural-language metric substitutes for explicit submitted judgments.
        complete[aid]=x
    return complete

def summarize_labels(items,a,b,consensus,mapping):
    aa=validate_labels(a,items,'AAA');bb=validate_labels(b,items,'BBB')
    paired=set(aa)&set(bb);same={k for k in paired if aa[k]['dimensions']==bb[k]['dimensions']}
    adopted={};seen=set();item_by_id={i['answer_id']:i for i in items}
    for c in consensus:
        aid=c.get('answer_id')
        if aid not in item_by_id or aid in seen:raise ValueError('Unknown or duplicate consensus ID')
        seen.add(aid)
        if c.get('human_completed') is not True:continue
        if aid not in paired:raise ValueError('Consensus requires both independent reviews')
        validate_labels([{**c,'reviewer':'AAA+BBB'}],[item_by_id[aid]],'AAA+BBB')
        if c.get('reviewer')!='AAA+BBB':raise ValueError('Consensus reviewer mismatch')
        if c.get('reviewer_A_label_sha256')!=digest(aa[aid]) or c.get('reviewer_B_label_sha256')!=digest(bb[aid]):
            raise ValueError('Consensus must bind exact A/B judgments')
        adopted[aid]=c
    total=len(items);complete=len(adopted)==total and total>0
    def success(x):return all(x['dimensions'].values())
    n=len(paired);agree=sum(success(aa[k])==success(bb[k]) for k in paired)
    pa=sum(success(aa[k]) for k in paired)/n if n else None
    pb=sum(success(bb[k]) for k in paired)/n if n else None
    pe=pa*pb+(1-pa)*(1-pb) if n else None
    kappa=(agree/n-pe)/(1-pe) if n and pe!=1 else None
    bymethod={}
    for m in sorted({x['method'] for x in mapping}):
        ids={x['answer_id'] for x in mapping if x['method']==m};known=ids&set(adopted)
        bymethod[m]=dict(total=len(ids),measured=len(known),correct=sum(success(adopted[k]) for k in known),
            accuracy=sum(success(adopted[k]) for k in known)/len(ids) if len(known)==len(ids) and ids else None)
    return dict(status='HUMAN_ANSWER_SCORING_COMPLETE' if complete else 'AWAITING_HUMAN_ANSWER_LABELS',
        source_run_id=RUN.name,gold_manifest_sha256=sha(GOLD/'manifest.json'),
        preparation_complete=True,total_answers=total,reviewer_A_completed=len(aa),reviewer_B_completed=len(bb),
        paired_completed=n,consensus_completed=len(adopted),human_answer_scoring_complete=complete,
        semantic_human_accuracy=sum(success(x) for x in adopted.values())/total if complete else None,
        agreement=dict(paired=n,full_dimension_agreements=len(same),binary_agreements=agree,
                       percent_agreement=agree/n if n else None,cohen_kappa=kappa),by_method=bymethod,
        gold_review_complete=True,gold_review_basis='USER_ATTESTATION',
        limitations=['GOLD 검수 승인은 144개 모델 답변에 대한 인간 의미 채점과 별개입니다.',
            '실험 방법 라벨만 가립니다. 정규화 답변의 문체·내부 식별자로 방법이 추정될 수 있어 완전 블라인딩이 아닙니다. coordinator_only는 검수자에게 공유하지 않습니다.',
            'AI 보조 GOLD와 개발 문항을 사용하므로 새로운 독립 홀드아웃 평가가 아닙니다.',
            '인간 작성 여부는 검수자 확인 기록을 근거로 하며 전자서명 인증은 아닙니다.'])

def prepare():
    if OUT.exists():raise FileExistsError('Existing package preserved')
    raw=rows(RUN/'comparison/observations.jsonl');assert len(raw)==144
    for r in raw:verify_raw((RUN/'comparison').resolve(),r)
    gold={x['case_id']:x for x in rows(GOLD/'answer_contracts.jsonl')}
    random.Random(20261102144).shuffle(raw)
    items=[];mapping=[]
    for n,r in enumerate(raw,1):
        aid=f'ANSWER_{n:03d}'
        final=r.get('final_state',{}).get('final_dict') if isinstance(r.get('final_state'),dict) else None
        original=r.get('emitted_answer') if isinstance(r.get('emitted_answer'),dict) else final
        # Preserve exact submitted answer payload; no replacement with retrieval, GOLD or candidate plan.
        normalized=normalize(r)
        displayed=display_projection(normalized.get('answer'))
        item=dict(answer_id=aid,query=r['query'],case_id=r['case_id'],answer=displayed,display_sha256=digest(displayed),
            projection='v2_emitted_only normalized final answer; geometry blobs and duplicate tool receipt copies omitted; identical singleton document_answers deduplicated; prose not truncated',
            answer_sha256=digest(original),gold_manifest_sha256=sha(GOLD/'manifest.json'),
            gold_contract={k:display_projection(v) for k,v in gold[r['case_id']].items() if k in ('case_id','required_task_obligations','forbidden_substitutions','expected_spatial_behavior','scope_notes')},
            gold_reference_path='gold_reference/'+r['case_id']+'.json',answer_absence_note='원문 최종 답안 없음' if original is None else None)
        items.append(item)
        mapping.append(dict(answer_id=aid,case_id=r['case_id'],method=r['method'],repeat=r['repeat'],
            raw_artifact_path=r['raw_artifact_path'],raw_artifact_sha256=r['raw_artifact_sha256'],
            answer_sha256=digest(original),display_sha256=digest(displayed)))
    a=[empty_label(x,'AAA') for x in items];b=[empty_label(x,'BBB') for x in reversed(items)]
    consensus=[dict(empty_label(x,'AAA+BBB'),reviewer_A_label_sha256=None,reviewer_B_label_sha256=None) for x in items]
    OUT.mkdir(parents=True);(OUT/'coordinator_only').mkdir();(OUT/'gold_reference').mkdir()
    for cid,contract in gold.items():dump(OUT/'gold_reference'/(cid+'.json'),display_projection(contract))
    jsonl(OUT/'blinded_answers.jsonl',items);jsonl(OUT/'AAA_labels.jsonl',a);jsonl(OUT/'BBB_labels.jsonl',b)
    jsonl(OUT/'consensus_labels.jsonl',consensus);jsonl(OUT/'coordinator_only/method_mapping.jsonl',mapping)
    dump(OUT/'summary.json',summarize_labels(items,a,b,consensus,mapping))
    info=['# 144답변 독립 인간 의미 채점 안내','',
        'AAA·BBB의 기존 GOLD18 승인과 이번 144답변 채점은 구분한다. 현재 실제 답변별 인간 판단은 수령하지 않았다.',
        'AAA_labels.jsonl / BBB_labels.jsonl을 각각 독립 작성한다. 상대 판단·coordinator_only 폴더·기계 채점 결과를 보지 않는다.',
        'blinded_answers.jsonl은 방법명을 숨긴 원문 최종 답안과 승인 GOLD를 제공한다. 답변 문체/구조에서 방법이 추정될 수 있어 완전 블라인딩은 아니다.',
        '고정 순서는 재현 가능하며 AAA와 BBB의 양식 순서는 반대다. 독립성은 접근통제가 아닌 절차적 분리다.',
        '각 답변마다 dimensions 네 항목(true/false), rationale, answer_evidence_quote, gold_evidence_locator, human_label_source(실제 작성 기록), reviewed_at(YYYY-MM-DD), human_completed=true, independent_review_confirmed=true를 입력한다.',
        'meaning_correct: 요청 의미와 사실 관계가 맞는가. required_tasks_complete: 필수 하위작업을 모두 충족하는가. evidence_supported: 주장이 제시한 원본 근거와 맞는가. no_unsupported_claims: 근거 없는 좌표/객체/실행/권위 주장이 없는가.',
        '주 지표는 네 항목 모두 true인 답변의 비율이다. 정답 행동이 추가입력/자료범위 차단이면 그 행동과 설명의 적합성을 채점한다. 객체 검색 미실행 자체를 항상 의미오류로 처리하지 않는다.',
        '원문 답안이 없으면 absence note를 인용하고 실패 사유를 기록한다. 사례별 판단 없이 전체 동일 값을 채우지 않는다.',
        '독립 기록을 확정한 뒤 consensus_labels.jsonl에 합의 판단을 작성한다. reviewer_A/B_label_sha256은 각 실제 label 객체의 canonical JSON SHA256이다. disagreements와 agreement 모두 원래 A/B 기록으로 계산한다.',
        '실행: .venv/Scripts/python.exe -m tools.scie_results_ui.prepare_semantic_review --import-labels <입력폴더> --output <새결과폴더>',
        '입력폴더는 AAA_labels.jsonl, BBB_labels.jsonl, consensus_labels.jsonl을 포함한다. 기존 기록/결과는 덮지 않는다.',
        '검증기는 실제 사람의 신원을 증명하지 않는다. 사람 작성 확인과 답변별 근거 기록을 요구하며 AI 판단을 HUMAN으로 바꾸어 입력해서는 안 된다.','',
        '## 확인한 기존 자료',
        'Downloads의 A/B 18문항 파일은 AI 보조 GOLD 초안이다. 기존 승인 기록은 GOLD18 전체 승인으로, 144답변 label이 아니다. 따라서 144답변 인간 의미 정확도는 현재 null이다.']
    info += ['','## 실제 작성 순서','원본 패키지를 작업 폴더로 복사한 뒤 AAA/BBB Markdown의 human-label JSON 블록을 편집한다. 원본 폴더는 변경하지 않는다.', 'Copy-Item -LiteralPath research/marine_geollm_scie/review/20261102_answer_semantic_review_v1 -Destination outputs/human_answer_submission_20261102 -Recurse', 'AAA/BBB 완료 후: .venv/Scripts/python.exe -m tools.scie_results_ui.prepare_semantic_review --prepare-consensus outputs/human_answer_submission_20261102 --markdown --output outputs/human_answer_consensus_20261102', '새 합의 폴더의 consensus_labels.jsonl 실제 판단을 작성한 뒤: .venv/Scripts/python.exe -m tools.scie_results_ui.prepare_semantic_review --import-labels outputs/human_answer_consensus_20261102 --output outputs/human_answer_scored_20261102', '원문 전체 hash와 정규화 표시답안 hash를 분리한다. 최종 답안 정규화에서 geometry 좌표 배열/대형 WKT·EWKB는 표시만 제외하고 객체 ID·거리·원천 hash·답변 본문을 유지한다. 정확한 원본은 coordinator 경로/hash로 보존한다. 문체·내부 식별자에 따른 부분 방법라벨 가림이다.', 'UI 반영은 --import-labels 시 --output을 research/marine_geollm_scie/review 아래의 새 폴더로 지정하고 --publish-ui를 명시한다. 기본은 비공개이며 기존 준비 패키지를 수정하지 않는다.']
    (OUT/'채점안내_KR.md').write_text('\n'.join(info)+'\n',encoding='utf-8')
    # Human-readable independent packets omit mapping, latency, model/status and machine verdicts.
    for reviewer,seq in [('AAA',items),('BBB',list(reversed(items)))]:
        lines=[f'# {reviewer} — 독립 인간 답변 채점 144건','', '실험 방법 라벨과 기계 채점은 별도 분리했다. 원문 내부의 실행 상태·지연·식별자는 보존되어 완전 블라인딩이 아니다. 아래 human-label 블록에 판단을 기록한다.','']
        for item in seq:
            lines += [f"## {item['answer_id']} — {item['query']}",'',f"답안 hash: `{item['answer_sha256']}`",'','### 실제 최종 답안','```json',json.dumps(item['answer'],ensure_ascii=False,indent=2),'```','','### 승인 GOLD',f"[해당 사례 전체 GOLD]({item['gold_reference_path']})",'```json',json.dumps(item['gold_contract'],ensure_ascii=False,indent=2),'```','','### 입력할 인간 채점 기록','```human-label',json.dumps(empty_label(item,reviewer),ensure_ascii=False,indent=2),'```','']
        (OUT/f'{reviewer}_144답변_독립채점_KR.md').write_text('\n'.join(lines),encoding='utf-8')
    dump(OUT/'manifest.json',dict(status='PREPARED_NOT_HUMAN_SCORED',observations_sha256=sha(RUN/'comparison/observations.jsonl'),
        gold_manifest_sha256=sha(GOLD/'manifest.json'),raw_hashes_verified=144,
        files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}))
    print('Prepared 144 blinded answers; actual human labels 0')

def markdown_labels(path):
    text=path.read_text(encoding='utf-8-sig')
    blocks=re.findall(r"```human-label\s*\n(.*?)\n```",text,re.S)
    if not blocks:raise ValueError('No human-label blocks')
    return [json.loads(x) for x in blocks]

def read_submitted(source,name,markdown=False):
    if markdown and name in ('AAA','BBB'):
        return markdown_labels(source/f'{name}_144답변_독립채점_KR.md')
    return rows(source/(name+'_labels.jsonl'))

def validate_package():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    if sha(GOLD/'manifest.json')!=manifest['gold_manifest_sha256']:
        raise ValueError('Pinned GOLD changed; old labels cannot be attributed to new GOLD')
    for name,h in manifest['files'].items():
        if sha(OUT/name)!=h:raise ValueError('Original review package changed')
    return manifest

def prepare_consensus(source,output,markdown=False):
    validate_package()
    if output.exists():raise FileExistsError('New consensus output required')
    items=rows(OUT/'blinded_answers.jsonl')
    a=validate_labels(read_submitted(source,'AAA',markdown),items,'AAA')
    b=validate_labels(read_submitted(source,'BBB',markdown),items,'BBB')
    if not a or set(a)!=set(b):raise ValueError('Matching independently completed answer IDs required')
    records=[dict(empty_label(i,'AAA+BBB'),reviewer_A_label_sha256=digest(a[i['answer_id']]),
        reviewer_B_label_sha256=digest(b[i['answer_id']])) for i in items if i['answer_id'] in a]
    output.mkdir(parents=True)
    jsonl(output/'AAA_labels.jsonl',list(a.values()));jsonl(output/'BBB_labels.jsonl',list(b.values()))
    jsonl(output/'consensus_labels.jsonl',records)
    print('Prepared blank consensus with bound A/B records; no judgment inferred')

def publish_ui(output):
    output=output.resolve();review=(R/'review').resolve()
    if not output.is_relative_to(review) or output==review:
        raise ValueError('UI publication requires a new result directory inside research/review')
    manifest_path=output/'manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('source_package_manifest_sha256')!=sha(OUT/'manifest.json'):
        raise ValueError('Source review package mismatch')
    if manifest.get('files',{}).get('summary.json')!=sha(output/'summary.json'):
        raise ValueError('Summary hash mismatch')
    summary=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    if summary.get('source_run_id')!=RUN.name or summary.get('gold_manifest_sha256')!=sha(GOLD/'manifest.json'):
        raise ValueError('Result identity mismatch')
    pointer=review/'answer_semantic_latest.json'
    temp=review/'answer_semantic_latest.json.tmp'
    dump(temp,dict(result_relative_path=output.relative_to(R.resolve()).as_posix(),manifest_sha256=sha(manifest_path)))
    temp.replace(pointer)

def import_labels(source,output,markdown=False,publish=False):
    if output.exists():raise FileExistsError('New output directory required')
    manifest=validate_package()
    items=rows(OUT/'blinded_answers.jsonl');mapping=rows(OUT/'coordinator_only/method_mapping.jsonl')
    a=read_submitted(source,'AAA',markdown);b=read_submitted(source,'BBB',markdown);c=rows(source/'consensus_labels.jsonl')
    summary=summarize_labels(items,a,b,c,mapping)
    output.mkdir(parents=True)
    dump(output/'summary.json',summary)
    for name,rs in [('AAA_labels.jsonl',a),('BBB_labels.jsonl',b),('consensus_labels.jsonl',c)]:jsonl(output/name,rs)
    dump(output/'manifest.json',dict(source_package_manifest_sha256=sha(OUT/'manifest.json'),
        input_hashes={name:sha(source/name) for name in ((['AAA_144답변_독립채점_KR.md','BBB_144답변_독립채점_KR.md'] if markdown else ['AAA_labels.jsonl','BBB_labels.jsonl'])+['consensus_labels.jsonl'])},
        files={p.name:sha(p) for p in output.iterdir() if p.is_file()}))
    if publish:publish_ui(output)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--import-labels',type=Path);p.add_argument('--output',type=Path);p.add_argument('--prepare-consensus',type=Path);p.add_argument('--markdown',action='store_true');p.add_argument('--publish-ui',action='store_true');args=p.parse_args()
    if args.prepare_consensus:
        if not args.output:p.error('--output required')
        prepare_consensus(args.prepare_consensus,args.output,args.markdown)
    elif args.import_labels:
        if not args.output:p.error('--output required')
        import_labels(args.import_labels,args.output,args.markdown,args.publish_ui)
    else:prepare()
