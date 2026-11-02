import hashlib,json
from tools.scie_results_ui.rq3_development import BASE,load_rq3_development


def fixture(root):
 p=root/BASE;p.mkdir(parents=True)
 row=dict(case_id='development',variant='wrong_centroid',execution_success=True,spatial_correct=False,returned_count=1,gold_count=2,object_ids=['id1'],missing_ids=['id2'],extra_ids=[])
 (p/'summary.json').write_text(json.dumps(dict(evidence_verified=True,production_authority_granted=False,scope='DEVELOPMENT_SQL_MUTATION_NOT_METHOD_BENCHMARK',sql_trace={k:True for k in ('execution_attempted','execution_started','tool_called','sql_executed')},spatial_cases=[row])),encoding='utf-8')
 (p/'sql.txt').write_text('synthetic test only',encoding='utf-8')
 manifest=dict(files={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['summary.json','sql.txt']})
 (p/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
 return p,manifest


def test_verified_wrong_execution_is_separate_from_benchmark(tmp_path):
 fixture(tmp_path);r=load_rq3_development(tmp_path)
 assert r['status']=='VERIFIED_DEVELOPMENT_DIAGNOSTIC'
 assert r['included_in_selected_run'] is False
 assert r['spatial_cases'][0]['execution_success'] is True
 assert r['spatial_cases'][0]['spatial_correct'] is False


def test_missing_or_changed_evidence_is_not_zero_or_success(tmp_path):
 assert load_rq3_development(tmp_path)['status']=='NOT_MEASURED'
 p,_=fixture(tmp_path);(p/'sql.txt').write_text('changed',encoding='utf-8')
 r=load_rq3_development(tmp_path)
 assert r['status']=='INVALID_OR_UNMEASURED' and r['spatial_cases']==[]


def test_holdout_or_traversal_never_read(tmp_path):
 p,m=fixture(tmp_path);m['files']['../holdout/secret']='0'*64
 (p/'manifest.json').write_text(json.dumps(m),encoding='utf-8')
 assert load_rq3_development(tmp_path)['errors']==['INVALID_ARTIFACT_PATH']


def test_invalid_verdict_or_execution_never_becomes_published_diagnostic(tmp_path):
 p,m=fixture(tmp_path)
 original=json.loads((p/'summary.json').read_text(encoding='utf-8'))
 import copy
 for mutation in ('verdict','count','trace','scope'):
  summary=copy.deepcopy(original)
  if mutation=='verdict':summary['spatial_cases'][0]['spatial_correct']=True
  if mutation=='count':summary['spatial_cases'][0]['returned_count']=2
  if mutation=='trace':summary['sql_trace']['sql_executed']=False
  if mutation=='scope':summary['production_authority_granted']=True
  (p/'summary.json').write_text(json.dumps(summary),encoding='utf-8')
  m['files']['summary.json']=hashlib.sha256((p/'summary.json').read_bytes()).hexdigest()
  (p/'manifest.json').write_text(json.dumps(m),encoding='utf-8')
  assert load_rq3_development(tmp_path)['status']=='INVALID_OR_UNMEASURED'
