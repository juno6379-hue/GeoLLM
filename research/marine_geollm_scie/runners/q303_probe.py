"""Single-case no-model diagnostic, not a replacement K5 experiment."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import uuid
from research.marine_geollm_scie.runners.execution_observer import ExecutionObserver, q303_checks
from research.marine_geollm_scie.baselines.production_adapter import observable


def main(output):
    out = Path(output)
    if out.exists():
        raise FileExistsError(out)
    from services.orchestrator.graph import orchestrator_graph
    identifier = str(uuid.uuid4())
    initial = {'task_id': identifier, 'query': 'Find wrecks intersecting the selected area.',
               'organization_id': 'research_diagnostic', 'user_id': 'research_diagnostic',
               'status': 'RECEIVED', 'spatial_context': {}, 'state_history': []}
    observer = ExecutionObserver(identifier)
    row = {'case_id': 'PILOT_Q3_03', 'condition': 'isolated_no_network_no_model_diagnostic',
           'initial_state': initial, 'not_k5_replacement': True}
    try:
        with observer:
            row['final_state'] = observable(asyncio.run(orchestrator_graph.ainvoke(initial,
                config={'configurable': {'thread_id': identifier}, 'recursion_limit': 30})))
    finally:
        row['execution_observation'] = observer.result()
        row['checks'] = q303_checks((row.get('final_state') or {}).get('final_dict') or {}, row['execution_observation'])
        row['semantic_gold_scored'] = False
        row['source_hashes'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('services', 'shared', 'research/marine_geollm_scie/runners')
            for p in Path(folder).rglob('*.py')}
        out.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(row['checks']))


if __name__ == '__main__':
    main(sys.argv[1])
