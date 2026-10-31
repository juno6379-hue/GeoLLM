"""Explicit baseline response renderer, not a post-hoc GOLD normalizer.

Only observed tool receipts / validator blockers are projected. Candidate prose
is retained separately and is never rewritten into a source quotation.
"""
import math


def render(plan, execution, *, coverage, validated_qecs=()):
    result={'answer_text':plan.get('answer','') if isinstance(plan,dict) else '',
            'rendering':'DETERMINISTIC_RECEIPT_PROJECTION_V2','spatial_tasks':{},
            'tool_receipts':execution.get('receipts',[]),'candidate_prose_is_unverified':True,
            'projection_errors':[]}
    calls=plan.get('tool_calls',[]) if isinstance(plan,dict) else []
    receipts=execution.get('receipts',[])
    documents=[]
    for index,(call,receipt) in enumerate(zip(calls,receipts)):
        if not isinstance(call,dict) or not isinstance(receipt,dict):
            result['projection_errors'].append({'call_index':index,'reason':'INVALID_CALL_OR_RECEIPT_TYPE'})
            continue
        if call.get('tool_id')=='catalogue.search' and receipt.get('status')=='TOOL_RETURNED':
            doc=receipt.get('result',{}).get('document_answer')
            if doc:documents.append(doc)
        if call.get('tool_id')!='spatial.query':continue
        args=call.get('arguments')
        if not isinstance(args,dict):
            result['projection_errors'].append({'call_index':index,'reason':'INVALID_ARGUMENTS_TYPE'})
            continue
        source=args.get('source')
        targets=args.get('feature_types',args.get('target_features'))
        invalid=[]
        if not isinstance(source,str):invalid.append('source')
        if not isinstance(targets,list) or any(not isinstance(x,str) for x in targets):invalid.append('feature_types')
        if invalid:
            # Preserve the original plan/receipt; never select an item from a
            # list, stringify an object, or fabricate a target for bad input.
            result['projection_errors'].append({'call_index':index,'reason':'INVALID_SPATIAL_ARGUMENT_TYPES','fields':invalid})
            continue
        scope=coverage.get(source,{})
        payload=receipt.get('result',{})
        rows=payload.get('rows',[]) if isinstance(payload,dict) else None
        if receipt.get('status')=='TOOL_RETURNED' and (not isinstance(rows,list) or any(
                not isinstance(r,dict) or not isinstance(r.get('source_id'),(str,int)) or isinstance(r.get('source_id'),bool)
                or (r.get('distance_m') is not None and (type(r['distance_m']) not in (int,float) or not math.isfinite(r['distance_m'])))
                for r in rows)):
            result['projection_errors'].append({'call_index':index,'reason':'INVALID_SPATIAL_RECEIPT_ROWS'})
            continue
        for target in targets:
            if receipt.get('status')=='TOOL_RETURNED':
                selected=[r for r in rows if source!='s101' or r.get('label')==target]
                ids=[str(r['source_id']) for r in selected]
                result['spatial_tasks'][target]={'status':'SUCCESS' if ids else 'SUCCESS_EMPTY',
                    'object_ids':ids,'count':len(ids),'source_snapshot_sha256':scope.get('source_sha256'),
                    'object_evidence':{str(r['source_id']):{'object_id':str(r['source_id']),
                        'source_snapshot_sha256':scope.get('source_sha256'),'geometry':r.get('geometry'),
                        'attributes':r.get('attributes'),'distance_m':r.get('distance_m')} for r in selected},
                    'query_evidence':{'source':source,'arguments':args,'postcondition':payload.get('postcondition')}}
            else:
                reason=receipt.get('reason') or receipt.get('error_type')
                result['spatial_tasks'][target]={'status':'DATA_OUT_OF_SCOPE' if reason=='DATA_OUT_OF_SCOPE' else 'BLOCKED_DATA',
                    'object_ids':None,'count':None,'reason':reason}
        if receipt.get('status')=='TOOL_RETURNED' or receipt.get('reason')=='DATA_OUT_OF_SCOPE':
            result['source_coverage']={'source_snapshot_sha256':scope.get('source_sha256'),
                'requested_extent_covered':receipt.get('status')=='TOOL_RETURNED',
                'explanation':scope.get('explanation') or 'Declared frozen research source scope only; real-world completeness not established.',
                'scope':scope}
    if documents:
        result['document_answers']=documents
        if len(documents)==1:result['document_answer']=documents[0]
    blockers=[b for q in validated_qecs for b in q.get('blockers',[])]
    if blockers:
        result['validator_blockers']=blockers
        result['status']=next((q['readiness'] for q in validated_qecs if q.get('blockers')), 'BLOCKED_CONFIG')
        if any('geometry' in b.casefold() for b in blockers):
            result.update(blocker='MISSING_REFERENCE_GEOMETRY',clarification_request='Provide the required reference geometry.')
    elif isinstance(plan,dict) and plan.get('action')=='clarify':
        result.update(status='NEEDS_USER_INPUT',clarification_request=plan.get('answer'))
        if 'MISSING_REFERENCE_GEOMETRY' in plan.get('missing_inputs',[]):result['blocker']='MISSING_REFERENCE_GEOMETRY'
    else:
        result['status']='COMPLETED' if receipts and all(isinstance(r,dict) and r.get('status')=='TOOL_RETURNED' for r in receipts) else 'PARTIAL'
    if result['projection_errors']:
        result['status']='PARTIAL'
        result['error_code']='ANSWER_PROJECTION_INPUT_INVALID'
    # Counts/distances are explicit receipt aggregation, not model interpretation.
    if len(result['spatial_tasks'])>1 and all(t.get('object_ids') is not None for t in result['spatial_tasks'].values()):
        tasks=result['spatial_tasks']
        result['comparison']={'counts':{k:v['count'] for k,v in tasks.items()},'distance_ranges_m':{},
                              'feature_definition_evidence':{}}
        for target,task in tasks.items():
            values=[e['distance_m'] for e in task['object_evidence'].values() if e.get('distance_m') is not None]
            result['comparison']['distance_ranges_m'][target]={'minimum':min(values) if values else None,'maximum':max(values) if values else None}
            for doc in documents:
                if any(f.get('code')==target for f in doc.get('features',[])):
                    result['comparison']['feature_definition_evidence'][target]=doc.get('evidence')
    return result
