"""Research-only deterministic retrieval. No routing, LLM, database or gold labels."""
from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
FC = 'data/s101_feature_catalogue_v2_parsed.json'
NODES = 'outputs/graph/kg_nodes_v2.jsonl'
EDGES = 'outputs/graph/kg_edges_v2.jsonl'
REGISTRIES = ('data/marine_term_dictionary.yaml', 'data/s101_feature_dictionary.yaml')


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=16)
def _read_cached(path: str, size: int, modified: int):
    raw = Path(path).read_bytes()
    return raw.decode('utf-8'), _sha(raw)


def _read(path: str):
    file = ROOT / path
    stat = file.stat()
    return _read_cached(str(file), stat.st_size, stat.st_mtime_ns)


@lru_cache(maxsize=8)
def _json_document(text: str):
    return json.loads(text)


@lru_cache(maxsize=8)
def _yaml_document(text: str):
    return yaml.safe_load(text)


@lru_cache(maxsize=4)
def _json_rows(text: str):
    return tuple(json.loads(line) for line in text.splitlines() if line.strip())


@lru_cache(maxsize=2)
def _edge_rows(text: str):
    return tuple((number, json.loads(line)) for number, line in enumerate(text.splitlines(), 1) if line.strip())


def _contains(query: str, label: str) -> bool:
    label = label.casefold().strip()
    if len(label) < 2:
        return False
    if label not in query:
        return False
    if re.fullmatch(r'[a-z0-9 _-]+', label):
        return bool(re.search(r'(?<![a-z0-9])' + re.escape(label) + r's?(?![a-z0-9])', query))
    return label in query


def _terms(query: str):
    """Registry aliases retrieve candidates only; ambiguity is never resolved here."""
    terms, trace, errors = set(), [], []
    for path in REGISTRIES:
        try:
            text, digest = _read(path)
            doc = _yaml_document(text)
            rows = doc.get('terms', doc.get('s101_features', {}))
            for label, row in rows.items():
                matched = [term for term in [label, *row.get('aliases', [])] if _contains(query, term)]
                if not matched:
                    continue
                targets = row.get('maps_to_features', row.get('feature_candidates', []))
                terms.update(str(x).casefold() for x in targets)
                trace.append({'path': path, 'sha256': digest, 'label': label,
                              'matched': matched, 'candidate_features': targets,
                              'verification_status': row.get('verification_status'),
                              'role': 'retrieval_only_not_semantic_gold'})
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append({'path': path, 'error_type': type(exc).__name__})
    return terms, trace, errors


def build_packet(query: str, method: str, max_chars: int = 6000) -> dict:
    """Return source-preserving B0/B1/B2 evidence with explicit missingness.

    Character budget is a ceiling, not a token-equivalence claim. Whole records
    are admitted; records are never sliced into misleading partial JSON.
    """
    if method not in {'B0', 'B1', 'B2'}:
        raise ValueError('Packet retrieval supports B0, B1 and B2 only')
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars < 0:
        raise ValueError('max_chars must be a nonnegative integer')
    packet = {'method': method, 'query': query, 'sources': [], 'evidence': '',
              'retrieval_trace': [], 'errors': [], 'max_chars': max_chars,
              'status': 'NO_EVIDENCE_BY_DESIGN' if method == 'B0' else 'EVIDENCE_UNAVAILABLE',
              'matched_records': 0, 'omitted_records': 0, 'execution_authorized': False}
    candidates = []
    if method != 'B0':
        folded = query.casefold()
        terms, trace, errors = _terms(folded)
        packet.update(retrieval_trace=trace, errors=errors)
        try:
            if method == 'B1':
                text, digest = _read(FC)
                catalogue = _json_document(text)
                # Preserve FC text and binding rows; do not inject KG relationships.
                features = [f for f in catalogue['features'] if f['code'].casefold() in terms
                            or any(_contains(folded, str(f.get(k, ''))) for k in ('code', 'name'))]
                for f in sorted(features, key=lambda x: x['code']):
                    locator = 'features/' + f['code']
                    candidates.append(({'path': FC, 'sha256': digest, 'locator': locator}, f))
                    refs = {b['ref'] for b in f.get('bindings', []) if b.get('type') == 'attribute'}
                    for attr in catalogue.get('attributes', []):
                        if attr['code'] in refs:
                            candidates.append(({'path': FC, 'sha256': digest,
                                                'locator': 'attributes/' + attr['code']}, attr))
            else:
                node_text, node_hash = _read(NODES)
                edge_text, edge_hash = _read(EDGES)
                nodes = {n['id']: n for n in _json_rows(node_text)}
                seeds = {key for key, n in nodes.items()
                         if any(str(n.get('properties', {}).get(k, '')).casefold() in terms
                                for k in ('canonical_name', 'catalogue_name'))
                         or any(_contains(folded, str(n.get(k, ''))) for k in ('name',))}
                for line, edge in _edge_rows(edge_text):
                    if edge['subject_id'] not in seeds and edge['object_id'] not in seeds:
                        continue
                    # Only actual edges whose both endpoints exist; never infer links.
                    endpoints = [edge['subject_id'], edge['object_id']]
                    if not all(key in nodes for key in endpoints):
                        continue
                    record = {'edge': edge, 'endpoints': [nodes[key] for key in endpoints]}
                    source = {'path': EDGES, 'sha256': edge_hash, 'locator': 'line:' + str(line),
                              'edge_id': edge.get('id'), 'nodes_path': NODES, 'nodes_sha256': node_hash}
                    candidates.append((source, record))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            packet['errors'].append({'error_type': type(exc).__name__, 'stage': method})
    chunks, seen = [], set()
    for source, record in candidates:
        identity = (source['path'], source['locator'])
        if identity in seen:
            continue
        seen.add(identity)
        packet['matched_records'] += 1
        chunk = json.dumps({'source': source, 'record': record}, ensure_ascii=False, sort_keys=True)
        if sum(map(len, chunks)) + len(chunks) + len(chunk) > max_chars:
            packet['omitted_records'] += 1
            continue
        chunks.append(chunk)
        packet['sources'].append(source)
    packet['evidence'] = '\n'.join(chunks)
    packet['evidence_text'] = packet['evidence']
    packet['evidence_sha256'] = _sha(packet['evidence'].encode('utf-8'))
    packet['hash'] = packet['evidence_sha256']
    if chunks:
        packet['status'] = 'AVAILABLE'
    elif candidates:
        packet['status'] = 'EVIDENCE_BUDGET_EXHAUSTED'
    packet['packet_sha256'] = _sha(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode('utf-8'))
    return packet
