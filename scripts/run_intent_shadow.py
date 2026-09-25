"""Reproducible offline shadow comparison; never changes the live router.

python -m scripts.run_intent_shadow --ollama-url http://host.docker.internal:11434 --model gemma2:latest
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from services.orchestrator.intent_shadow import (
    ROOT, PROMPT, fingerprint, json_request, prepare_candidates, rankings, registry_snapshot, score_candidates,
)


def validate_dataset(dataset):
    cases = dataset["cases"]
    ids, queries, groups = set(), set(), {}
    for case in cases:
        normalized = "".join(case["query"].casefold().split())
        if case["id"] in ids or normalized in queries:
            raise ValueError("Duplicate case or normalized query")
        if case["split"] not in {"calibration", "evaluation"}:
            raise ValueError("Invalid split")
        if case["group"] in groups and groups[case["group"]] != case["split"]:
            raise ValueError("Lineage group leaks across calibration/evaluation")
        ids.add(case["id"]); queries.add(normalized); groups[case["group"]] = case["split"]
    return cases


def fit_temperature(rows):
    eligible = [row for row in rows if row["case"]["split"] == "calibration" and row["shadow"].get("accepted")
                and row["case"]["expected_route"] in {c["candidate_id"] for c in row["candidates"]}]
    if not eligible:
        return {"temperature": 1., "status": "NOT_FITTED", "case_ids": []}
    trials = []
    for temperature in (.1, .25, .5, 1., 2., 4.):
        losses = []
        for row in eligible:
            probs = rankings(row["candidates"], row["shadow"], temperature)["ollama_calibrated"]["probabilities"]
            losses.append(-math.log(max(probs[row["case"]["expected_route"]], 1e-12)))
        trials.append({"temperature": temperature, "nll": statistics.mean(losses)})
    best = min(trials, key=lambda trial: trial["nll"])
    return {**best, "status": "FITTED_OFFLINE_ONLY", "case_ids": [r["case"]["id"] for r in eligible], "trials": trials}


def metrics(rows, method):
    truth, predicted, confidence = [], [], []
    nll, brier, fallbacks, abstentions = [], [], 0, 0
    for row in rows:
        expected = row["case"]["expected_route"]
        ranking = row["rankings"].get(method)
        if ranking is None:
            fallbacks += 1
            ranking = row["rankings"]["rule"] if "mix" in method or method == "rule" else {"ranking": [], "probabilities": {}}
        top = ranking["ranking"][0] if ranking["ranking"] else None
        if method.startswith("ollama") and row["shadow"].get("judgement", {}).get("out_of_candidates"):
            top = None
        if method == "registry_context_mix" and ranking.get("advisory_blocked"):
            top = None
        abstentions += int(top is None)
        probabilities = ranking["probabilities"]
        truth.append(expected); predicted.append(top); confidence.append(probabilities.get(top, 0.))
        nll.append(-math.log(max(probabilities.get(expected, 0.), 1e-12)))
        brier.append(sum((probabilities.get(label, 0.) - int(label == expected)) ** 2 for label in set(probabilities) | {expected}))
    labels = sorted(set(truth))
    f1s = []
    for label in labels:
        tp = sum(a == b == label for a, b in zip(truth, predicted))
        fp = sum(a != label and b == label for a, b in zip(truth, predicted))
        fn = sum(a == label and b != label for a, b in zip(truth, predicted))
        f1s.append(2*tp / max(2*tp + fp + fn, 1))
    correct = [a == b for a, b in zip(truth, predicted)]
    ece = 0.
    for bin_id in range(5):
        indices = [i for i, value in enumerate(confidence) if min(int(value*5), 4) == bin_id]
        if indices:
            ece += len(indices)/max(len(rows),1)*abs(statistics.mean(confidence[i] for i in indices)-statistics.mean(correct[i] for i in indices))
    return {"n": len(rows), "provisional_label_agreement": statistics.mean(correct) if rows else None,
            "single_label_macro_f1": statistics.mean(f1s) if f1s else None,
            "interpretation": "Agreement with an unreviewed single route label, not task correctness; related or composed capabilities may be valid",
            "nll": statistics.mean(nll) if nll else None, "brier": statistics.mean(brier) if brier else None,
            "ece_5_bins": ece if rows else None, "fallback_count": fallbacks, "abstentions": abstentions,
            "label_disagreements": [{"id": r["case"]["id"], "group": r["case"].get("group"), "reference_label": a, "selected": b, "semantic_verdict": "NOT_REVIEWED"} for r,a,b in zip(rows,truth,predicted) if a != b]}


def summarize(rows, calibration, dataset):
    for row in rows:
        row["rankings"] = rankings(row["candidates"], row["shadow"], calibration["temperature"])
        rule = row["rankings"]["rule"]["ranking"][0]
        row["disagreement"] = {name: rank["ranking"][0] != rule for name,rank in row["rankings"].items()}
        judgement = row["shadow"].get("judgement", {})
        row["decision_disagreement"] = {
            "ollama_vs_rule": (judgement.get("selected_candidate") != rule) if row["shadow"].get("accepted") else None,
            "out_of_candidates": judgement.get("out_of_candidates"),
            "requires_clarification": judgement.get("requires_clarification"),
        }
    evaluation = [row for row in rows if row["case"]["split"] == "evaluation"]
    methods = ["rule", "ollama", "ollama_calibrated", "simple_mix", "calibrated_mix", "registry_context_mix"]
    covered = [r for r in evaluation if r["case"]["expected_route"] in {c["candidate_id"] for c in r["candidates"]}]
    return {"label_status": dataset["label_status"], "gold_label_accuracy": None,
            "scope": "provisional pilot; not an independent human-verified holdout",
            "counts": {"total": len(rows), "evaluation": len(evaluation), "reference_label_covered": len(covered)},
            "reference_label_coverage": len(covered)/len(evaluation) if evaluation else None,
            "semantic_candidate_recall": None,
            "task_adequacy": {"status": "NOT_REVIEWED", "required_task_coverage": None,
                              "acceptable_capability_combinations": None, "unnecessary_execution_rate": None,
                              "note": "Different route names alone do not establish semantic failure or missing capability"},
            "schema_success_rate": sum(r["shadow"].get("accepted",False) for r in rows)/len(rows) if rows else None,
            "latency_ms_median": statistics.median(r["shadow"]["latency_ms"] for r in rows) if rows else None,
            "calibration": {**calibration, "label_basis": dataset["label_status"], "deployable": False},
            "metrics_all_evaluation": {method: metrics(evaluation, method) for method in methods},
            "metrics_reference_label_covered": {method: metrics(covered, method) for method in methods},
            "reference_labels_absent": [r["case"]["id"] for r in evaluation if r not in covered],
            "unmeasured": {"slot_exact_match": None, "evidence_selection_f1": None,
                           "clarification_precision_recall": None, "reason": "Independent slot/evidence/clarification annotations are not available"},
            "inference_failures": [{"id": r["case"]["id"], "reason": r["shadow"].get("rejected_reason")}
                                   for r in rows if not r["shadow"].get("accepted")],
            "execution_observations": {status: sum(r.get("execution", {}).get("capture_status", "NOT_RUN") == status for r in rows)
                                       for status in ["OBSERVED", "ERROR", "TIMEOUT", "NOT_RUN"]},
            "rule_top_ties": [r["case"]["id"] for r in rows if sum(c["rule_score"] == max(x["rule_score"] for x in r["candidates"]) for c in r["candidates"]) > 1],
            "qlora_decision": {"apply": False, "status": "DEFER",
                               "missing_conditions": ["independent_human_gold", "sufficient_holdout", "repeated_errors_after_prompt_improvement", "base_license_gpu_rollback_review"]}}


def write_report(output, rows, dataset):
    report = summarize(rows, fit_temperature(rows), dataset)
    report["run_complete"] = len(rows) == len(dataset["cases"])
    report["scoring_source_hashes"] = {name: fingerprint((ROOT/name).read_text(encoding='utf-8-sig')) for name in
                                      ['services/orchestrator/intent_shadow.py','scripts/run_intent_shadow.py']}
    for name, content in [('report.json', json.dumps(report,ensure_ascii=False,indent=2)),
                          ('scored_rows.jsonl', ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))]:
        temporary = output/(name+'.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(output/name)
    return report


def capture_execution(case, api_url):
    try:
        task = json_request(api_url.rstrip('/') + '/api/v1/tasks', {"query": case["query"],
                            "spatial_context": case.get("context", {}).get("spatial_context", {})}, timeout=30)
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            result = json_request(api_url.rstrip('/') + '/api/v1/tasks/' + task['task_id'], timeout=30)
            if result.get('status') in {'COMPLETED','PARTIAL','FAILED','BLOCKED','NEEDS_CLARIFICATION','WAITING_FOR_REVIEW'}:
                return {"capture_status": "OBSERVED", "task_id": task['task_id'], "response": result,
                        "conversation_forwarded": False}
            time.sleep(.5)
        return {"capture_status": "TIMEOUT", "task_id": task['task_id']}
    except Exception as exc:
        return {"capture_status": "ERROR", "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT/'configs/evaluation/intent_shadow_pilot.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ollama-url', default='http://host.docker.internal:11434')
    parser.add_argument('--model')
    parser.add_argument('--summarize-only', action='store_true', help='Recompute a report from preserved rows without inference or API calls')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--api-url', help='Optional existing-router execution observations; no shadow action is executed')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--case-ids', nargs='+', help='Explicit subset, e.g. calibration cases for prompt diagnostics')
    args = parser.parse_args()
    if args.summarize_only:
        manifest = json.loads((args.output/'manifest.json').read_text(encoding='utf-8'))
        rows = [json.loads(line) for line in (args.output/'raw_rows.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        print(json.dumps(write_report(args.output, rows, manifest['dataset']), ensure_ascii=True))
        return
    if not args.model:
        parser.error('--model is required for inference')
    dataset = json.loads(args.dataset.read_text(encoding='utf-8-sig'))
    cases = validate_dataset(dataset)
    if args.case_ids:
        if set(args.case_ids) - {case['id'] for case in cases}:
            parser.error('Unknown case ID')
        cases = [case for case in cases if case['id'] in args.case_ids]
    if args.limit:
        cases = cases[:args.limit]
    if args.output.exists():
        raise ValueError('Use a new output directory to preserve immutable runs')
    args.output.mkdir(parents=True)
    os.environ['GEOLLM_SEMANTIC_PRIOR_OLLAMA'] = 'false'
    os.environ['GEOLLM_CAPABILITY_PGVECTOR'] = 'false'
    from services.orchestrator.query_candidate_broker import query_candidate_broker, _load_registry
    tags = json_request(args.ollama_url.rstrip('/')+'/api/tags')
    model = next((m for m in tags.get('models',[]) if m['name'] == args.model), None)
    if not model or 'completion' not in model.get('capabilities', ['completion']):
        raise ValueError('An installed completion model is required')
    try:
        commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "mode": "offline_shadow_no_execution_change",
                "dataset": dataset, "dataset_hash": fingerprint(dataset), "selected_case_ids": [c['id'] for c in cases], "model": model,
                "ollama_version": json_request(args.ollama_url.rstrip('/')+'/api/version'),
                "prompt": PROMPT.read_text(encoding='utf-8'), "registry_snapshot": registry_snapshot(),
                "commit": commit, "source_hashes": {name: fingerprint((ROOT/name).read_text(encoding='utf-8-sig')) for name in
                    ['services/orchestrator/intent_shadow.py','services/orchestrator/query_candidate_broker.py','scripts/run_intent_shadow.py']},
                "rule_baseline": {"pgvector": False, "ollama_prior": False},
                "mixture_weights": {"rule":.55,"ollama":.25,"registry":.1,"context":.1}}
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    rows = []
    for case in cases:
        trace = query_candidate_broker.build_trace(case['query'])
        candidates = prepare_candidates(trace, case.get('context',{}), _load_registry())
        shadow = score_candidates(case['query'],case.get('context',{}),candidates,base_url=args.ollama_url,model=args.model,timeout=args.timeout)
        row = {"case": case, "label_status": dataset['label_status'], "trace": trace, "candidates": candidates,
               "shadow": shadow, "execution": capture_execution(case,args.api_url) if args.api_url else {"capture_status":"NOT_RUN"}}
        rows.append(row)
        with (args.output/'raw_rows.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        print(json.dumps({"id":case['id'],"accepted":shadow['accepted'],"latency_ms":shadow['latency_ms'],"error":shadow.get('rejected_reason')},ensure_ascii=True),flush=True)
        write_report(args.output, rows, dataset)
    report = write_report(args.output, rows, dataset)
    print(json.dumps({"report":str(args.output/'report.json'),"schema_success_rate":report['schema_success_rate'],"reference_label_coverage":report['reference_label_coverage']}),flush=True)


if __name__ == '__main__':
    main()
