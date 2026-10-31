"""Derive new code lineage only after re-verifying unchanged frozen data and DB.

Never edits the parent manifest, rewrites source data, or loads/writes a DB.
Only two explicitly named execution files may acquire new hashes. All data
files and each actual research DB relation must still match the parent bytes.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from .binding_snapshot import digest, verify_files, ROOT, TARGET_CONTAINER

DATABASE = 'scie_model_v3'
CODE_REFRESH_ALLOWLIST = frozenset({'services/orchestrator/query_normalizer.py',
                                   'services/orchestrator/graph_rag_retriever.py'})
RELATION_KEYS = {'knowledge.document_chunks': 'chunk_id',
    'knowledge.capability_embeddings': 'id', 'serving.marine_gazetteer_current': 'source_id',
    'serving.navigation_aid_current': 'source_id', 'serving.island_gazetteer_current': 'source_id',
    'projection.s101_feature_current': 'feature_instance_id'}


def safe_child(folder, relative):
    p = (Path(folder)/relative).resolve()
    if not p.is_relative_to(Path(folder).resolve()):
        raise ValueError('Snapshot artifact escapes its directory')
    return p


def validate_parent(parent, parent_dir, refresh_code, root=ROOT):
    requested = set(refresh_code)
    if not requested or not requested <= CODE_REFRESH_ALLOWLIST:
        raise ValueError('Explicit execution-source allowlist required')
    if parent.get('status') != 'LOADED_VERIFIED' or parent.get('db_identity') != {
            'container': TARGET_CONTAINER, 'database': DATABASE}:
        raise ValueError('Verified model research parent required')
    relations = parent.get('relations', [])
    if len(relations) != len(RELATION_KEYS) or {r['relation'] for r in relations} != set(RELATION_KEYS):
        raise ValueError('All six frozen relations required')
    names = [r['csv_path'] for r in relations]
    if len(set(names)) != len(names):
        raise ValueError('Distinct data artifacts required')
    for r in relations:
        if digest(safe_child(parent_dir, r['csv_path'])) != r['sha256']:
            raise ValueError('Parent data export changed: '+r['relation'])
    changes = []
    seen = set()
    for item in parent.get('files', []):
        path = item['path']
        if path in seen:
            raise ValueError('Duplicate mounted source entry')
        seen.add(path)
        actual = digest(safe_child(root, path))
        if actual != item['sha256']:
            if path not in requested:
                raise ValueError('Non-authorized mounted source changed: '+path)
            changes.append({'path': path, 'parent_sha256': item['sha256'], 'derived_sha256': actual,
                'change_type': 'EXECUTION_SOURCE_ONLY_NOT_DATA_REBASELINE'})
    if not requested <= seen:
        raise ValueError('Requested source absent from parent manifest')
    if not changes:
        raise ValueError('No execution source change to derive')
    return changes


def export_relation(record, destination):
    relation = record['relation']
    if relation not in RELATION_KEYS:
        raise ValueError('Unknown research relation')
    # Both identifiers come only from this static allowlist. -q suppresses
    # BEGIN/COMMIT command tags; COPY remains byte-comparable with parent CSV.
    query = ('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY; '
             'SET LOCAL statement_timeout=\'180s\'; '
             'COPY (SELECT * FROM '+relation+' ORDER BY '+RELATION_KEYS[relation]+') TO STDOUT WITH CSV HEADER; COMMIT;')
    with Path(destination).open('xb') as stream:
        subprocess.run(['docker', 'exec', TARGET_CONTAINER, 'psql', '-X', '-q', '-v', 'ON_ERROR_STOP=1',
            '-U', 'postgres', '-d', DATABASE, '-c', query], stdout=stream, stderr=subprocess.PIPE,
            check=True, timeout=240)
    actual = digest(destination)
    if actual != record['sha256']:
        raise ValueError('Actual research DB content differs from frozen parent: '+relation)
    return {'relation': relation, 'rows': record['rows'], 'roundtrip_sha256': actual,
        'content_match': True, 'row_count_basis': 'exact entire CSV including header matches parent',
        'transaction_mode': 'per-relation REPEATABLE READ READ ONLY',
        'verified_at': datetime.now(timezone.utc).isoformat()}


def derive(parent_path, output, refresh_code):
    parent_path, output = Path(parent_path).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError('New derived snapshot directory required')
    parent_hash = digest(parent_path)
    parent = json.loads(parent_path.read_text(encoding='utf-8'))
    changes = validate_parent(parent, parent_path.parent, refresh_code)
    info = json.loads(subprocess.check_output(['docker', 'inspect', TARGET_CONTAINER]))[0]
    if info['Config'].get('Labels', {}).get('marine.scie.research') != 'true':
        raise ValueError('Research container label required')
    output.mkdir(parents=True)
    derived = deepcopy(parent)
    derived.update(status='DERIVING_EXECUTION_SNAPSHOT', loaded_verification=[],
        derived_at=datetime.now(timezone.utc).isoformat(),
        derivation={'kind': 'SAME_DATA_NEW_EXECUTION_SOURCE_LINEAGE', 'parent_manifest_path': str(parent_path),
            'parent_manifest_sha256': parent_hash, 'execution_source_changes': changes,
            'requested_refresh_allowlist': sorted(refresh_code), 'database_writes': False,
            'data_rebaselined': False, 'coverage_or_gold_promoted': False,
            'consistency_scope': 'Every relation re-exported in its own read-only repeatable-read transaction and matches the same immutable parent content; not a single cross-relation transaction.'})
    by_path = {c['path']: c['derived_sha256'] for c in changes}
    for item in derived['files']:
        if item['path'] in by_path:
            item['sha256'] = by_path[item['path']]
    def save():
        (output/'snapshot_manifest.json').write_text(json.dumps(derived, ensure_ascii=False, indent=2), encoding='utf-8')
    save()
    try:
        for record in parent['relations']:
            destination = safe_child(output, record['csv_path'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            derived['loaded_verification'].append(export_relation(record, destination))
            save()
        # Parent data and all mounted artifacts are rechecked after actual DB
        # export; changed code must still equal the captured new digest.
        if digest(parent_path) != parent_hash:
            raise ValueError('Parent manifest changed during derivation')
        if validate_parent(parent, parent_path.parent, refresh_code) != changes:
            raise ValueError('Execution source changed during derivation')
        verify_files(derived, output)
        derived['status'] = 'LOADED_VERIFIED'
        derived['derivation']['all_six_db_content_hashes_match_parent'] = True
        derived['derivation']['parent_manifest_unchanged'] = True
        save()
    except BaseException as exc:
        derived.update(status='DERIVATION_FAILED', error_type=type(exc).__name__, error=str(exc))
        save()
        raise
    return derived


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--parent', required=True); p.add_argument('--output', required=True)
    p.add_argument('--refresh-code', choices=sorted(CODE_REFRESH_ALLOWLIST), action='append', required=True)
    a = p.parse_args(); derive(a.parent, a.output, a.refresh_code)
