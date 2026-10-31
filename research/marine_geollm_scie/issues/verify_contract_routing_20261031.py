"""Audit preserved API observations against execution boundaries and actual FC."""
import argparse
import hashlib
import json
from pathlib import Path
from shared.schemas.agent import QueryExecutionContext
from services.orchestrator.execution_validator import is_execution_authorized
from .reproduce_radius_api_rq_v2 import ROOT


def verify(folder):
    folder = Path(folder)
    rows = [json.loads(x) for x in (folder/'api_rows.jsonl').read_text(encoding='utf-8').splitlines()]
    catalogue_path = ROOT/'data/s101_feature_catalogue_v2_parsed.json'
    catalogue = json.loads(catalogue_path.read_text(encoding='utf-8'))
    features = {x['code']: x for x in catalogue['features']}
    checks = []
    for row in rows:
        case = row['case_id']
        task = row.get('final') or {}
        final = task.get('final_result') or {}
        structured = final.get('structured_result') or {}
        qec = (final.get('orchestrator_v2') or {}).get('query_execution_context')
        qec_valid = True
        try:
            authorized = is_execution_authorized(QueryExecutionContext.model_validate(qec)) if qec else False
        except ValueError:
            qec_valid, authorized = False, False
        result = {'case_id': case, 'captured': row['status']=='CAPTURED', 'status': task.get('status'),
                  'error_code': final.get('error_code'), 'authorized': authorized, 'qec_schema_valid': qec_valid, 'latency_ms': row['latency_ms']}
        if case in {'anchorage_ko','anchorage_en','wreck_attributes'}:
            expected = 'Wreck' if case=='wreck_attributes' else 'AnchorageArea'
            doc = structured.get('document_answer') or {}
            found = next((x for x in doc.get('features',[]) if x['code']==expected), {})
            evidence = doc.get('evidence') or {}
            result['pass'] = (task.get('status')=='COMPLETED' and authorized
                and found.get('definition')==features[expected]['definition']
                and set(found.get('permitted_primitives',[]))==set(features[expected]['permitted_primitives'])
                and evidence.get('source_sha256')==hashlib.sha256((ROOT/catalogue['metadata']['source']).read_bytes()).hexdigest()
                and structured.get('search_execution',{}).get('status')=='NOT_RUN')
        elif case=='missing_aoi':
            result['pass'] = task.get('status')=='NEEDS_CLARIFICATION' and final.get('error_code')=='AOI_REQUIRED' and not authorized
        elif case=='explicit_aoi':
            result['pass'] = task.get('status')=='BLOCKED' and final.get('error_code')=='INTERSECTION_EXECUTION_NOT_SUPPORTED' and not authorized
        elif case=='composite_targets':
            result['pass'] = task.get('status')=='PARTIAL' and 'all_requested_feature_groups' in structured.get('unmet_outputs',[])
        elif case=='private_coordinates':
            result['pass'] = task.get('status')=='BLOCKED' and final.get('error_code')=='BLOCKED_POLICY' and not authorized
        elif case=='public_codes':
            result['pass'] = task.get('status')=='COMPLETED' and authorized and len(structured.get('listed_values',[]))==29
        elif case in {'mixed_attribute_coordinates','mixed_attribute_map'}:
            result['pass'] = task.get('status') in {'NEEDS_CLARIFICATION','PARTIAL','BLOCKED'} and bool(final)
        else:
            # Raw snippets or no documents cannot complete an explanation.
            # These currently unresolved requests must expose incompleteness.
            result['pass'] = bool(final) and task.get('status') in {'PARTIAL','BLOCKED','NEEDS_CLARIFICATION'}
            result['semantic_correctness'] = None
        result['pass'] = result['captured'] and qec_valid and result['pass']
        checks.append(result)
    artifact={'scope':'Execution boundary and source consistency, not semantic GOLD',
        'source_raw_sha256':hashlib.sha256((folder/'api_rows.jsonl').read_bytes()).hexdigest(),
        'passed':sum(x['pass'] for x in checks), 'total':len(checks), 'checks':checks}
    (folder/'verified_contracts.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(artifact,ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',required=True);verify(p.parse_args().folder)
