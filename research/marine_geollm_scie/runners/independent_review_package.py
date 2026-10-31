"""Blank independent GOLD review forms; existing AI reference is separate and labelled."""
import argparse
import hashlib
import json
from pathlib import Path


def build(contracts_path, output):
    contracts_path, output = Path(contracts_path), Path(output)
    if output.exists():
        raise FileExistsError('New review package required')
    refs = [json.loads(x) for x in contracts_path.read_text(encoding='utf-8').splitlines() if x.strip()]
    if len(refs) != 18 or len({r['case_id'] for r in refs}) != 18:
        raise ValueError('18 unique reference cases required')
    output.mkdir(parents=True)
    digest = hashlib.sha256(contracts_path.read_bytes()).hexdigest()
    questions, candidates = [], []
    for r in refs:
        scope = r.get('document_scope') or {}
        evidence = scope.get('evidence_requirements') or {}
        # Feature-specific locators reveal the AI candidate's selected classes.
        # Initial judgement receives only whole-source identity; full locators
        # remain available in the explicitly separate AI candidate file.
        source_identity = {k: evidence[k] for k in ('edition', 'source_path', 'source_sha256') if k in evidence}
        if source_identity:
            source_identity['review_scope'] = 'WHOLE_SOURCE_NO_PRESELECTED_FEATURE_LOCATORS'
        spatial = r.get('spatial_reference') or {}
        # Initial independent judgement must not see AI-calculated answer IDs.
        spatial_source = {k: spatial[k] for k in ('dataset_snapshot_sha256', 'reference_geometry_source',
            'reference_crs', 'distance_policy', 'crs_policy', 'scope') if k in spatial}
        # Resolve the actual source by hash, without exposing computed answer IDs.
        if spatial_source.get('dataset_snapshot_sha256'):
            dataset = Path(__file__).resolve().parents[3]/'Dataset'
            for candidate in dataset.glob('*.csv'):
                if hashlib.sha256(candidate.read_bytes()).hexdigest() == spatial_source['dataset_snapshot_sha256']:
                    spatial_source['dataset_source_path'] = str(candidate.resolve())
                    break
        questions.append({'case_id': r['case_id'], 'query': r['query'], 'equivalence_group': r['equivalence_group'],
            'source_references': source_identity or None, 'spatial_source_condition': spatial_source or None,
            'original_contract_sha256': digest, 'model_outputs_shown': False})
        candidates.append({'case_id': r['case_id'], 'provenance_label': 'AI_AGENT_FINALIZED_NOT_INDEPENDENT_HUMAN_GOLD',
            'independent_human_review': False, 'candidate_contract': r})
    def jsonl(name, rows):
        (output/name).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')
    jsonl('questions_and_sources.jsonl', questions)
    jsonl('AI_reference_candidates_separate.jsonl', candidates)
    for reviewer in ('A', 'B'):
        blank = [{**q, 'reviewer_role': reviewer, 'reviewer_name': None, 'reviewed_at': None,
            'review_status': 'NOT_REVIEWED', 'independence_attested': None,
            'required_tasks': None, 'acceptable_answers': None, 'required_evidence': None,
            'spatial_oracle_or_missingness': None, 'clarification_required': None,
            'source_checked': None, 'source_locators_used': None, 'reason': None,
            'ai_candidates_seen_before_initial_judgement': None, 'human_approval': False} for q in questions]
        jsonl(f'reviewer_{reviewer}_blank.jsonl', blank)
        lines = [f'# 독립 검수자 {reviewer} — 18문항 빈 양식', '',
            '검수자 이름: ______  검수 일시: ______  독립 검수 확인: ______',
            '모델 출력과 상대 검수자 판단을 보지 않고 작성하십시오. 초기 판단용 출처에는 AI가 선택한 객체별 locator를 제공하지 않습니다. AI 후보는 초기 판단을 저장한 뒤 별도 대조합니다.', '']
        for q in questions:
            lines += [f"## {q['case_id']} — {q['query']}", '',
                '출처 및 고정 입력 조건:', '```json', json.dumps({k: q[k] for k in ('source_references', 'spatial_source_condition')}, ensure_ascii=False, indent=2), '```', '',
                '- 필수 작업: ______', '- 허용 답안과 대안: ______', '- 반드시 포함할 근거: ______',
                '- 공간 정답 또는 미확정 사유: ______', '- 추가 입력 필요 여부와 이유: ______',
                '- 실제 확인한 출처·위치(locator): ______', '- AI 후보를 초기 판단 전에 보았는지: ______',
                '- 판단 및 근거: ______', '- 검수자·검수 일시·승인 여부: ______', '']
        (output/f'검수자{reviewer}_18문항_독립검수_빈양식_KR.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    jsonl('adjudication_blank.jsonl', [{'case_id': q['case_id'], 'query': q['query'],
        'reviewer_A_record_sha256': None, 'reviewer_B_record_sha256': None,
        'disagreement': None, 'resolved_contract': None, 'adjudicator': None, 'adjudicated_at': None,
        'source_checked': None, 'reason': None, 'review_status': 'NOT_REVIEWED',
        'independent_human_review': False, 'human_approval': False} for q in questions])
    lines = ['# 독립 검수 합의 — 18문항 빈 양식', '', 'A·B 개별 판단을 보존한 뒤 작성합니다. 불일치가 없더라도 출처 확인과 합의자 서명을 기록합니다.', '']
    for q in questions:
        lines += [f"## {q['case_id']} — {q['query']}", '', '- A 검수 기록 및 해시: ______',
            '- B 검수 기록 및 해시: ______', '- 불일치 항목: ______', '- 확정 답안·허용 대안·필수 근거: ______',
            '- 출처 확인 결과 및 해결 이유: ______', '- 합의자·일시·승인 여부: ______', '']
    (output/'합의검토_18문항_독립검수_빈양식_KR.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    lines = ['# 독립 GOLD 검수 18문항', '',
        '검수자는 사용자가 선정했다고 확인했습니다. 이 패키지는 빈 양식이며 검수 완료·승인이 아닙니다.',
        'A와 B는 서로의 판단과 모델 출력을 보지 않고 원문 질의와 출처부터 확인합니다. AI 후보는 별도 파일이며 초기 독립 판단을 기록한 뒤 대조하십시오.',
        '초기 판단 양식은 원천 전체의 경로·해시·판만 제공합니다. 특정 객체별 locator와 AI 정답 선택은 별도 후보 파일에만 있습니다. 초기 독립 답안 작성과 기존 AI 후보의 사후 검증을 구분해 기록하십시오.',
        '동등표현 Q4 세 문항은 같은 공간조건 군집입니다. 미확정 공간 범위·AOI·원천 coverage는 임의 정답으로 채우지 말고 미확정 사유를 기록합니다.',
        'A/B JSONL에 검수자·일시·독립성·필수작업·허용답안·근거·clarification 필요성을 작성하고, 합의 파일에 불일치와 해결 근거를 남깁니다.',
        '기존 파일의 human_approval을 자동 True로 바꾸지 않습니다. 제출본은 원본 hash와 함께 새 참조 버전으로 반영하고 이전 AI 참조를 보존합니다.',
        '이 18문항은 이미 개발에 사용했습니다. 독립 검수 후에도 미노출 holdout으로 표시하지 않습니다.', '',
        '## 질문 목록', '']
    lines += [f"{i}. **{q['case_id']}** — {q['query']}" for i, q in enumerate(questions, 1)]
    (output/'검수안내_KR.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    manifest = {'status': 'AWAITING_INDEPENDENT_REVIEW', 'reviewers_assigned_user_confirmed': True,
        'independent_reviews_completed': 0, 'rows': 18, 'source_contract_sha256': digest,
        'model_outputs_in_review_forms': False, 'human_approval': False,
        'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--contracts', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); build(a.contracts, a.output)
