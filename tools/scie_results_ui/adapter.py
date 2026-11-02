"""File-backed projection of existing research artifacts; never runs experiments."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote

import yaml

RESEARCH = Path('research/marine_geollm_scie')
GOLD = 'benchmark/gold_v2_immutable_20261101_v1'
BASE = '/research/scie-results'


class ResultsAdapter:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.research = self.root / RESEARCH
        self.sources: dict[str, dict] = {}
        self.allowed: dict[str, Path] = {}
        self.generated = datetime.now(timezone.utc).isoformat()
        self.cache = {}

    def load(self, relative: str, default=None):
        if relative in self.cache:
            return self.cache[relative]
        path = (self.research / relative).resolve()
        if not path.is_relative_to(self.research.resolve()):
            raise ValueError('outside research root')
        key = path.relative_to(self.root).as_posix()
        receipt = dict(source_path=key, source_sha256=None, source_version=path.parent.name,
                       generated_at=self.generated, status='UNAVAILABLE_LOCAL_ARTIFACT', limitations=[])
        self.sources[key] = receipt
        if not path.is_file():
            return default
        raw = path.read_bytes()
        receipt.update(source_sha256=hashlib.sha256(raw).hexdigest(), status='AVAILABLE',
                       artifact_url=BASE + '/artifact?path=' + quote(key, safe=''))
        self.allowed[key] = path
        try:
            text = raw.decode('utf-8-sig')
            if path.suffix == '.json':
                value = json.loads(text)
                if not isinstance(value, dict):
                    raise ValueError('Expected object artifact')
            elif path.suffix == '.jsonl':
                value = []
                for line in text.splitlines():
                    if line.strip():
                        try:
                            item = json.loads(line)
                            if isinstance(item, dict):
                                value.append(item)
                            else:
                                raise json.JSONDecodeError('Expected object row', line, 0)
                        except json.JSONDecodeError:
                            receipt['status'] = 'PARTIAL'
                            receipt['limitations'].append('읽는 시점의 불완전 JSONL 행은 집계하지 않음')
            elif path.suffix in ('.yaml', '.yml'):
                value = yaml.safe_load(text)
                if not isinstance(value, dict):
                    raise ValueError('Expected mapping artifact')
            else:
                value = text
            if isinstance(value, dict):
                receipt['source_version'] = value.get('version', value.get('schema_version', path.parent.name))
            self.cache[relative] = value
            return value
        except (ValueError, UnicodeError, yaml.YAMLError) as exc:
            receipt.update(status='UNAVAILABLE_LOCAL_ARTIFACT', limitations=[type(exc).__name__])
            return default

    def graph_count(self, relative):
        """Count complete physical JSONL records without retaining large QEC geometry."""
        path = (self.research / relative).resolve()
        if not path.is_relative_to(self.research.resolve()):
            raise ValueError('outside research root')
        key = path.relative_to(self.root).as_posix()
        if not path.is_file():
            self.load(relative, None)
            return None
        digest = hashlib.sha256()
        count = 0
        with path.open('rb') as stream:
            for line in stream:
                digest.update(line)
                if line.strip() and line.endswith(b'\n'):
                    count += 1
        self.sources[key] = dict(source_path=key, source_sha256=digest.hexdigest(),
            source_version=path.parent.parent.name, generated_at=self.generated, status='AVAILABLE',
            limitations=['물리적 JSONL 행 수; 평가 성공 수 아님'], artifact_url=BASE + '/artifact?path=' + quote(key, safe=''))
        self.allowed[key] = path
        return count

    def _runs(self, index: str):
        ids = list(dict.fromkeys(re.findall(r'runs/(\d{8}_gold_v2_eight_k\d+_v\d+)', index)))
        selected = None
        for line in index.splitlines():
            if '최신 완료' in line:
                match = re.search(r'runs/(\d{8}_gold_v2_eight_k\d+_v\d+)', line)
                if match:
                    selected = match.group(1)
                    break
        runs = []
        for rid in ids:
            prefix = 'runs/' + rid
            status = self.load(prefix + '/status.json', {})
            manifest = self.load(prefix + '/comparison/manifest.json', {})
            comparison = self.load(prefix + '/comparison/observations.jsonl', [])
            graph_count = self.graph_count(prefix + '/graph/production_rows.jsonl')
            faults = self.load(prefix + '/faults/rows.jsonl', [])
            summary = self.load(prefix + '/report_with_faults/summary.json', {})
            gate = summary.get('completion_gate', {})
            index_line = next((line for line in index.splitlines() if rid in line), '')
            index_validated = '최신 완료' in index_line or '무결성 검증' in index_line or '무결성검증' in index_line
            identity = manifest.get('execution_identity', {})
            profile = self.load(prefix + '/profiles/model_profile.json', {})
            total = len({(r.get('case_id'), r.get('method'), r.get('repeat', 0)) for r in comparison})
            if not any(r.get('method') == 'P1' for r in comparison) and graph_count is not None:
                total += graph_count
            runs.append(dict(run_id=rid, status=status.get('status', 'UNAVAILABLE_LOCAL_ARTIFACT'),
                             stage=status.get('stage'), created_at=status.get('created_at'),
                             comparison_rows=len(comparison) if comparison else None,
                             graph_rows=graph_count,
                             observed_rows=total if comparison or graph_count is not None else None,
                             expected_rows=status.get('expected_comparison_rows'),
                             fault_rows=len(faults) if faults else None,
                             can_be_cited=index_validated and gate.get('observation_comparison_complete') is True and status.get('status') == 'COMPLETED_OBSERVATIONS',
                             index_validated=index_validated,
                             summary_available=bool(summary), source_hash=identity.get('system_source_sha256'),
                             snapshot_hash=identity.get('source_snapshot_sha256'),
                             model_digest=profile.get('model_digests'),
                             repeats=status.get('repeats'), completion_gate=gate,
                             limitations=manifest.get('limits', [])))
        return selected, runs

    @staticmethod
    def compact_row(row):
        keys = ('case_id', 'method', 'status', 'graph_status', 'initial_plan_hash', 'initial_plan_sha256',
                'review_artifact_sha256', 'raw_artifact_path', 'raw_artifact_sha256', 'execution_observation',
                'costs', 'schema_errors')
        return {k: row.get(k) for k in keys}

    def dashboard(self):
        index = self.load('RESULTS_INDEX_KR.md', '')
        selected, runs = self._runs(index)
        manifest = self.load(GOLD + '/manifest.json', {})
        protocol = self.load(GOLD + '/comparison_protocol.json', {})
        contracts = self.load(GOLD + '/answer_contracts.jsonl', [])
        queries = self.load(GOLD + '/queries.jsonl', [])
        rescore_path = 'review/20261102_approved_gold_rescore_v1'
        rescore = self.load(rescore_path + '/summary.json', {})
        approval = self.load(rescore_path + '/approval.json', {})
        self.load(rescore_path + '/재채점_결과_KR.md', '')
        self.load(rescore_path + '/scores.jsonl', [])
        receipt = self.sources.get((RESEARCH / GOLD / 'manifest.json').as_posix(), {})
        approval_valid = (approval.get('independent_human_review_complete') is True
            and bool(receipt.get('source_sha256'))
            and approval.get('gold_manifest_sha256') == receipt.get('source_sha256')
            and sorted(approval.get('case_ids', [])) == sorted(c['case_id'] for c in contracts))
        if not approval_valid or rescore.get('run_id') != selected:
            rescore = {}

        # Reserved evaluation material is not part of the public query/answer browser.
        # Only fixed high-level fields are projected; do not allow downloading the
        # raw holdout summary in case a future producer adds sensitive fields.
        holdout_path = 'benchmark/holdout_20261102_v1/summary.json'
        holdout_raw = self.load(holdout_path, {})
        holdout = {k: holdout_raw.get(k) for k in (
            'status', 'main_cases', 'rq2_fault_cases', 'rq2_invalid_cases', 'rq2_valid_controls', 'rq4_recovery_cases', 'spatial_oracle_cases',
            'gold_source_verified', 'human_review_complete', 'evaluation_executed',
            'system_freeze_complete', 'evaluation_ready', 'split', 'limitations', 'manifest_sha256')}
        holdout_key = (RESEARCH / holdout_path).as_posix()
        self.allowed.pop(holdout_key, None)
        self.sources[holdout_key].pop('artifact_url', None)
        self.sources[holdout_key]['limitations'].append('Reserved holdout: high-level summary only; no query/GOLD download')
        semantic_path = 'review/20261102_answer_semantic_review_v1/summary.json'
        semantic_raw = self.load(semantic_path, {})
        semantic_publication = {'status': 'PREPARED_FORMS_ONLY'}
        pointer = self.load('review/answer_semantic_latest.json', {})
        if pointer:
            try:
                relative = pointer.get('result_relative_path')
                if not isinstance(relative, str) or not relative.startswith('review/'):
                    raise ValueError('Review result path required')
                folder = (self.research / relative).resolve()
                if not folder.is_relative_to((self.research / 'review').resolve()):
                    raise ValueError('Result outside review root')
                result_manifest_path = folder / 'manifest.json'
                result_manifest_raw = result_manifest_path.read_bytes()
                if hashlib.sha256(result_manifest_raw).hexdigest() != pointer.get('manifest_sha256'):
                    raise ValueError('Published manifest hash mismatch')
                published_manifest = json.loads(result_manifest_raw)
                package_manifest = self.research / 'review/20261102_answer_semantic_review_v1/manifest.json'
                if published_manifest.get('source_package_manifest_sha256') != hashlib.sha256(package_manifest.read_bytes()).hexdigest():
                    raise ValueError('Different answer review package')
                published_summary_raw = (folder / 'summary.json').read_bytes()
                if hashlib.sha256(published_summary_raw).hexdigest() != published_manifest.get('files', {}).get('summary.json'):
                    raise ValueError('Published summary hash mismatch')
                published = json.loads(published_summary_raw)
                if (published.get('source_run_id') != selected
                    or published.get('gold_manifest_sha256') != receipt.get('source_sha256')):
                    raise ValueError('Published run/GOLD mismatch')
                semantic_path = (folder / 'summary.json').relative_to(self.research).as_posix()
                semantic_raw = self.load(semantic_path, {})
                semantic_publication = {'status': 'VERIFIED_PUBLISHED_RESULT', 'manifest_sha256': pointer['manifest_sha256']}
            except (ValueError, TypeError, OSError):
                semantic_publication = {'status': 'REJECTED_PUBLICATION', 'reason': '결과 경로·해시·원본 검수자료·실행/GOLD 연결 검증 실패'}

        semantic_review = {k: semantic_raw.get(k) for k in (
            'assisted_review_complete', 'assisted_metrics', 'independent_review_confirmed',
            'status', 'total_answers', 'reviewer_A_completed', 'reviewer_B_completed',
            'paired_completed', 'consensus_completed', 'semantic_human_accuracy',
            'human_answer_scoring_complete', 'gold_review_complete', 'gold_review_basis',
            'limitations', 'preparation_complete', 'by_method', 'agreement', 'source_run_id', 'gold_manifest_sha256')}
        semantic_identity_valid = (semantic_raw.get('source_run_id') == selected
            and semantic_raw.get('gold_manifest_sha256') == receipt.get('source_sha256')
            and bool(receipt.get('source_sha256')))
        semantic_review['source_identity_verified'] = semantic_identity_valid
        semantic_review['publication'] = semantic_publication
        if not semantic_identity_valid:
            semantic_review = dict(status='UNAVAILABLE_LOCAL_ARTIFACT', source_identity_verified=False,
                semantic_human_accuracy=None, human_answer_scoring_complete=False,
                limitations=['선택된 실행·GOLD와 연결된 답변 검수 자료가 아직 확인되지 않았습니다.'])
        # A prepared pack or approved GOLD alone never supplies human answer scores.

        if semantic_review.get('human_answer_scoring_complete') is not True:
            semantic_review['semantic_human_accuracy'] = None
        if semantic_identity_valid:
            for public_form in ('AAA_labels.jsonl', 'BBB_labels.jsonl', 'consensus_labels.jsonl',
                                'AAA_144답변_독립채점_KR.md', 'BBB_144답변_독립채점_KR.md', '채점안내_KR.md'):
                self.load('review/20261102_answer_semantic_review_v1/' + public_form, None)
            for category in range(1, 7):
                for number in range(1, 4):
                    self.load(f'review/20261102_answer_semantic_review_v1/gold_reference/PILOT_Q{category}_{number:02d}.json', {})



        self.load(GOLD + '/oracle_checks.json', {})
        self.load(GOLD + '/source_checks.json', {})
        self.load(GOLD + '/oracle_query.sql', '')
        self.load(GOLD + '/canonical_busan_boundary.json', {})
        freeze_checks = []
        for entry in manifest.get('files', []):
            name = entry.get('name', '')
            if not name or Path(name).name != name:
                freeze_checks.append(dict(name=name, verified=False))
                continue
            self.load(GOLD + '/' + name, None)
            receipt = self.sources.get((RESEARCH / GOLD / name).as_posix(), {})
            freeze_checks.append(dict(name=name, expected_sha256=entry.get('sha256'),
                                      actual_sha256=receipt.get('source_sha256'),
                                      verified=bool(entry.get('sha256')) and entry.get('sha256') == receipt.get('source_sha256')))
        summary, comparison, selected_status, selected_manifest, fault_rows = {}, [], {}, {}, []
        if selected:
            prefix = 'runs/' + selected
            summary = self.load(prefix + '/report_with_faults/summary.json', {})
            comparison = self.load(prefix + '/comparison/observations.jsonl', [])
            selected_status = self.load(prefix + '/status.json', {})
            selected_manifest = self.load(prefix + '/comparison/manifest.json', {})
            fault_rows = self.load(prefix + '/faults/rows.jsonl', [])
            self.load(prefix + '/report_with_faults/comparison_KR.md', '')
            self.load(prefix + '/fault_report/comparison_KR.md', '')
            version = selected.rsplit('_', 1)[-1]
            self.load(f'protocol/eight_results_{version}_{selected[:8]}_KR.md', '')
        # The index is authoritative: a newer finished worker is not silently promoted.
        selected_info = next((r for r in runs if r['run_id'] == selected), {})
        overall = summary.get('overall_by_method', {})
        fault = summary.get('controlled_fault_recovery', {})
        detector_breakdown = {}
        for method in ('B4', 'P0', 'H'):
            rows = [r for r in fault_rows if r.get('method') == method and r.get('expected_invalid') is True]
            detector_breakdown[method] = None if not rows else dict(
                invalid_faults=len(rows),
                compiler_rejection=sum((r.get('validator_detection') or {}).get('compiler_rejected') is True for r in rows) if method != 'B4' else None,
                native_validator=sum((r.get('validator_detection') or {}).get('native_validator_called') is True and (r.get('validator_detection') or {}).get('invalid') is True for r in rows) if method != 'B4' else None,
                validator_treatment_applicable=method != 'B4',
                llm_review=sum(r.get('review_invalid') is True for r in rows) if method != 'P0' else None,
                predicted_invalid=sum(r.get('predicted_invalid') is True for r in rows))
        scope = protocol.get('approved_scope_partition', {})
        query_by_id = {q['case_id']: q for q in queries}
        cases = []
        for contract in contracts:
            cid = contract.get('case_id')
            query = query_by_id.get(cid, {})
            stratum = ('OUT_OF_COVERAGE_SAFE_ABSTENTION' if cid in scope.get('out_of_coverage_safe_abstention', [])
                       else 'MISSING_INPUT' if cid in scope.get('missing_input', [])
                       else 'IN_SNAPSHOT_SPATIAL' if cid in scope.get('in_snapshot', [])
                       else 'SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4')
            spatial_gold = contract.get('spatial_gold')
            spatial_reference = contract.get('spatial_reference')
            has_gold = isinstance(spatial_gold, dict) or isinstance(spatial_reference, dict)
            if isinstance(spatial_reference, dict) and 'object_ids' in spatial_reference:
                stratum = 'SOURCE_BOUND_CORPUS_SPATIAL'
            elif stratum == 'SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4':
                stratum = 'SOURCE_BOUND_DOCUMENT_EVIDENCE'
            gold_summary = {}
            for family, gold in (spatial_gold or {}).items():
                if isinstance(gold, dict):
                    gold_summary[family] = {k: gold.get(k) for k in ('object_ids', 'source_snapshot_sha256', 'evidence_per_object_required')}
                    gold_summary[family]['object_count'] = len(gold['object_ids']) if isinstance(gold.get('object_ids'), list) else None
            reference_summary = {k:v for k,v in (spatial_reference or {}).items() if k not in ('objects', 'geometry', 'geometry_ewkb', 'geometry_wkt')}
            case = {k: contract.get(k) for k in ('case_id', 'query', 'category', 'equivalence_group',
                    'required_task_obligations', 'required_qec_fields', 'machine_checks', 'source_provenance',
                    'scope_notes', 'holdout_eligible', 'spatial_object_scoring_enabled')}
            case.update(language=query.get('language'), evaluation_stratum=stratum,
                        source_evaluation_stratum=contract.get('evaluation_stratum'),
                        spatial_gold_available=has_gold,
                        spatial_correctness_applicable=contract.get('spatial_correctness_applicable', contract.get('spatial_object_scoring_enabled')),
                        spatial_gold_summary=gold_summary, spatial_reference_summary=reference_summary,
                        reference_geometry_identity={k:v for k,v in (contract.get('reference_geometry') or {}).items()
                                                     if k not in ('geometry_ewkb', 'geometry_wkt', 'geometry', 'coordinates')},
                        coverage_reference=contract.get('coverage_reference'),
                        spatial_predicate=contract.get('spatial_predicate'),
                        safe_abstention_expected=stratum == 'OUT_OF_COVERAGE_SAFE_ABSTENTION',
                        human_gold_status='USER_CONFIRMED_COMPLETE' if approval_valid else 'COMPLETE' if contract.get('independent_expert_review') is True else 'NOT_READY',
                        results=[self.compact_row(r) for r in comparison if r.get('case_id') == cid])
            cases.append(case)
        methods = []
        for mid in manifest.get('methods', []):
            metrics = overall.get(mid, {})
            methods.append(dict(id=mid, name=protocol.get('methods', {}).get(mid, mid),
                                observations=metrics.get('observations'), metrics=metrics, costs=metrics.get('costs', {}),
                                shared_artifacts=[self.compact_row(r) for r in comparison if r.get('method') == mid],
                                spatial_comparison_note='도구 없는 기준선: 공간 실패 순위로 해석하지 않음' if mid in ('B0','B1','B2') else None))
        registry = self.load('reliability/reliability_case_registry.yaml', {})
        audit = self.load('reliability/reliability_gap_audit.json', {})
        audit_by_id = {c['case_id']: c for c in audit.get('cases', [])}
        reliability = dict(cases=[dict(c, audit=audit_by_id.get(c.get('case_id'))) for c in registry.get('cases', [])],
                           audit={k:v for k,v in audit.items() if k != 'cases'})
        self.load('reliability/RELIABILITY_DECISION_MATRIX.md', '')
        self.load('reliability/IMPLEMENTATION_GAP_AUDIT.md', '')
        limits = ['관측 완료는 논문 검증 완료가 아닙니다.', '기계 계약 검사는 독립 인간 의미 정확도가 아닙니다.',
                  'Q4 동등 표현은 독립 공간 문제로 합산하지 않습니다.', '범위 밖 자료는 실세계 0건을 뜻하지 않습니다.',
                  '현재 완료 인용 대상은 RESULTS_INDEX의 최신 완료 행을 따릅니다. 진행 중 실험은 별도 표시합니다.',
                  '정책·구현 감사는 기록 시점 자료이며 이후 운영 수정 완료를 자동 의미하지 않습니다.']
        limits += ['원본 실험 당시: ' + str(x) for x in selected_manifest.get('limits', [])]
        overview = dict(selected_run_id=selected, latest_run_id=runs[0]['run_id'] if runs else None,
                        case_count=manifest.get('case_count'), method_count=len(manifest['methods']) if 'methods' in manifest else None,
                        observed_rows=summary.get('observed_rows'), expected_observations=summary.get('expected_observations'),
                        fault_rows=summary.get('rq2_fault_comparison', {}).get('rows'),
                        benchmark_freeze_complete=(manifest.get('benchmark_freeze_complete') is True and all(c['verified'] for c in freeze_checks)) if freeze_checks else None,
                        independent_expert_review_complete=True if approval_valid else manifest.get('independent_expert_review_complete'),
                        historical_independent_expert_review_complete=manifest.get('independent_expert_review_complete'),
                        review_approval=approval if approval_valid else None,
                        holdout_count=sum(c.get('holdout_eligible') is True for c in contracts) if contracts else None,
                        repeats=selected_status.get('repeats'), scientific_completion=summary.get('scientific_completion'),
                        completion_gate=summary.get('completion_gate', {}),
                        status='OBSERVATION_COMPLETE' if selected_info.get('can_be_cited') else 'UNAVAILABLE_LOCAL_ARTIFACT')
        result = dict(holdout=holdout, semantic_review=semantic_review, rescore=rescore, overview=overview, benchmark=dict(manifest=manifest, freeze_checks=freeze_checks, cases=cases,
                      categories=dict(Counter(c.get('category') for c in cases)), protocol=protocol), methods=methods,
                      rq={'1':dict(status='NOT_FINAL', by_method_query_condition=summary.get('by_method_query_condition', {})),
                          '2':dict(status=fault.get('status', 'NOT_MEASURED'), overall_by_method=fault.get('overall_by_method', {}), by_method_error_type=fault.get('by_method_error_type', {}), detector_breakdown=detector_breakdown, model_digests=selected_info.get('model_digest')),
                          '3':dict(status='PILOT_ONLY' if overall else 'NOT_MEASURED', overall_by_method=overall, equivalence_group_warning=summary.get('equivalence_group_warning')),
                          '4':dict(status=fault.get('status', 'NOT_MEASURED'), overall_by_method=fault.get('overall_by_method', {})),
                          '5':dict(status='OBSERVED_COST_ONLY' if overall else 'NOT_MEASURED', overall_by_method=overall)},
                      reliability=reliability, runs=runs, limitations=limits, sources=list(self.sources.values()),
                      generated_at=self.generated, status=overview['status'])
        return result
