"""Real source-backed point -> API -> attribute-filtered PostGIS regression and shadow baseline."""
import argparse
import json
import os
import time
import urllib.request
from pathlib import Path
import psycopg2
from scripts.check_geollm_web_samples import observe


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    if a.output.exists(): raise ValueError('Use a new run path')
    for _ in range(120):
        try:
            if urllib.request.urlopen('http://localhost:8000/health',timeout=2).status==200: break
        except OSError: pass
        time.sleep(1)
    else: raise RuntimeError('API not ready')
    with psycopg2.connect(os.environ['S101_DB_URL']) as c:
        with c.cursor() as cur:
            cur.execute('SELECT feature_instance_id, ST_AsText(ST_PointOnSurface(geometry)) FROM projection.s101_feature_valid WHERE feature_type_name=%s AND attributes @> %s::jsonb ORDER BY feature_instance_id LIMIT 1',
                ('ShorelineConstruction',json.dumps({'categoryOfShorelineConstruction':'1','waterLevelEffect':'3'})))
            anchor=cur.fetchone()
    if not anchor: raise RuntimeError('No real submerged breakwater anchor; do not fabricate fixture')
    context={'geometry':anchor[1],'crs':'EPSG:4326','base_location':'실제 S-101 객체에서 선택한 평가 기준점'}
    cases=[(201,'반경 1km 이내 잠제를 찾아줘'),(202,'반경 1km 이내 수중방파제를 찾아줘'),
           (203,'반경 1km 이내 물양장을 찾아줘'),(204,'반경 1km 이내 예선을 찾아줘'),
           (205,'반경 1km 이내 선유장을 찾아줘'),(206,'잠제 말고 침선을 찾아줘'),
           (207,'반경 1km 이내 잠제와 침선을 찾아줘'),(208,'잠제를 찾아줘'),
           (209,'반경 1km 이내 잠제를 찾아줘'),(210,'반경 1km 이내 잠제를 찾아줘')]
    a.output.parent.mkdir(parents=True,exist_ok=True); passed=0
    for identifier,query in cases:
        case_context=dict(context)
        if identifier==209: case_context['exclusions']=['ShorelineConstruction']
        if identifier==210: case_context['target_features']=['ShorelineConstruction','Wreck']
        row=observe('http://localhost:8000',identifier,query,case_context)
        final=(row.get('completion') or {}).get('final_result') or {}
        structured=final.get('structured_result') or {}
        if identifier in (201,202):
            features=structured.get('features') or []
            ok=final.get('status')=='COMPLETED' and structured.get('total_count',0)>=1 and bool(structured.get('query_execution_id'))
            ok=ok and all(str(f['attributes'].get('categoryOfShorelineConstruction'))=='1' and str(f['attributes'].get('waterLevelEffect'))=='3' for f in features)
            qec=(final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
            execution=(qec.get('provenance') or {}).get('execution') or {}
            ok=ok and qec.get('readiness')=='EXECUTION_READY' and qec.get('execution_status')=='EXECUTED'
            ok=ok and bool(qec.get('plan_hash')) and execution.get('query_execution_id')==structured.get('query_execution_id')
            ok=ok and (qec.get('slots') or {}).get('filters',{}).get('attribute_filters')==structured.get('mapping',{}).get('filters')
            evidence=(final.get('evidence_bundle') or {}).get('spatial_feature_evidence') or []
            ok=ok and len(evidence)==len(features) and all(e.get('data',{}).get('query_execution_id')==execution.get('query_execution_id') for e in evidence)
        else:
            code={203:'TERM_MAPPING_UNRESOLVED',204:'TERM_MAPPING_UNRESOLVED',205:'TERM_MAPPING_UNRESOLVED',
                  206:'NEGATION_EXECUTION_NOT_SUPPORTED',207:'COMPOUND_MAPPING_REQUIRED',208:'RADIUS_REQUIRED',
                  209:'NEGATION_EXECUTION_NOT_SUPPORTED',210:'COMPOUND_MAPPING_REQUIRED'}[identifier]
            ok=final.get('error_code')==code and final.get('orchestrator_v2',{}).get('query_execution_context',{}).get('execution_status')=='NOT_RUN'
        row.update(contract_check_passed=bool(ok),evaluation_anchor={'source':'projection.s101_feature_valid','feature_id':anchor[0]})
        with a.output.open('a',encoding='utf-8') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
        passed+=bool(ok); print(json.dumps({'sample':identifier,'passed':bool(ok),'status':final.get('status'),'code':final.get('error_code'),'seconds':row['elapsed_seconds']}),flush=True)
    print(f'{passed}/{len(cases)} real API contracts')
    return passed!=len(cases)


if __name__=='__main__': raise SystemExit(main())
