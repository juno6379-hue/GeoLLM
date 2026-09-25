"""Link grounded query evidence to existing dictionary/KG/capability contracts.

No new ontology classes, facts, coordinates or executable tools are invented.
Indexes are immutable for a process lifetime and refreshed on service restart.
"""
from __future__ import annotations

import re
import hashlib
import json
import time
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _indexes():
    from services.orchestrator.graph_rag_retriever import _load_graph
    from services.orchestrator.kg_ontology_validator import _status
    from services.orchestrator.marine_lexicon import load_terms
    terms, term_sources = load_terms()
    contract = yaml.safe_load((ROOT/'data/kg_ontology_contract.yaml').read_text(encoding='utf-8'))
    nodes, edges = _load_graph()
    by_name, outgoing = defaultdict(list), defaultdict(list)
    for identifier, node in nodes.items():
        if node.get('node_type') not in {'Feature', 'MarineTerm', 'DerivedConcept', 'SemanticMapping', 'UpperClass'}:
            continue
        props = node.get('properties') or {}
        for name in {node.get('name'), props.get('canonical_name')} - {None}:
            by_name[str(name).casefold()].append(identifier)
    for edge in edges:
        schema = contract.get('edge_types', {}).get(edge.get('predicate'))
        subject, obj = nodes.get(edge.get('subject_id'), {}), nodes.get(edge.get('object_id'), {})
        valid = bool(schema and subject.get('node_type') in schema.get('subject_types', [])
                     and obj.get('node_type') in schema.get('object_types', []))
        if not valid:
            continue
        outgoing[edge['subject_id']].append({
            'edge_id': edge.get('id'), 'subject_id': edge['subject_id'], 'predicate': edge['predicate'],
            'object_id': edge['object_id'], 'ontology_types_valid': True,
            'verification_status': _status(edge, schema), 'provenance': edge.get('provenance'),
            'authority_for_execution': False})
    patterns = []
    for label, entry in terms.items():
        for alias in [label, *entry.get('aliases', [])]:
            if not isinstance(alias, str) or not alias:
                continue
            # Korean particles may follow a noun; English aliases require a word boundary.
            suffix = r'(?![A-Za-z0-9_])' if alias.isascii() else ''
            patterns.append((re.compile(r'(?<![가-힣A-Za-z0-9_])'+re.escape(alias)+suffix, re.I), label, entry))
    # Hash the loaded objects, not files that may have changed after _load_graph cached them.
    versions = {name: hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                for name, value in {'terms': term_sources, 'ontology': contract, 'kg_nodes': nodes, 'kg_edges': edges}.items()}
    return patterns, by_name, outgoing, contract.get('contract_id'), versions


def bind_semantic_slots(query: str, analysis: dict, capabilities: list[dict]) -> dict:
    started = time.monotonic()
    patterns, by_name, outgoing, contract_id, versions = _indexes()
    from services.orchestrator.marine_terminology import match_terminology
    terminology = analysis.get('maritime_terminology')
    if terminology is None:
        terminology = match_terminology(query, analysis.get('constraints', []))
    terms, seeds, paths, features = [], set(), {}, set()
    for pattern, label, entry in patterns:
        for match in pattern.finditer(query):
            excluded = any(c['kind'] == 'exclusion' and c['scope_status'] == 'EXPLICIT_LOCAL_SCOPE'
                           and c['span'][0] <= match.start() < c['span'][1] for c in analysis.get('constraints', []))
            canonical = entry.get('canonical_id')
            terms.append({'raw_text': match[0], 'span': list(match.span()), 'canonical_id': canonical,
                          'excluded': excluded, 'registry_ref': entry['registry_ref'],
                          'feature_candidates':entry.get('maps_to_features',[]),
                          'attribute_filters':entry.get('attribute_filters',{}),
                          'attribute_filter_execution_status':'RUNTIME_VALIDATION_REQUIRED' if entry.get('attribute_filters') else 'NOT_APPLICABLE'})
            if excluded:
                continue
            values = [canonical, *entry.get('maps_to_concepts', []), *entry.get('maps_to_features', [])]
            features.update(entry.get('maps_to_features', []))
            for value in values:
                seeds.update(by_name.get(str(value).casefold(), []))
    for seed in sorted(seeds):
        for edge in outgoing.get(seed, []):
            paths[edge['edge_id']] = edge
    grounded = [s for s in analysis.get('slots', []) if s['validation_status'] == 'GROUNDED']
    distances = [s for s in grounded if s.get('quantity_role') == 'radius']
    supplied = {'query_text': {'source': 'query'}}
    if any(not term['excluded'] for term in terms):
        supplied['feature_term'] = {'source': 'registry_alias', 'terms': [t for t in terms if not t['excluded']]}
    if features:
        supplied['target_feature_group'] = {'source': 'marine_term_dictionary', 'features': sorted(features), 'runtime_validation_required': True}
    if len(distances) == 1:
        supplied['radius_m'] = {'source': 'query_span', 'evidence': distances[0]}
    bindings = []
    for candidate in capabilities:
        required = candidate.get('input_slots') or []
        bindings.append({'candidate_id': candidate['candidate_id'],
                         'bound_inputs': {k: supplied[k] for k in required if k in supplied},
                         'unresolved_inputs': [k for k in required if k not in supplied],
                         'declared_outputs': candidate.get('output_slots') or [],
                         'status': 'INPUTS_GROUNDED' if required and all(k in supplied for k in required) else 'RUNTIME_BINDING_REQUIRED',
                         'execution_authorized': False})
    return {'contract': 'semantic_slot_binding.v1', 'ontology_contract': contract_id, 'source_sha256': versions,
            'term_bindings': terms, 'kg_seed_ids': sorted(seeds), 'kg_relations': list(paths.values()),
            'capability_bindings': bindings, 'target_features': sorted(features),
            'maritime_terminology': terminology,
            'unresolved_terminology': [
                {'span':t['span'], 'raw_text':t['raw_text'], 'reason':'ONTOLOGY_MAPPING_NOT_VERIFIED',
                 'candidate_tool_contracts':[c['candidate_id'] for c in capabilities
                     if set(c.get('input_slots') or []) & {'feature_term','target_feature_group'}],
                 'execution_authorized':False}
                for t in terminology['candidates'] if not t['excluded'] and not t['quoted']],
            'limitations': ['KG relations propose evidence; provenance and runtime geometry/data gates remain required',
                            'Duration is not an absolute temporal_window; location text is not anchor_geometry'],
            'latency_ms': round((time.monotonic()-started)*1000, 3)}
