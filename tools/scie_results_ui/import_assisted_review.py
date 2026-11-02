"""Import user-confirmed AI-assisted judgments without claiming independent review."""
import argparse
from datetime import date
from pathlib import Path
import shutil
from tools.scie_results_ui.prepare_semantic_review import (OUT,R,RUN,GOLD,DIMENSIONS,sha,digest,rows,dump,validate_package,publish_ui)

FILES=('AAA_labels_HUMAN_FINAL.jsonl','BBB_labels_HUMAN_FINAL.jsonl','consensus_labels_HUMAN_FINAL.jsonl')

def validate(records,items,role):
    expected={i['answer_id']:i for i in items}; found={}
    author='HUMAN_VERIFIED_AI_ASSISTED_CONSENSUS' if role=='AAA_BBB_CONSENSUS' else 'HUMAN_VERIFIED_AI_ASSISTED_REVIEW'
    for x in records:
        aid=x.get('answer_id')
        if aid not in expected or aid in found:raise ValueError('Unknown or duplicate answer')
        for key in ('answer_sha256','display_sha256','gold_manifest_sha256'):
            if x.get(key)!=expected[aid][key]:raise ValueError('Answer/display/GOLD hash mismatch')
        if x.get('reviewer')!=role or x.get('author_type')!=author:raise ValueError('Assisted reviewer provenance mismatch')
        if x.get('human_completed') is not True or x.get('ai_assisted_origin') is not True or x.get('independent_review_confirmed') is not False:
            raise ValueError('Expected completed assisted, non-independent review')
        date.fromisoformat(x['reviewed_at'])
        for key in ('rationale','answer_evidence_quote','gold_evidence_locator','human_label_source','human_reviewer','human_review_attestation'):
            if not isinstance(x.get(key),str) or not x[key].strip():raise ValueError('Missing per-answer review provenance')
        if set(x.get('dimensions',{}))!=set(DIMENSIONS) or any(type(v) is not bool for v in x['dimensions'].values()):raise ValueError('Four boolean dimensions required')
        found[aid]=x
    if set(found)!=set(expected):raise ValueError('All original answer IDs required')
    return found

def aggregate(a,b,c,mapping):
    for aid,x in c.items():
        if x.get('AAA_dimensions')!=a[aid]['dimensions'] or x.get('BBB_dimensions')!=b[aid]['dimensions']:
            raise ValueError('Consensus references different submitted A/B dimensions')
    def stats(ids):
        n=len(ids); ds={k:sum(c[i]['dimensions'][k] for i in ids) for k in DIMENSIONS}
        full=sum(all(c[i]['dimensions'].values()) for i in ids)
        return dict(total=n,dimension_correct=ds,dimension_rates={k:v/n if n else None for k,v in ds.items()},joint_correct=full,joint_accuracy=full/n if n else None)
    ids=sorted(c);summary=stats(ids)
    summary['by_method']={m:stats([x['answer_id'] for x in mapping if x['method']==m]) for m in sorted({x['method'] for x in mapping})}
    summary['by_case']={cid:stats([x['answer_id'] for x in mapping if x['case_id']==cid]) for cid in sorted({x['case_id'] for x in mapping})}
    agreement={}
    for key in (*DIMENSIONS,'all_four'):
        pick=lambda x:all(x['dimensions'].values()) if key=='all_four' else x['dimensions'][key]
        n=len(ids);matches=sum(pick(a[i])==pick(b[i]) for i in ids);pa=sum(pick(a[i]) for i in ids)/n;pb=sum(pick(b[i]) for i in ids)/n;pe=pa*pb+(1-pa)*(1-pb)
        agreement[key]=dict(matches=matches,total=n,agreement=matches/n,cohen_kappa=(matches/n-pe)/(1-pe) if pe!=1 else None)
    summary['agreement']=agreement
    return summary

def run(source,output,publish=False):
    validate_package()
    if output.exists():raise FileExistsError('New output required')
    items=rows(OUT/'blinded_answers.jsonl');mapping=rows(OUT/'coordinator_only/method_mapping.jsonl')
    a,b,c=[validate(rows(source/name),items,role) for name,role in zip(FILES,('AAA','BBB','AAA_BBB_CONSENSUS'))]
    metrics=aggregate(a,b,c,mapping)
    summary=dict(status='HUMAN_CONFIRMED_AI_ASSISTED_COMPLETE',source_run_id=RUN.name,gold_manifest_sha256=sha(GOLD/'manifest.json'),
        total_answers=len(items),reviewer_A_completed=len(a),reviewer_B_completed=len(b),paired_completed=len(a.keys()&b.keys()),consensus_completed=len(c),
        human_answer_scoring_complete=False,independent_review_confirmed=False,semantic_human_accuracy=None,
        assisted_review_complete=True,assisted_metrics=metrics,preparation_complete=True,gold_review_complete=True,gold_review_basis='USER_ATTESTATION',
        limitations=['AI 보조 판정을 사용자가 검토 확인한 기록입니다. 별도 두 인간 검수자의 독립성은 확인되지 않았습니다.',
        '의미 정확성 단일 항목과 네 항목 공동 충족률을 구분합니다.',
        'A/B 일치도는 제출된 보조 판정 간 일치도이며 독립 인간 검수자 간 신뢰도로 해석하지 않습니다.',
        '개발용 18문항의 K1 결과이며 독립 홀드아웃 성능이 아닙니다.'])
    output.mkdir(parents=True)
    for name in FILES:shutil.copyfile(source/name,output/name)
    dump(output/'summary.json',summary)
    dump(output/'label_bindings.json',{'binding_created_at_import':True,'records':[dict(answer_id=i,AAA_sha256=digest(a[i]),BBB_sha256=digest(b[i]),consensus_sha256=digest(c[i])) for i in sorted(c)]})
    text=['# 사람이 확인한 AI 보조 답변 채점 결과','',
          'AAA/BBB/합의 각144건. 제출된 원문은 변경하지 않고 답안·표시답안·GOLD hash와 합의 A/B 판정을 검증했다.',
          'independent_review_confirmed=false를 보존한다. 독립 인간 의미 정확도가 아닌 사용자 확인 AI 보조 채점 결과다.','',
          '| 차원 | 충족/전체 | 비율 |','|---|---:|---:|']
    for k,v in metrics['dimension_correct'].items():text.append(f'| {k} | {v}/144 | {v/144:.2%} |')
    text += [f"| 네 항목 모두 충족 | {metrics['joint_correct']}/144 | {metrics['joint_accuracy']:.2%} |",'',
             '| 방법 | 의미 정확성 | 네 항목 공동 충족 |','|---|---:|---:|']
    for m,v in metrics['by_method'].items():text.append(f"| {m} | {v['dimension_correct']['meaning_correct']}/{v['total']} | {v['joint_correct']}/{v['total']} |")
    text+=['','A/B dimension별 일치도·Cohen kappa와 사례별 결과는 summary.json에 보존한다. 이는 AI 보조 판정 비교이며 독립 인간 간 신뢰도 추정이 아니다.',
           '다음: 개발 사례의 오류·원천 범위/정상 오차단 보완 → 최종 시스템 동결 → 신규 홀드아웃 GOLD 검수와 실행 harness 검증 → 별도 평가. 현재 제출은 새 홀드아웃 승인이나 평가 실행을 의미하지 않는다.']
    (output/'결과_KR.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    dump(output/'manifest.json',dict(source_package_manifest_sha256=sha(OUT/'manifest.json'),
        source_files={str(source/name):sha(source/name) for name in FILES},scorer_sha256=sha(Path(__file__)),
        files={p.name:sha(p) for p in output.iterdir() if p.is_file()}))
    if publish:publish_ui(output)
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--publish-ui',action='store_true');args=p.parse_args()
    s=run(args.source,args.output,args.publish_ui);print(s['assisted_metrics'])
