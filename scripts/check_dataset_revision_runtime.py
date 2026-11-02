"""Operational regression for repaired source text, warnings and default radius."""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.check_geollm_web_samples import observe
from scripts.check_coverage_availability_20261102 import hashes
from scripts.audit_dataset_answer_usage import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repair-receipt', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    repair = json.loads(args.repair_receipt.read_text(encoding='utf-8'))
    before = hashes()
    cases = [('revised_csv', '해양수산부 행정규칙 자료를 알려줘'),
             ('coordinate_warning', '2023 해양사고심판사례집 북위 35도 02분 60초 자료를 알려줘'),
             ('default_radius', '독도 부근 지명을 알려줘')]
    results = []
    for index, (name, query) in enumerate(cases):
        row = observe('http://127.0.0.1:8000', index, query, socket_timeout=180, observation_timeout=300)
        raw = json.dumps(row, ensure_ascii=False, indent=2).encode()
        (args.output / (name + '.json')).write_bytes(raw)
        final = (row.get('completion') or {}).get('final_result') or {}
        structured = final.get('structured_result') or {}
        body = final.get('answer_text') or final.get('summary') or ''
        passages = structured.get('source_passages') or []
        if name == 'revised_csv':
            ids = {p['chunk_id'] for p in passages}
            checks = {'source_answer': inspect(row)['passed'], 'new_revision_used': bool(ids) and ids <= set(repair['new_ids']),
                      'old_revision_absent': not ids.intersection(repair['old_ids']),
                      'audited': bool(passages) and all(p['source_text_verification']['status'] == 'AUDIT_SNAPSHOT_MATCH' for p in passages)}
        elif name == 'coordinate_warning':
            checks = {'source_answer': inspect(row)['passed'],
                      'warning_receipt': any(p.get('source_text_verification', {}).get('coordinate_literal_issues') for p in passages),
                      'warning_in_answer': '원문 좌표 표기에 검토' in body,
                      'no_coordinate_authority': structured.get('coordinate_authority') is False}
        else:
            checks = {'completed': final.get('status') == 'COMPLETED',
                      'default_10km': structured.get('distance_m') == 10000,
                      'source_bound': structured.get('count_scope') == 'SOURCE_CORPUS_RETURNED_ROWS',
                      'no_absence_claim': structured.get('absence_certified') is False,
                      'nonempty': (structured.get('returned_count') or 0) > 0}
        result = {'case': name, 'passed': all(checks.values()), 'checks': checks, 'raw_sha256': hashlib.sha256(raw).hexdigest()}
        results.append(result)
        print(json.dumps(result), flush=True)
    result = {'checks': results, 'source_hashes_before': before, 'source_unchanged': before == hashes(),
              'paper_experiment': False, 'holdout_used': False, 'semantic_accuracy': None}
    (args.output / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    raise SystemExit(0 if result['source_unchanged'] and all(r['passed'] for r in results) else 1)


if __name__ == '__main__':
    main()
