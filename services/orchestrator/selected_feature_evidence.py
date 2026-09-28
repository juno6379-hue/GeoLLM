"""Read selected S-101 instances from their declared serving source."""
import hashlib
import json
import os
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from services.orchestrator.request_obligations import audit_outputs, required_outputs
from services.orchestrator.s101_portrayal import resolve_s101_portrayal
from services.orchestrator.route_planner import RoutePlanner
from services.orchestrator.execution_validator import validate_execution_context, project_execution_decision
from services.orchestrator.evidence_builder import build_evidence_bundle
from shared.schemas.agent import ExecutionSlots, QueryExecutionContext, PlanStatus

SOURCE = 'projection.s101_feature_valid'


def fetch_feature(feature_id):
    with psycopg2.connect(os.environ['S101_DB_URL'], connect_timeout=5) as connection:
        connection.set_session(readonly=True)
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SET LOCAL statement_timeout='5s'")
            cursor.execute('SELECT feature_instance_id, feature_type_name, attributes, '
                           'ST_AsGeoJSON(geometry)::jsonb AS geometry, '
                           'GeometryType(geometry) AS geometry_type '
                           'FROM projection.s101_feature_valid WHERE feature_instance_id=%s LIMIT 2',
                           (feature_id,))
            return [dict(row) for row in cursor.fetchall()]


def execute(state):
    context = state.get('spatial_context') or {}
    if hasattr(context, 'model_dump'):
        context = context.model_dump()
    selected = context.get('selected_feature') or {}
    selected = selected if isinstance(selected, dict) else {}
    props = selected.get('properties') or {}
    props = props if isinstance(props, dict) else {}
    identifier = selected.get('id', props.get('feature_id'))
    source = selected.get('source_ref') or props.get('source_ref')
    qec = {'execution_status': 'NOT_RUN', 'tool_bindings': [], 'data_bindings': []}
    final = {'task_id': state['task_id'], 'status': 'NEEDS_CLARIFICATION',
             'structured_result': {}, 'map_layers': [],
             'orchestrator_v2': {'query_execution_context': qec}}

    def problem(status, code, message):
        final.update(status=status, error_code=code, answer_text=message, summary=message)
        if status == 'NEEDS_CLARIFICATION':
            final['clarification_questions'] = [message]

    if state.get('user_id') == 'blocked_user':
        problem('BLOCKED', 'ACCESS_DENIED', '이 요청에 대한 접근 권한이 없습니다.')
    elif source != SOURCE:
        problem('NEEDS_CLARIFICATION', 'SELECTED_FEATURE_SOURCE_REQUIRED',
                '선택 객체의 원천을 확인해주세요. 현재 S-101 serving 원천의 객체 ID를 조회할 수 있습니다.')
    elif isinstance(identifier, bool) or not str(identifier).isascii() or not str(identifier).isdigit() or not 0 < int(identifier) < 2**63:
        problem('NEEDS_CLARIFICATION', 'INVALID_SELECTED_FEATURE_ID', '유효한 S-101 객체 ID를 선택해주세요.')
    else:
        try:
            slots = ExecutionSlots(analysis_type='selected_feature_lookup', feature_instance_id=int(identifier),
                                   feature_instance_ref={'id': int(identifier), 'source_ref': source})
            plan = RoutePlanner().generate_plan(state['query'], slots.model_dump(), None,
                                               'selected_map_feature', 'selected_feature_lookup', 'SPATIAL_ANALYSIS')
            typed_context = QueryExecutionContext(request_id=state['task_id'], task_id=state['task_id'],
                original_query=state['query'], slots=slots, route_plan=plan,
                context={'resolution_source': 'request.spatial_context.selected_feature', 'selected_feature_id': int(identifier)},
                semantic_resolution={'required_outputs': required_outputs(state['query'])})
            typed_context.plan_hash = hashlib.sha256(json.dumps({'plan': plan, 'slots': slots.model_dump()},
                                                               sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            typed_context = validate_execution_context(typed_context)
            plan = typed_context.route_plan
            project_execution_decision(typed_context, plan)
            qec.update(typed_context.model_dump(mode='json'))
            final['orchestrator_v2']['route_plan'] = plan
            if typed_context.readiness != PlanStatus.EXECUTION_READY:
                problem('BLOCKED', 'SELECTED_FEATURE_EXECUTION_BLOCKED', '선택 객체 실행 계약을 검증하지 못했습니다.')
                return {'final_dict': final, 'status': final['status'], 'task_plan': plan,
                        'query_execution_context': qec, 'selected_feature_handled': True}
            rows = fetch_feature(int(identifier))
            qec['execution_status'] = 'EXECUTED'
            execution_id = str(uuid.uuid4())
            qec['provenance']['execution'] = {'query_execution_id': execution_id, 'tool_id': 'postgis.selected_feature_lookup'}
            if len(rows) != 1:
                problem('BLOCKED', 'SELECTED_FEATURE_NOT_FOUND' if not rows else 'SELECTED_FEATURE_AMBIGUOUS',
                        '선택 객체를 원천에서 유일하게 확인하지 못했습니다. 객체를 다시 선택해주세요.')
            else:
                row = rows[0]
                digest = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                evidence = {'source_ref': SOURCE, 'feature_id': row['feature_instance_id'],
                            'feature_type': row['feature_type_name'], 'attributes': row['attributes'],
                            'geometry': row['geometry'], 'row_sha256': digest,
                            'query_execution_id': execution_id,
                            'client_properties_used_as_evidence': False}
                candidate = resolve_s101_portrayal(row['feature_type_name'],
                    (row['geometry'] or {}).get('type'), row['attributes'])
                candidate.update(status='CANDIDATE_NOT_VERIFIED', official_rule_executed=False,
                                 implementation_ref='services/orchestrator/s101_portrayal.py',
                                 implementation_sha256=hashlib.sha256(Path(__file__).with_name('s101_portrayal.py').read_bytes()).hexdigest())
                final['structured_result'].update(selected_feature_evidence=evidence, portrayal_candidate=candidate)
                final['evidence_bundle'] = build_evidence_bundle(task_id=state['task_id'], spatial_feature_evidence=[
                    {'evidence_id': evidence['query_execution_id'], 'evidence_type': 'selected_feature',
                     'source_ref': SOURCE, 'data': evidence}]).model_dump(mode='json')
                message = f"선택 객체 {row['feature_instance_id']}의 원천 유형은 {row['feature_type_name']}입니다. DB 속성과 geometry를 확인했습니다."
                final.update(status='COMPLETED', answer_text=message, summary=message)
        except (psycopg2.Error, KeyError):
            qec['execution_status'] = 'FAILED'
            problem('BLOCKED', 'SELECTED_FEATURE_SOURCE_UNAVAILABLE', '선택 객체의 원천 조회에 실패했습니다.')
    final = audit_outputs(state.get('query', ''), final)
    return {'final_dict': final, 'status': final['status'], 'query_execution_context': qec,
            'task_plan': final['orchestrator_v2'].get('route_plan'),
            'selected_feature_handled': True}
