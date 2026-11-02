"""Derived approved-GOLD scoring; original runs and conditional metrics stay immutable."""
import hashlib
import json
from pathlib import Path
from collections import Counter
from research.marine_geollm_scie.runners.report_eight import verify_raw
from research.marine_geollm_scie.runners.freeze_v2_benchmark import verify
from research.marine_geollm_scie.evaluation.v2_results import score_row

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'research/marine_geollm_scie'
G=R/'benchmark/gold_v2_immutable_20261101_v1'
RUN=R/'runs/20261102_gold_v2_eight_k1_v6'
OUT=R/'review/20261102_approved_gold_rescore_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readrows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def delivery_score(s):
    """Task delivery is distinct from geometric accuracy of returned objects."""
    old=s['all_applicable_checks_pass']
    if old is not None:return old,'EXISTING_CONTRACT_VERDICT'
    obs=s['observation']
    if obs['trace'].get('observation_complete') is not True:return None,'INCOMPLETE_OBSERVATION'
    if not obs['output_available']:return False,'TERMINAL_NO_USABLE_ANSWER'
    if s['checks']=={'spatial_objects':None}:
        return False,'REQUIRED_SOURCE_BOUND_OBJECT_SET_NOT_DELIVERED'
    return None,'UNRESOLVED_CHECK'

def main():
    if OUT.exists():raise FileExistsError('Preserve prior rescore; choose a new version')
    before={str(p.relative_to(ROOT)):sha(p) for folder in (G,RUN) for p in folder.rglob('*') if p.is_file()}
    verify(G)
    contracts={c['case_id']:c for c in readrows(G/'answer_contracts.jsonl')}
    rows=readrows(RUN/'comparison/observations.jsonl')
    assert len(rows)==144 and len({(x['case_id'],x['method'],x['repeat']) for x in rows})==144
    assert Counter(x['method'] for x in rows)==dict.fromkeys(['B0','B1','B2','B3','B4','P0','H','P1'],18)
    for x in rows:verify_raw((RUN/'comparison').resolve(),x)
    scores=[]
    for x in rows:
        s=score_row(x,contracts[x['case_id']]);value,reason=delivery_score(s)
        s.update(approved_gold_task_delivery=value,rescore_reason=reason,raw_artifact_path=x['raw_artifact_path'],raw_artifact_sha256=x['raw_artifact_sha256'])
        scores.append(s)
    approval=dict(status='USER_CONFIRMED_COMPLETE',independent_human_review_complete=True,
        reviewers=['AAA','BBB'],agreement_date='2026-11-02',approval_date='2026-11-02',timezone='Asia/Seoul',
        confirmation_source='USER_MESSAGE',confirmation_text='독립 인간 검수도 완료하였다; 합의일과 승인 기록은 오늘 날짜로 해라',
        gold_manifest_sha256=sha(G/'manifest.json'),case_ids=sorted(contracts),signatures=None,
        scope='Existing GOLD v2 accepted without answer-contract changes; completion attested by user; signatures not synthesized')
    def group(ss):
        known=[s for s in ss if s['approved_gold_task_delivery'] is not None]
        return dict(total=len(ss),measured=len(known),passed=sum(s['approved_gold_task_delivery'] is True for s in known),
            failed=sum(s['approved_gold_task_delivery'] is False for s in known),missing=len(ss)-len(known),
            value=sum(s['approved_gold_task_delivery'] is True for s in known)/len(ss) if len(known)==len(ss) else None,
            newly_resolved=sum(s['all_applicable_checks_pass'] is None and s['approved_gold_task_delivery'] is not None for s in ss))
    summary=dict(status='RESCORED',run_id=RUN.name,approval=approval,rows=len(scores),
        metric='APPROVED_GOLD_TASK_DELIVERY_NOT_HUMAN_SEMANTIC_ACCURACY',
        by_method={m:group([s for s in scores if s['method']==m]) for m in sorted({s['method'] for s in scores})},
        by_condition={m+'|'+c:group([s for s in scores if s['method']==m and s['query_condition']==c]) for m in sorted({s['method'] for s in scores}) for c in sorted({s['query_condition'] for s in scores})},
        overall=group(scores),human_answer_scoring_complete=False,semantic_human_accuracy=None,
        remaining=['Returned-object spatial accuracy remains unmeasured where no source-bound objects were returned.',
                   'Success-conditional metrics are not applicable with zero successful executions.',
                   'Human GOLD review completion does not mean humans scored the 144 model answers.',
                   'K1 and no independent holdout; AI-assisted review materials disclosed.'],originals_preserved=True)
    OUT.mkdir(parents=True)
    dump(OUT/'approval.json',approval);dump(OUT/'summary.json',summary)
    (OUT/'scores.jsonl').write_text(''.join(json.dumps(s,ensure_ascii=False)+'\n' for s in scores),encoding='utf-8')
    lines=['# 승인 GOLD v2 — 기존 144답변 재채점','',
        '검수자 AAA·BBB / 합의일·승인일 2026-11-02 (사용자 완료 확인). 서명은 생성하지 않았다.',
        '기존 GOLD·실험 원본 불변. 모델 재호출 없이 동일 기계계약을 다시 검사했다.',
        '새 지표는 **승인 GOLD 과업 충족률**이다. 완료된 응답에서 필수 원천 객체집합을 제공하지 못한 경우와 최종 답안 부재를 실패로 포함한다. 기존 SCR·기계계약 지표를 소급 수정하지 않는다. 인간 의미 정확도가 아니다.','',
        '| 방법 | 충족 | 실패 | 측정/전체 | 새로 판정 |','|---|---:|---:|---:|---:|']
    for m,v in summary['by_method'].items():lines.append(f"| {m} | {v['passed']} | {v['failed']} | {v['measured']}/{v['total']} | {v['newly_resolved']} |")
    lines+=['','공간 결과 미제공은 과업 실패이지만 잘못된 좌표를 반환한 것으로 해석하지 않는다. 반환 객체의 조건부 공간 정확도, 성공 분모 0의 오류율, 인간 답변 채점은 별도 상태로 남긴다.',
        '사례별 checks·정규화 답변·원문 경로/hash·판정 이유: scores.jsonl. 조건별 집계: summary.json.']
    (OUT/'재채점_결과_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    assert all(sha(ROOT/p)==h for p,h in before.items())
    dump(OUT/'preserved_hashes.json',before)
    dump(OUT/'manifest.json',dict(files={p.name:sha(p) for p in OUT.iterdir() if p.is_file()},scorer_sha256=sha(Path(__file__)),original_files_verified=len(before)))
    print(json.dumps(summary['overall']))
if __name__=='__main__':main()
