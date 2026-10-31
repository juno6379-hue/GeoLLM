"""Post-run component contract audit. Gold contracts never enter generation."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re
from pathlib import Path


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def comparison_condition(folder, cohort):
    folder = Path(folder)
    filenames = ('model_graph_manifest.json', 'adapter_manifest.json') if cohort == 'P_PRODUCTION_GRAPH' else ('manifest.json',)
    path = next((folder/name for name in filenames if (folder/name).is_file()), folder/filenames[0])
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    profile = data.get('model_profile') or {}
    profile_path = folder.parent/'baseline_profile.json'
    profile_verified = False
    if cohort == 'BASELINE_EXECUTION_ADAPTER' and profile_path.is_file() and sha(profile_path) == data.get('profile_sha256'):
        profile = json.loads(profile_path.read_text(encoding='utf-8')); profile_verified = True
    snapshot = data.get('snapshot_manifest') or profile.get('snapshot_manifest') or {}
    expected = data.get('snapshot_manifest_sha256') or snapshot.get('sha256')
    snapshot_path = Path(snapshot['path']) if snapshot.get('path') else None
    if snapshot_path is not None and not snapshot_path.is_absolute():
        snapshot_path = Path(__file__).resolve().parents[3]/snapshot_path
    observed = sha(snapshot_path) if snapshot_path is not None and snapshot_path.is_file() else None
    return {'cohort': cohort, 'manifest_path': str(path), 'manifest_sha256': sha(path) if path.exists() else None,
        'method': data.get('method'), 'scope': data.get('scope'),
        'snapshot_manifest_sha256': expected, 'snapshot_manifest_path': str(snapshot_path) if snapshot_path else None,
        'snapshot_observed_sha256': observed, 'snapshot_artifact_verified': bool(expected and observed == expected),
        'profile_sha256': data.get('profile_sha256'), 'baseline_profile_file_verified': profile_verified,
        'model_metadata': data.get('model_metadata'), 'budget': data.get('budget'), 'model_profile': profile,
        'semantic_prior_timeout_seconds': profile.get('semantic_prior_timeout_seconds', data.get('semantic_prior_timeout_seconds')),
        'experiment_note': profile.get('experiment_note', data.get('experiment_note')),
        'source_hashes_digest': hashlib.sha256(json.dumps(data.get('source_hashes', {}),sort_keys=True).encode()).hexdigest() if data.get('source_hashes') else None,
        'limitations': data.get('limitations', data.get('differences_from_model_baselines'))}


def normalized_baseline(row):
    receipts = (row.get('tool_execution') or {}).get('receipts', [])
    output = {'document_answer': {'features': [], 'attribute_bindings': []}, 'per_tool_status': [],
        'search_executed': False, 'execution_status': 'NOT_EXECUTED', 'source_coverage': {'unverified_conditions': []}}
    evidences = []; spatial_rows = []; spatial_sources = set()
    for receipt in receipts:
        output['per_tool_status'].append({'tool_id': receipt.get('tool_id'), 'status': receipt.get('status')})
        result = receipt.get('result') or {}
        doc = result.get('document_answer')
        if doc:
            output['document_answer']['features'] += doc.get('features', [])
            output['document_answer']['attribute_bindings'] += doc.get('attribute_bindings', [])
            if doc.get('evidence'): evidences.append(doc['evidence'])
            if doc.get('definition_quote'): output['document_answer']['definition_quote'] = doc['definition_quote']
        if receipt.get('tool_id') == 'spatial.query':
            if receipt.get('status') == 'TOOL_RETURNED':
                output['search_executed'] = True; spatial_rows += result.get('rows', [])
                spatial_sources.add(result.get('source'))
            else:
                output['source_coverage']['unverified_conditions'].append(receipt.get('reason', receipt.get('error_type')))
    if evidences and len({(e.get('edition'), e.get('source_sha256')) for e in evidences}) == 1:
        evidence = dict(evidences[0])
        evidence['locators'] = sorted({v for e in evidences for v in e.get('locators', [])})
        evidence['claim_source_links'] = [v for e in evidences for v in e.get('claim_source_links', [])]
        output['document_answer']['evidence'] = evidence
    for field, key in (('features', 'code'), ('attribute_bindings', None)):
        unique = {}
        for value in output['document_answer'][field]:
            unique[value.get(key) if key else (value.get('owner'), value.get('attribute'))] = value
        output['document_answer'][field] = list(unique.values())
    if output['search_executed']:
        output['execution_status'] = 'SEARCH_EXECUTED'
        if spatial_sources == {'marine_places'} and spatial_rows:
            ids = [(r.get('properties') or {}).get('공간정보일련번호') for r in spatial_rows]
            source_hashes = {(r.get('provenance') or {}).get('source_sha256') for r in spatial_rows}
            if all(v is not None for v in ids) and len(source_hashes) == 1 and None not in source_hashes:
                output['returned_object_ids'] = ['mof_marine_names_20221231:'+str(v) for v in ids]
                output['dataset_snapshot_sha256'] = next(iter(source_hashes))
    plan = row.get('plan') or {}
    if plan.get('action') == 'clarify' and not output['search_executed'] and plan.get('missing_inputs'):
        output['execution_status'] = 'NEEDS_USER_INPUT'; output['clarification_request'] = plan['missing_inputs']
    return output


def normalized_production(row):
    """Map emitted fields without reading GOLD, source files or retrieved text.

    Missing structured document fields are machine-contract omissions, not a
    judgement that the free prose is semantically incorrect. Unrecorded spatial
    execution remains unknown rather than inventing a no-execution observation.
    """
    final = (row.get('final_state') or {}).get('final_dict')
    if not isinstance(final, dict) or not final:
        return None
    structured = final.get('structured_result') or {}
    if not isinstance(structured, dict): structured = {}
    doc = structured.get('document_answer')
    output = {'document_answer': dict(doc) if isinstance(doc, dict) else {'features': [], 'attribute_bindings': []},
        'search_executed': None, 'execution_status': final.get('status'),
        'source_coverage': structured.get('source_coverage') or {},
        'per_task_status': structured.get('per_task_status') or {},
        'mapping_provenance': {'version': 'emitted_output_v1', 'root': 'final_state.final_dict',
            'retrieved_text_used_as_answer': False, 'reference_used_for_mapping': False,
            'structured_document_answer_present': isinstance(doc, dict)}}
    output['document_answer'].setdefault('features', [])
    output['document_answer'].setdefault('attribute_bindings', [])
    if doc is None and structured.get('analysis_type') == 'public_catalogue_attribute_lookup':
        code = structured.get('feature_code'); attribute = structured.get('attribute_code')
        if code:
            output['document_answer']['features'] = [{'code': code, 'definition': structured.get('feature_definition')}]
        binding = structured.get('binding')
        if code and attribute and isinstance(binding, dict):
            output['document_answer']['attribute_bindings'] = [{
                'owner': code, 'attribute': attribute, 'lower': binding.get('lower'),
                'upper': binding.get('upper'), 'unbounded': binding.get('unbounded'),
                'permitted_values': structured.get('permitted_values'),
                'attribute_definition': structured.get('definition'),
                'global_listed_values': structured.get('listed_values')}]
        # Parsed-JSON locators are not XML claim links; do not fabricate them.
    search = structured.get('search_execution') or {}
    if search.get('status') in {'COMPLETED', 'SEARCH_EXECUTED'}:
        output['search_executed'] = True
        output['execution_status'] = 'SEARCH_EXECUTED'
    elif search.get('status') in {'NOT_RUN', 'NOT_EXECUTED'}:
        output['search_executed'] = False
    if final.get('status') in {'NEEDS_CLARIFICATION', 'NEEDS_USER_INPUT'}:
        output['execution_status'] = 'NEEDS_USER_INPUT'
        output['clarification_request'] = final.get('clarification_questions') or []
    if output['search_executed'] is True:
        features = structured.get('features')
        if not isinstance(features, list):
            features = (structured.get('geojson') or {}).get('features', [])
        properties = [f.get('properties', f) for f in features if isinstance(f, dict)]
        ids = [f.get('공간정보일련번호') for f in properties]
        hashes = {(f.get('provenance') or {}).get('source_sha256') for f in properties}
        layers = {f.get('layer_id') for f in properties}
        if properties and all(v is not None for v in ids) and layers == {'marine_gazetteer_mof'} and len(hashes) == 1 and None not in hashes:
            output['returned_object_ids'] = ['mof_marine_names_20221231:'+str(v) for v in ids]
            output['dataset_snapshot_sha256'] = next(iter(hashes))
        elif not properties and structured.get('source') == 'marine_places' and structured.get('dataset_snapshot_sha256'):
            # An empty executed result still needs an explicit source identity.
            output['returned_object_ids'] = []
            output['dataset_snapshot_sha256'] = structured['dataset_snapshot_sha256']
    return output


def get(output, field):
    value = output
    for key in field.split('.'):
        if not isinstance(value, dict): return None
        value = value.get(key)
    return value


def check_contract(output, check):
    kind = check['kind']; expected = check.get('expected'); value = get(output, check['field'])
    features = (output.get('document_answer') or {}).get('features', [])
    if kind == 'set_inclusion': return set(expected) <= {f.get('code') for f in features}
    if kind == 'per_feature_set_equality':
        observed = {f.get('code'): f.get('permitted_primitives') for f in features}
        return all(code in observed and set(observed[code] or []) == set(values) for code, values in expected.items())
    if kind == 'nonempty_per_feature':
        observed = {f.get('code'): f.get('definition') for f in features}
        return all(isinstance(observed.get(c), str) and bool(observed[c].strip()) for c in check['expected_codes'])
    if kind == 'exact_value':
        if check['field'] == 'search_executed' and value is None: return None
        return value == expected
    if kind == 'edition_hash_locator_match':
        if not isinstance(value, dict): return False
        return (value.get('edition') == expected['edition'] and value.get('source_sha256') == expected['source_sha256']
            and set(expected['locators']) <= set(value.get('locators', []))
            and all(any(link.get('definition_locator') in {loc, loc+"/*[local-name()='definition']"} and link.get('source_sha256') == expected['source_sha256']
                for link in value.get('claim_source_links', [])) for loc in expected['locators']))
    if kind == 'exact_structured_bindings':
        if not isinstance(value, list): return False
        # Required owner/attribute bindings must match every frozen field. Extra
        # independently returned source attributes are retained but not required.
        index = {(v.get('owner'), v.get('attribute')): v for v in value}
        return all(all(index.get((e['owner'], e['attribute']), {}).get(k) == v for k, v in e.items()) for e in expected)
    if kind == 'source_bound_set_equality':
        if output.get('search_executed') is not True: return None
        if output.get('dataset_snapshot_sha256') != check['dataset_snapshot_sha256'] or not isinstance(value, list): return None
        return set(value) == set(expected)
    if kind == 'required_structured_disclosure':
        # A benchmark-oracle assertion is an evaluation-side concept, not a
        # required production API field. Do not synthesize it from a failure.
        if not isinstance(value, dict) or 'benchmark_oracle_available' not in value: return None
        return isinstance(value, dict) and value.get('benchmark_oracle_available') is False and bool(value.get('unverified_conditions'))
    if kind == 'per_obligation_status':
        return isinstance(value, dict) and all(key in value and value[key] in {'COMPLETED','BLOCKED','NOT_EXECUTED','PARTIAL','NEEDS_USER_INPUT'} for key in check['expected_obligations'])
    return None


def score(row, contract, cohort):
    # Both adapters consume recorded outputs without reference-driven rewriting.
    output = normalized_baseline(row) if cohort == 'BASELINE_EXECUTION_ADAPTER' else normalized_production(row)
    if output is None:
        return {'case_id': row['case_id'], 'cohort': cohort, 'method': row.get('method'), 'repeat': row.get('repeat', 0),
            'status': 'OUTPUT_MAPPING_NOT_AVAILABLE', 'checks': [], 'all_applicable_checks_pass': None}
    checks = [{'id': c['id'], 'kind': c['kind'], 'pass': check_contract(output, c)} for c in contract['machine_checks']]
    for item in checks:
        if item['pass'] is None:
            item['unmeasured_reason'] = {
                'source_bound_set_equality': 'Spatial execution, returned IDs or matching source snapshot not verified',
                'required_structured_disclosure': 'Benchmark oracle assertion absent; runtime coverage is not an oracle claim',
                'exact_value': 'Explicit spatial execution observation unavailable',
            }.get(item['kind'], 'Unsupported machine check')
    measured = [c['pass'] for c in checks if c['pass'] is not None]
    return {'case_id': row['case_id'], 'cohort': cohort, 'method': row.get('method'), 'repeat': row.get('repeat', 0),
        'status': 'COMPONENT_CHECKS_ONLY', 'mapping_version': 'emitted_output_v1', 'checks': checks, 'measured_checks': len(measured),
        'passed_checks': sum(measured), 'null_checks': len(checks)-len(measured),
        'all_applicable_checks_pass': all(measured) if measured and len(measured) == len(checks) else None,
        'full_semantic_accuracy': None, 'independent_human_gold': False, 'normalized_observation': output}


def common_output_observations(row, contract, cohort):
    """Only emitted answers, not retrieved source bodies or reference prose."""
    if cohort == 'BASELINE_EXECUTION_ADAPTER':
        observed = normalized_baseline(row)
        doc = observed['document_answer']
        text = '\n'.join(str(f.get('code', ''))+'\n'+str(f.get('definition', '')) for f in doc['features'])
        citations = (doc.get('evidence') or {}).get('locators', [])
        role = 'EXECUTED_TOOL_STRUCTURED_ANSWER_NOT_INITIAL_MODEL_CANDIDATE'
    else:
        final = (row.get('final_state') or {}).get('final_dict') or {}
        text = '\n'.join(str(final.get(key) or '') for key in ('answer_text', 'summary'))
        text += '\n'+'\n'.join(str(c.get('text') or '') for c in final.get('claims', []) if isinstance(c, dict))
        citations = (final.get('structured_result') or {}).get('citations', [])
        role = 'PRODUCTION_EMITTED_ANSWER_EXCLUDING_RETRIEVED_SNIPPETS'
    scope = contract.get('document_scope') or {}
    expected_features = scope.get('features', [])
    literal = {f['code']: f.get('definition') in text if f.get('definition') else None for f in expected_features}
    codes = {f['code']: bool(re.search(r'(?<![A-Za-z0-9_])'+re.escape(f['code'])+r'(?![A-Za-z0-9_])', text)) for f in expected_features}
    return {'case_id': row['case_id'], 'cohort': cohort, 'method': row.get('method'), 'repeat': row.get('repeat', 0),
        'output_role': role, 'output_text_present': bool(text.strip()), 'definition_verbatim_in_emitted_answer': literal or None,
        'feature_code_literal_in_emitted_answer': codes or None, 'returned_citation_count': len(citations),
        'citation_claim_support': None, 'semantic_accuracy': None,
        'note': 'Literal output observations only. Paraphrases may be correct; citation presence is not source support.'}


def run(baselines, graph, contracts, output):
    baselines, graph, contracts, output = map(Path, (baselines, graph, contracts, output))
    if output.exists(): raise FileExistsError('New report directory required')
    references = {r['case_id']: r for r in load(contracts)}
    if len(references) != 18 or any(r.get('finalization_status') != 'AGENT_FINALIZED_UNDER_USER_DIRECTION' for r in references.values()):
        raise ValueError('Exactly 18 fixed v5 agent-finalized contracts required; do not relabel as human GOLD')
    sources = [(baselines/'execution_rows.jsonl', 'BASELINE_EXECUTION_ADAPTER'), (graph/'production_rows.jsonl', 'P_PRODUCTION_GRAPH')]
    scores = []; observations = []; provenance = []; common = []
    for path, cohort in sources:
        if not path.exists():
            provenance.append({'path': str(path), 'status': 'NOT_AVAILABLE'}); continue
        rows = load(path); provenance.append({'path': str(path), 'sha256': sha(path), 'rows': len(rows), 'cohort': cohort})
        for row in rows:
            if row['case_id'] not in references: raise ValueError('Unknown case outside fixed contracts')
            scores.append(score(row, references[row['case_id']], cohort))
            common.append(common_output_observations(row, references[row['case_id']], cohort))
            observations.append({'case_id': row['case_id'], 'method': row.get('method'), 'cohort': cohort,
                'repeat': row.get('repeat', 0), 'model_status': row.get('status'), 'graph_status': row.get('graph_status'),
                'tool_status': (row.get('tool_execution') or {}).get('status'),
                'latency_ms': row.get('total_latency_ms', row.get('latency_ms')),
                'input_tokens': (row.get('model_costs') or {}).get('input_tokens'),
                'output_tokens': (row.get('model_costs') or {}).get('output_tokens')})
    output.mkdir(parents=True)
    for name, records in [('component_scores', scores), ('observations', observations), ('common_output_observations', common)]:
        (output/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    groups = defaultdict(list)
    for row in scores: groups[(row['cohort'],row['method'])].append(row)
    summary = [{'cohort': key[0], 'method': key[1], 'rows': len(rows), 'unique_cases': len({r['case_id'] for r in rows}),
        'complete_check_rows': sum(r.get('all_applicable_checks_pass') is True for r in rows),
        'incomplete_check_rows': sum(r.get('all_applicable_checks_pass') is False for r in rows),
        'unmeasured_rows': sum(r.get('all_applicable_checks_pass') is None for r in rows)} for key,rows in groups.items()]
    if summary:
        with (output/'summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    manifest = {'scope': 'AGENT_FINALIZED_V5_COMPONENT_CONTRACT_AUDIT_NOT_FULL_SEMANTIC_ACCURACY',
        'evaluator_sha256': sha(__file__), 'mapping_version': 'emitted_output_v1',
        'contract_sha256': sha(contracts), 'sources': provenance, 'independent_human_gold': False, 'holdout': False,
        'old_planning_pilot_included': False, 'all_requested_cases_observed': len({r['case_id'] for r in scores}) == 18,
        'summary': summary}
    conditions = [comparison_condition(baselines, 'BASELINE_EXECUTION_ADAPTER'), comparison_condition(graph, 'P_PRODUCTION_GRAPH')]
    manifest['comparison_conditions'] = conditions
    manifest['same_snapshot_reference_verified'] = bool(conditions[0]['snapshot_manifest_sha256']) and conditions[0]['snapshot_manifest_sha256'] == conditions[1]['snapshot_manifest_sha256']
    manifest['same_snapshot_artifact_verified'] = manifest['same_snapshot_reference_verified'] and any(c['snapshot_artifact_verified'] for c in conditions) and all(c['snapshot_observed_sha256'] in (None,c['snapshot_manifest_sha256']) for c in conditions)
    manifest['policy_timeout_cost_conditions_equal'] = False
    manifest['equal_compute_budget'] = False
    manifest['common_full_task_accuracy_comparison_ready'] = False
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    lines = ['# 실제 실행 비교의 구성요소 검사', '', '사용자 지시 아래 에이전트가 확정한 v5 계약이며 독립 인간 GOLD 또는 전체 의미 정확도가 아닙니다.',
        '기존 planning90은 포함하지 않았습니다. P와 baseline의 호출예산·문서검색·답변생성 방식이 다르며 동일 모델을 동일 계산조건으로 표현하지 않습니다.',
        '기존 baseline 실행90행과 새 graph를 재비교할 때 정책·timeout·코드·비용 조건이 달라질 수 있습니다. 조건 manifest와 실제 snapshot 파일 해시를 별도로 기록하며, 같은 snapshot을 timeout 단독 효과나 동일 실행조건의 증거로 해석하지 않습니다.',
        'P와 baseline의 실제 반환 필드를 같은 기계 계약으로 검사합니다. 필수 구조 필드 누락은 계약 실패이며 서술 의미의 오답 판정이 아닙니다. 공간 실행·원천 해시가 확인되지 않으면 해당 공간 검사는 미측정입니다.', '',
        '| 실행군 | 방법 | 행 | 사례 | 검사전체통과 | 검사실패 | 미측정 포함 |', '| --- | --- | --- | --- | --- | --- | --- |']
    lines += [f'| {s["cohort"]} | {s["method"]} | {s["rows"]} | {s["unique_cases"]} | {s["complete_check_rows"]} | {s["incomplete_check_rows"]} | {s["unmeasured_rows"]} |' for s in summary]
    lines += ['', '미실행 공간검색을 0건 정답으로 처리하지 않습니다. P는 final_dict의 실제 document_answer·공간결과·상태를 매핑하며 documents/excerpt/detail_text 또는 GOLD로 답안을 재작성하지 않습니다. 최종 출력 자체가 없으면 미측정입니다.',
        'common_output_observations.jsonl은 양쪽의 실제 출력 답안에서 FC 원문 문장·feature code의 문자 출현과 반환 인용 개수만 대조합니다. P의 검색된 excerpt/detail_text는 답안으로 사용하지 않습니다. 의미가 같은 바꿔쓰기는 이 문자 검사에 불일치할 수 있으므로 정답률로 해석하지 않습니다.',
        '속성 검사는 요구된 owner/attribute 필드의 일치를 대조하며 추가 원천 속성은 금지하지 않습니다. 원문 존재·locator 일치만으로 서술의 의미 정확도를 주장하지 않습니다.']
    (output/'comparison_KR.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return manifest


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--baselines',required=True);p.add_argument('--graph',required=True)
    p.add_argument('--contracts',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args();run(a.baselines,a.graph,a.contracts,a.output_dir)
