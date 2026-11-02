"""Validate an explicit development GOLD atom package without scoring answers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .grounding_atoms_v1 import score_atoms, _json_value

PACKAGE = Path('research/marine_geollm_scie/benchmark/grounding_atoms_20261102_v1')


def validate_annotation_package(root, queries, package=PACKAGE, *, expected_case_count=18):
    root = Path(root).resolve()
    errors, cache = [], {}
    result = dict(status='UNAVAILABLE', expected_cases=expected_case_count, written_cases=0,
                  validated_cases=0, atom_count=0, optional_atom_count=0, human_approval=False,
                  independent_human_review=False, prediction_atoms_status='NOT_ANNOTATED',
                  measurement_status='NOT_MEASURED', errors=errors, package=str(package).replace('\\', '/'))

    def read(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or any('holdout' in p.lower() for p in path.relative_to(root).parts):
            raise ValueError('SOURCE_PATH_NOT_ALLOWED')
        key = path.as_posix()
        if key not in cache:
            raw = path.read_bytes()
            cache[key] = raw, hashlib.sha256(raw).hexdigest()
        return cache[key]

    def reference(ref):
        raw, digest = read(ref['path'])
        if digest != ref.get('sha256'):
            raise ValueError('SOURCE_HASH_MISMATCH')
        text = raw.decode('utf-8-sig')
        if 'jsonl_line' in ref:
            line = ref['jsonl_line']
            if type(line) is not int or line < 1:
                raise ValueError('INVALID_SOURCE_LINE')
            obj = json.loads(text.splitlines()[line - 1])
        else:
            obj = json.loads(text)
        pointer = ref.get('json_pointer', '')
        if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
            raise ValueError('INVALID_JSON_POINTER')
        for token in pointer.split('/')[1:]:
            token = token.replace('~1', '/').replace('~0', '~')
            if isinstance(obj, list):
                if not token.isdecimal() or (len(token) > 1 and token.startswith('0')):
                    raise ValueError('INVALID_JSON_ARRAY_POINTER')
                obj = obj[int(token)]
            else:
                obj = obj[token]
        return obj

    try:
        manifest_bytes, manifest_hash = read(Path(package) / 'manifest.json')
    except FileNotFoundError:
        return result
    except (OSError, ValueError) as exc:
        result.update(status='INVALID', errors=[str(exc)])
        return result
    try:
        manifest = json.loads(manifest_bytes)
        files = manifest.get('files')
        if not isinstance(files, dict) or not files:
            raise ValueError('MANIFEST_FILES_REQUIRED')
        for filename, expected_hash in files.items():
            if not isinstance(filename, str) or Path(filename).is_absolute() or '..' in Path(filename).parts:
                raise ValueError('MANIFEST_FILE_PATH_INVALID')
            if read(Path(package) / filename)[1] != expected_hash:
                raise ValueError('MANIFEST_FILE_HASH_MISMATCH')
        sources = manifest.get('sources')
        if not isinstance(sources, list) or not sources:
            raise ValueError('MANIFEST_SOURCES_REQUIRED')
        for source in sources:
            if read(source['path'])[1] != source.get('sha256'):
                raise ValueError('MANIFEST_SOURCE_HASH_MISMATCH')
        task_ids = manifest.get('task_ids')
        if not isinstance(task_ids, list) or not task_ids or any(not isinstance(x, str) or not x for x in task_ids):
            raise ValueError('DECLARED_TASK_IDS_REQUIRED')
        raw, digest = read(Path(package) / 'gold_atoms.jsonl')
        if manifest.get('files', {}).get('gold_atoms.jsonl') != digest:
            raise ValueError('ANNOTATION_HASH_MISMATCH')
        rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        result.update(written_cases=len(rows), manifest_sha256=manifest_hash, annotation_sha256=digest)
        query_by_id = {q['case_id']: q for q in queries}
        if len(query_by_id) != len(queries) or len(queries) != expected_case_count:
            raise ValueError('EXPECTED_QUERY_COHORT_MISMATCH')
        if len(rows) != expected_case_count or manifest.get('case_count') != expected_case_count:
            raise ValueError('ANNOTATION_CASE_COUNT_MISMATCH')
        seen, atom_ids = set(), set()
        for row in rows:
            cid = row.get('case_id')
            try:
                if cid in seen or cid not in query_by_id:
                    raise ValueError('DUPLICATE_OR_UNKNOWN_CASE')
                seen.add(cid)
                query = query_by_id[cid]
                if row.get('query') != query['query'] or row.get('query_sha256') != hashlib.sha256(query['query'].encode()).hexdigest():
                    raise ValueError('QUERY_HASH_MISMATCH')
                if row.get('equivalence_group') != query.get('equivalence_group'):
                    raise ValueError('EQUIVALENCE_GROUP_MISMATCH')
                source = reference(row['source_contract'])
                if source.get('case_id') != cid:
                    raise ValueError('SOURCE_CONTRACT_CASE_MISMATCH')
                if source.get('query') != query['query']:
                    raise ValueError('SOURCE_CONTRACT_QUERY_MISMATCH')
                mapping = row.get('task_mapping')
                if not isinstance(mapping, dict) or not mapping or any(k not in task_ids for k in mapping):
                    raise ValueError('CASE_TASK_MAPPING_INVALID')
                atoms = row['atoms']
                if not atoms:
                    raise ValueError('EMPTY_GOLD_ATOMS')
                optional_atoms = row.get('optional_atoms', [])
                all_atoms = atoms + optional_atoms
                score_atoms(all_atoms, [])  # schema only; optional atoms are not mandatory scoring targets
                for atom in all_atoms:
                    if atom.get('task_id') not in task_ids or atom.get('task_id') not in mapping:
                        raise ValueError('UNDECLARED_TASK_ID')
                    if atom.get('derivation') not in {'DIRECT_CONTRACT_VALUE', 'CONTRACT_PROJECTION', 'AI_CANONICALIZATION_PROPOSAL'}:
                        raise ValueError('UNKNOWN_DERIVATION')
                    if atom['atom_id'] in atom_ids:
                        raise ValueError('DUPLICATE_GLOBAL_ATOM_ID')
                    atom_ids.add(atom['atom_id'])
                    refs = atom.get('source_refs')
                    if not refs:
                        raise ValueError('ATOM_SOURCE_MISSING')
                    values = [reference(ref) for ref in refs]
                    if atom.get('derivation') == 'DIRECT_CONTRACT_VALUE' and not all(_json_value(v) in {_json_value(x) for x in values} for v in atom['accepted_values']):
                        raise ValueError('DIRECT_VALUE_NOT_IN_SOURCE')
                result['validated_cases'] += 1
                result['atom_count'] += len(atoms)
                result['optional_atom_count'] += len(optional_atoms)
            except (KeyError, IndexError, TypeError, ValueError, OSError) as exc:
                errors.append({'case_id': cid, 'reason': str(exc)})
        if seen != query_by_id.keys():
            errors.append({'reason': 'CASE_COHORT_MISMATCH'})
        result['status'] = 'VALIDATED_AI_ANNOTATION' if not errors else 'INVALID'
        result['annotation_complete'] = not errors
        result['limitation'] = '파일·질의·원천 포인터 검증이며 독립 인간 의미 검수나 모델 성능 측정이 아닙니다.'
    except (KeyError, IndexError, TypeError, ValueError, OSError) as exc:
        errors.append({'reason': str(exc)})
        result['status'] = 'INVALID'
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--queries', type=Path, default=Path('research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1/queries.jsonl'))
    args = parser.parse_args()
    root = args.root.resolve()
    query_path = (root / args.queries).resolve()
    if not query_path.is_relative_to(root) or any('holdout' in x.lower() for x in query_path.relative_to(root).parts):
        parser.error('Only local development queries are accepted')
    queries = [json.loads(line) for line in query_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    result = validate_annotation_package(root, queries)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('annotation_complete') else 1


if __name__ == '__main__':
    raise SystemExit(main())
