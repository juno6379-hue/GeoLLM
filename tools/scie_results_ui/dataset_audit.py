"""Project safe progress counters only; never load document or holdout content."""
import hashlib
import json
from pathlib import Path

PREFIX = Path('outputs/dataset_location_audit_20261102')
STAGES = ('source', 'spatial', 'answer')
FOLLOWUP_PREFIX = Path('outputs/dataset_unverified_followup_20261102')
STATUSES = {'RUNNING', 'PARTIALLY_VERIFIED', 'COMPLETED', 'BLOCKED', 'FAILED', 'NOT_STARTED'}


def load_progress(root):
    rows = []
    jobs = [(stage, PREFIX, stage) for stage in STAGES]
    jobs += [('followup_' + stage, FOLLOWUP_PREFIX, stage) for stage in ('pdf', 'locator', 'entity')]
    for stage, prefix, folder in jobs:
        relative = prefix / folder / 'status.json'
        path = (root / relative).resolve()
        row = dict(stage=stage, status='NOT_STARTED', counts={}, limitations=[], evidence=[],
                   source_path=relative.as_posix(), source_sha256=None)
        if path.is_relative_to((root / prefix).resolve()) and path.is_file():
            try:
                raw = path.read_bytes()
                value = json.loads(raw.decode('utf-8-sig'))
                if not isinstance(value, dict):
                    raise ValueError('Expected object')
                row.update(status=value.get('status') if value.get('status') in STATUSES else 'UNKNOWN',
                           updated_at=str(value.get('updated_at') or ''),
                           summary=str(value.get('summary') or ''),
                           source_sha256=hashlib.sha256(raw).hexdigest())
                counts = value.get('counts', {})
                row['counts'] = {str(k): v for k, v in counts.items()
                                 if v is None or (type(v) is int and v >= 0)} if isinstance(counts, dict) else {}
                row['limitations'] = [s for s in value.get('limitations', []) if isinstance(s, str)]
                # Identity only. No automatic dereferencing or file download route.
                for item in value.get('evidence', []):
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get('path') or '').replace('\\', '/')
                    if name.startswith(prefix.as_posix() + '/') and '..' not in Path(name).parts:
                        row['evidence'].append(dict(path=name, sha256=item.get('sha256')))
            except (OSError, ValueError, TypeError):
                row.update(status='UNAVAILABLE_LOCAL_ARTIFACT', limitations=['진행 파일을 읽는 중이거나 형식이 유효하지 않습니다. 이전 검사 성공을 추정하지 않습니다.'])
        rows.append(row)
    return dict(status='RUNNING' if any(r['status'] == 'RUNNING' for r in rows) else 'PARTIAL_OR_UNVERIFIED',
                dataset_semantic_audit_complete=False, holdout_used=False, stages=rows)
