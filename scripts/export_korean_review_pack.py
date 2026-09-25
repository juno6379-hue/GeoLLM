"""Export unlabelled, model-blind development review forms; never invent human gold."""
import argparse
import json
from pathlib import Path

from services.orchestrator.intent_shadow import fingerprint


def review_forms(snapshot):
    for case in snapshot['cases']:
        yield {'sample': case['sample'], 'query': case['query'], 'context': case['context'],
               'input_sha256': fingerprint(case['inputs']),
               'dataset_role': 'DEVELOPMENT_NOT_INDEPENDENT_HOLDOUT',
               'review_status': 'UNREVIEWED', 'reviewer_ids': [],
               'reference_policy_version': 'maritime-reference-v1',
               'reference_bindings': [], 'expected_claims': [],
               'reference_review_status': 'UNREVIEWED',
               'required_tasks': [], 'slots': {}, 'needs_clarification': None,
               'forbidden_capabilities': [], 'candidate_gap': None,
               'rationale': None, 'capability_contracts': case['inputs']['capability_contracts'],
               'candidate_issue': case['candidate_issue']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        for form in review_forms(snapshot):
            stream.write(json.dumps(form, ensure_ascii=False)+'\n')
    print(json.dumps({'forms':len(snapshot['cases']), 'human_gold':False, 'model_outputs_included':False}))


if __name__ == '__main__':
    main()
