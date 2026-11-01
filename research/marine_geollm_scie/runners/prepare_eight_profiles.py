"""Pin common source inputs for all eight methods; never copy answer object sets."""
import argparse
import hashlib
import json
from pathlib import Path
from shapely import wkb

from .binding_snapshot import ROOT, digest, verify_files
from .freeze_v2_benchmark import verify
from ..baselines.execution_dsl import ResearchDatabase


def prepare(snapshot_path, output, benchmark):
    output=Path(output).resolve();snapshot_path=Path(snapshot_path).resolve();benchmark=Path(benchmark).resolve()
    if output.exists():
        raise FileExistsError('New profile directory required')
    verify(benchmark,expected_manifest_sha256='feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c')
    snapshot=json.loads(snapshot_path.read_text(encoding='utf-8'));verify_files(snapshot,snapshot_path.parent)
    if snapshot.get('status')!='LOADED_VERIFIED':raise ValueError('Snapshot not verified')
    # User approved this reference input before comparison. Target answers are
    # absent from this query and from all generation profiles.
    boundary=json.loads((benchmark/'canonical_busan_boundary.json').read_text(encoding='utf-8'))
    rows=ResearchDatabase().query("SELECT feature_instance_id::text AS id,encode(ST_AsEWKB(geometry),'hex') AS ewkb FROM projection.s101_feature_current,input i WHERE feature_instance_id=(i.args->>'id')::bigint",{'id':boundary['id']})
    if len(rows)!=1 or rows[0]['ewkb']!=boundary['geometry_ewkb']:
        raise ValueError('Canonical reference differs from independently verified source')
    geometry=wkb.loads(bytes.fromhex(rows[0]['ewkb'])).wkt
    s101=next(r for r in snapshot['relations'] if r['relation']=='projection.s101_feature_current')
    refs={'canonical_busan_port_boundary':{'geometry_wkt':geometry,'crs':'EPSG:4326',
        'source_id':boundary['id'],'source_sha256':s101['sha256'],'name':'부산항 연구 기준 항계',
        'coverage_scope':'Single S-101 snapshot polygon, not verified full legal harbour boundary'}}
    old=ROOT/'research/marine_geollm_scie/runs/20261031_postfix_k5_v2'
    baseline=json.loads((old/'baseline_profile.json').read_text(encoding='utf-8'))
    model=json.loads((old/'model_profile.json').read_text(encoding='utf-8'))
    source_hashes={r['relation']:r['sha256'] for r in snapshot['relations']}
    coverage={
        's101':{'scope_verified':True,'bbox_epsg4326':[128.9,34.9,129.3,35.3],
            'source_sha256':s101['sha256'],'scope_type':'DECLARED_RESEARCH_SNAPSHOT',
            'real_world_completeness':False,'explanation':'Fixed Busan subset; outside cannot establish real-world absence.'},
        'navigation_aids':{'scope_verified':False,'source_sha256':source_hashes['serving.navigation_aid_current'],
            'real_world_completeness':False,'explanation':'Busan regional aids; nearest around Dokdo not covered.'},
        'marine_places':{'scope_verified':True,'scope_type':'FULL_DECLARED_SOURCE',
            'source_sha256':source_hashes['serving.marine_gazetteer_current'],'real_world_completeness':False,
            'explanation':'Entire frozen 2022 gazetteer corpus only; not all real-world places.'}}
    common={'contains_gold_answers':False,'snapshot_manifest':{'path':str(snapshot_path),'sha256':digest(snapshot_path)},
        'reference_geometries':refs,'coverage':coverage,
        'input_policy':'Same source registry supplied to every method; no per-case geometry substitution or answer injection.',
        'experiment_note':'Fresh GOLD v2 eight-method K1 after reliability changes; not old K5 reuse or equal-compute comparison.'}
    contract_path=ROOT/'research/marine_geollm_scie/protocol/eight_execution_contract_v3.json'
    contract=json.loads(contract_path.read_text(encoding='utf-8'))
    if not any(x['path']==contract_path.relative_to(ROOT).as_posix() and x['sha256']==digest(contract_path)
               for x in snapshot['files']):
        raise ValueError('Execution contract must be included in the new source freeze')
    common['execution_contract']={'path':contract_path.relative_to(ROOT).as_posix(),
                                  'sha256':digest(contract_path),'version':contract['version']}
    for profile in (baseline,model):profile.update(common)
    model['snapshot_manifest_sha256']=digest(snapshot_path)
    output.mkdir(parents=True,exist_ok=False)
    for name,profile in [('baseline_profile.json',baseline),('model_profile.json',model)]:
        (output/name).write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8')
    cases=[json.loads(x) for x in (benchmark/'queries.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    for case in cases:
        context=case.setdefault('spatial_context',{}) or {};case['spatial_context']=context
        context.update(reference_geometries=refs,source_coverage=coverage)
    with (output/'common_inputs.jsonl').open('x',encoding='utf-8') as stream:
        for case in cases:stream.write(json.dumps(case,ensure_ascii=False)+'\n')
    sources={r['path']:r['sha256'] for r in snapshot['files']}
    def mapping_hash(value):
        return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    baseline['benchmark_sha256']=digest(benchmark/'manifest.json')
    baseline['benchmark_inputs_path']=str(output/'common_inputs.jsonl')
    baseline['execution_source_hashes']=sources
    baseline['p1_profile_sha256']=digest(output/'model_profile.json')
    baseline['execution_identity']={
        'system_source_sha256':mapping_hash({k:v for k,v in sources.items() if k.startswith(('services/','shared/','data/'))}),
        'adapter_sha256':mapping_hash({k:v for k,v in sources.items() if k.startswith('research/')}),
        'model_profile_sha256':mapping_hash({'p1_profile':baseline['p1_profile_sha256'],
            'baseline_model':baseline['model'],'digest':baseline['model_digest'],
            'temperature':baseline['temperature'],'seed':baseline['seed'],
            'context_tokens':baseline['context_tokens'],'generation_budget':baseline['generation_budget_per_condition']}),
        'source_snapshot_sha256':digest(snapshot_path),
        'benchmark_inputs_sha256':digest(output/'common_inputs.jsonl'),
        'method_definitions_sha256':digest(benchmark/'comparison_protocol.json')}
    baseline['execution_identity']['execution_contract_sha256']=digest(contract_path)
    (output/'baseline_profile.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({'contains_gold_answers':False,
        'reference_is_input_not_spatial_gold':True,'files':{p.name:digest(p) for p in output.iterdir()},
        'benchmark_manifest_sha256':digest(benchmark/'manifest.json')},indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--snapshot',required=True);p.add_argument('--output',required=True);p.add_argument('--benchmark',required=True)
    a=p.parse_args();prepare(a.snapshot,a.output,a.benchmark)
