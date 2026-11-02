import copy
import pytest
from tools.scie_results_ui.prepare_semantic_review import DIMENSIONS, empty_label, validate_labels, summarize_labels, digest


def fixture():
    items=[dict(answer_id='ANSWER_001',answer_sha256='answer',gold_manifest_sha256='gold')]
    mapping=[dict(answer_id='ANSWER_001',method='P1')]
    a=empty_label(items[0],'AAA');b=empty_label(items[0],'BBB')
    return items,mapping,a,b


def complete(x):
    return dict(x,human_completed=True,independent_review_confirmed=True,reviewed_at='2026-11-02',
        dimensions=dict.fromkeys(DIMENSIONS,True),rationale='실제 답안의 필수 내용과 출처를 대조함',
        answer_evidence_quote='답안에서 인용',gold_evidence_locator='GOLD source locator',human_label_source='검수자 본인 작성 기록')


def test_gold_approval_never_becomes_answer_score():
    items,m,a,b=fixture();s=summarize_labels(items,[a],[b],[],m)
    assert s['gold_review_complete'] is True
    assert s['semantic_human_accuracy'] is None
    assert s['reviewer_A_completed']==s['consensus_completed']==0


def test_complete_pair_still_needs_bound_consensus():
    items,m,a,b=fixture();a=complete(a);b=complete(b)
    s=summarize_labels(items,[a],[b],[],m)
    assert s['paired_completed']==1 and s['semantic_human_accuracy'] is None
    c=complete(empty_label(items[0],'AAA+BBB'))
    c.update(reviewer_A_label_sha256=digest(a),reviewer_B_label_sha256=digest(b))
    s=summarize_labels(items,[a],[b],[c],m)
    assert s['human_answer_scoring_complete'] is True
    assert s['semantic_human_accuracy']==1 and s['agreement']['cohen_kappa'] is None


@pytest.mark.parametrize('field,value',[('author_type','AI'),('reviewer','BBB'),('answer_sha256','wrong'),
    ('gold_manifest_sha256','wrong'),('independent_review_confirmed',False),('rationale',''),('human_label_source','')])
def test_invalid_human_submission_rejected(field,value):
    items,m,a,b=fixture();a=complete(a);a[field]=value
    with pytest.raises(ValueError):validate_labels([a],items,'AAA')


def test_duplicate_and_nonboolean_rejected():
    items,m,a,b=fixture();a=complete(a)
    with pytest.raises(ValueError):validate_labels([a,a],items,'AAA')
    a['dimensions']['meaning_correct']='true'
    with pytest.raises(ValueError):validate_labels([a],items,'AAA')


def test_consensus_cannot_overwrite_independent_disagreement():
    items,m,a,b=fixture();a=complete(a);b=complete(b);b['dimensions']['meaning_correct']=False
    c=complete(empty_label(items[0],'AAA+BBB'));c.update(reviewer_A_label_sha256=digest(a),reviewer_B_label_sha256=digest(b))
    s=summarize_labels(items,[a],[b],[c],m)
    assert s['semantic_human_accuracy']==1
    assert s['agreement']['binary_agreements']==0
    c['reviewer_B_label_sha256']='not submitted b'
    with pytest.raises(ValueError):summarize_labels(items,[a],[b],[c],m)


def test_markdown_label_import(tmp_path):
    import json
    from tools.scie_results_ui.prepare_semantic_review import markdown_labels
    items,m,a,b=fixture();p=tmp_path/'review.md'
    p.write_text('## answer\n```human-label\n'+json.dumps(a)+'\n```\n',encoding='utf-8')
    assert markdown_labels(p)==[a]


def test_current_gold_mismatch_rejected(tmp_path,monkeypatch):
    import json
    import tools.scie_results_ui.prepare_semantic_review as mod
    package=tmp_path/'pack';gold=tmp_path/'gold';package.mkdir();gold.mkdir()
    (gold/'manifest.json').write_text('{}',encoding='utf-8')
    (package/'manifest.json').write_text(json.dumps({'gold_manifest_sha256':'old','files':{}}),encoding='utf-8')
    monkeypatch.setattr(mod,'OUT',package);monkeypatch.setattr(mod,'GOLD',gold)
    with pytest.raises(ValueError,match='Pinned GOLD changed'):mod.validate_package()


def test_ui_publication_rejects_outside_review(tmp_path):
    from tools.scie_results_ui.prepare_semantic_review import publish_ui
    with pytest.raises(ValueError,match='inside research/review'):publish_ui(tmp_path)


def test_display_deduplicates_not_prose():
    from tools.scie_results_ui.prepare_semantic_review import display_projection
    doc={'features':[{'code':'Wreck'}]}
    raw={'answer_text':'Unsupported prose must remain','document_answer':doc,'document_answers':[doc],
         'tool_receipts':[{'huge':'source copy'}],'geometry':'blob','returned_object_ids':['id1']}
    out=display_projection(raw)
    assert out['answer_text']==raw['answer_text']
    assert out['document_answer']==doc and 'document_answers' not in out
    assert out['returned_object_ids']==['id1']
