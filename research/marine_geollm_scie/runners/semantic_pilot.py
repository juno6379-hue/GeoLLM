"""Offline production linguistic-evidence component pilot; NOT full P or gold accuracy."""
from __future__ import annotations
import argparse, collections, datetime, hashlib, importlib.metadata, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(os.environ.get('GEOLLM_RESEARCH_SOURCE_ROOT', str(Path(__file__).resolve().parents[3])))
sys.path.insert(0,str(ROOT))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=Path,default=ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl')
    parser.add_argument('--output',type=Path,default=ROOT/'research/marine_geollm_scie/runs/20261029_pilot/semantic')
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--environment',choices=['host','isolated_container_network_none'],default='host')
    args=parser.parse_args()
    if args.repeats<1: parser.error('repeats must be positive')
    args.output.mkdir(parents=True,exist_ok=True)
    if any((args.output/name).exists() for name in ('raw.jsonl','semantic_rows.jsonl','manifest.json')):
        raise FileExistsError('Existing experiment artifacts; choose a new run directory')
    cases=[json.loads(x) for x in args.cases.read_text(encoding='utf-8').splitlines() if x.strip()]
    source_paths=['services/orchestrator/korean_query_analysis.py','services/orchestrator/marine_s101_mapping.py','services/orchestrator/marine_terminology.py','services/orchestrator/slot_evidence.py','data/marine_s101_bindings.json','data/mof_terminology_relations.json','data/s101_feature_catalogue_v2_parsed.json']
    packages={}
    for package in ['pydantic','PyYAML','kiwipiepy','kiwipiepy_model']:
        try: packages[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: packages[package]=None
    manifest={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'experiment':'production_linguistic_evidence_component','not_full_proposed':True,'repeats':args.repeats,'unique_cases':len(cases),'statistical_units':'case/equivalence_cluster; deterministic repeats not independent','model_backend':None,'ollama_used':False,'database_used':False,'benchmark_sha256':digest(args.cases),'source_hashes':{p:digest(ROOT/p) for p in source_paths},'python_version':platform.python_version(),'package_versions':packages,'kiwi_enabled_environment':os.getenv('GEOLLM_KIWI_ENABLED','true'),'git_commit_sha':os.getenv('GEOLLM_RESEARCH_GIT_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'gold_count':0}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    rows=[]
    for repeat in range(1,args.repeats+1):
        for case in cases:
            row={'case_id':case['case_id'],'query':case['query'],'category':case['category'],'equivalence_group':case['equivalence_group'],'method':'PRODUCTION_LINGUISTIC_COMPONENT','repeat':repeat,'annotation_status':case['annotation_status'],'execution_success':None,'semantic_correct':None,'plan_valid':None,'spatial_correct':None,'evidence_correct':None,'input_tokens':None,'output_tokens':None}
            start=time.perf_counter()
            try:
                from services.orchestrator.korean_query_analysis import analyze_query
                from services.orchestrator.marine_s101_mapping import resolve_mappings
                analysis=analyze_query(case['query'])
                mappings=resolve_mappings(case['query'],analysis['constraints'])
                row.update(status='COMPONENT_RETURNED',analysis=analysis,source_mappings=mappings)
                stable={**analysis};stable.pop('latency_ms',None)
                row['deterministic_output_sha256']=hashlib.sha256(json.dumps({'analysis':stable,'mappings':mappings},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            except Exception as exc:
                row.update(status='COMPONENT_ERROR',error_type=type(exc).__name__)
            row['latency_ms']=round((time.perf_counter()-start)*1000,3)
            rows.append(row)
            with (args.output/'raw.jsonl').open('a' if len(rows)>1 else 'w',encoding='utf-8') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
    grouped=collections.defaultdict(list)
    for row in rows: grouped[row['case_id']].append(row)
    summary={'rows':len(rows),'unique_cases':len(cases),'status_counts':dict(collections.Counter(x['status'] for x in rows)),'analyzer_status_counts':dict(collections.Counter(x.get('analysis',{}).get('analyzer',{}).get('status','NOT_REACHED') for x in rows)),'cases_with_repeat_disagreement':[k for k,v in grouped.items() if len({x.get('deterministic_output_sha256') for x in v})>1],'rows_with_source_mappings':sum(bool(x.get('source_mappings')) for x in rows),'gold_count':0,'accuracy':None,'limitation':'Offline linguistic evidence/source-backed lexical subset only; no routing, QEC, validator, GIS, Qwen or final answers. Zero matches do not mean no S-101 grounding exists elsewhere.'}
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (args.output/'semantic_rows.jsonl').open('x',encoding='utf-8') as stream:
        for row in rows:
            normalized={**row,'review_status':'DRAFT','full_qec':None,'final_result':None,
                        'scope':'COMPONENT_ONLY','cohort':'COMPONENT','environment':args.environment}
            stream.write(json.dumps(normalized,ensure_ascii=False)+'\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__': main()
