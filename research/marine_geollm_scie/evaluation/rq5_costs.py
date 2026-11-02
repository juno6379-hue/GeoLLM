"""Unique physical model calls and explicit standalone/allocated accounting."""
import hashlib,json,math

VERSION='rq5_cost_ledger.v1'

def numeric(value):
    return value if type(value) in (int,float) and math.isfinite(value) and value>=0 else None

def model_event(call):
    identity=call.get('event_id')
    raw={k:v for k,v in call.items() if k!='event_id'}
    return {'event_id':identity,'raw_call_sha256':hashlib.sha256(json.dumps(raw,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest(),
            'kind':call.get('kind','generation'),'input_tokens':numeric(call.get('input_tokens')),
            'output_tokens':numeric(call.get('output_tokens')),'latency_ms':numeric(call.get('latency_ms')),
            'status':call.get('status'),'tokens_scope':'PROVIDER_REPORTED_USAGE; missing usage remains null'}

def total(values):
    return sum(values) if all(numeric(v) is not None for v in values) else None

def event_ledger(rows):
    events={};consumers={};rowrefs={};missing=[];sql_events={};sql_missing=[]
    for row in rows:
        identity=(row['method'],row['case_id'],row.get('repeat',row.get('repeat_id',0)))
        key=json.dumps(identity,ensure_ascii=False)
        if key in rowrefs:raise ValueError('Duplicate RQ5 method/case/repeat')
        call_events=(row.get('costs') or {}).get('model_call_events')
        rowrefs[key]=[]
        sql=(row.get('costs') or {}).get('all_sql_events')
        if isinstance(sql,list):
            for index,event in enumerate(sql):sql_events[key+':sql:'+str(index)]=event
        else:sql_missing.append(key)
        if not isinstance(call_events,list):missing.append(key);continue
        if (row.get('costs') or {}).get('model_telemetry_complete') is False:missing.append(key)
        for event in call_events:
            eid=event.get('event_id')
            if not isinstance(eid,str) or not eid:raise ValueError('Missing physical model event identity')
            if eid in rowrefs[key]:raise ValueError('Same physical call counted twice within a method')
            if eid in events and events[eid]!=event:raise ValueError('Shared model event payload mismatch')
            events[eid]=event;consumers.setdefault(eid,[]).append(key);rowrefs[key].append(eid)
    standalone={};allocated={}
    for key,refs in rowrefs.items():
        standalone[key]={};allocated[key]={}
        for field in ('input_tokens','output_tokens','latency_ms'):
            standalone[key][field]=None if key in missing else total([events[e][field] for e in refs])
            allocated[key][field]=None if key in missing else total([events[e][field]/len(consumers[e]) if events[e][field] is not None else None for e in refs])
        standalone[key]['model_calls']=None if key in missing else len(refs)
        allocated[key]['model_calls']=None if key in missing else sum(1/len(consumers[e]) for e in refs)
    return {'version':VERSION,'events':events,'consumers':consumers,'row_event_refs':rowrefs,
            'missing_event_rows':missing,'unique_observed_model_calls':len(events),
            'sql_submission_events':sql_events,'observed_sql_submissions':len(sql_events),
            'total_sql_submissions':len(sql_events) if not sql_missing else None,'sql_missing_rows':sql_missing,
            'complete':not missing,'physical_total':{k:total([e[k] for e in events.values()]) if not missing else None for k in ('input_tokens','output_tokens','latency_ms')},
            'standalone_model_costs':standalone,'allocated_model_costs':allocated,
            'policy':'Standalone charges full shared generation/review to every consuming method; allocated divides each actual event equally among its consumers. Never sum standalone as physical run total. Allocated latency is work accounting, not user response latency.'}
