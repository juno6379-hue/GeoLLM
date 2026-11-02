"""All rows of a named inventory are not all objects in the real world."""
from unittest.mock import Mock

import pytest

from services.orchestrator.spatial_coverage import requests_source_corpus, assess_source_corpus
from tests.unit.test_s101_source_corpus import request, fixture
from services.orchestrator.s101_corpus import verify_s101_corpus


@pytest.mark.parametrize('query', [
    '2022 CSV에 수록된 모든 해양지명을 찾아줘',
    '현재 원천 목록에 등록된 모든 Wreck를 반경 1000m에서 찾아줘',
    'Find all Wrecks in the registered dataset within 1000m',
    'Find every Wreck in the pinned corpus within 1km',
    '2022 CSV에 수록된 독도 주변 5km 이내의 모든 해양지명을 찾아줘.',
    '현재 원천 목록에 등록된 부산항 주변 반경 1.5km 이내의 모든 Wreck를 찾아줘.',
    '2022 CSV에 수록된 독도 부근 모든 해양지명을 찾아줘',
])
def test_explicit_finite_membership_can_request_all_rows(query):
    assert requests_source_corpus(request(query))


@pytest.mark.parametrize('query', [
    '모든 침선을 빠짐없이 찾아줘',
    '자료에서 모든 침선을 빠짐없이 찾아줘',
    '현재 원천 목록에 등록된 모든 Wreck와 실세계의 모든 침선을 찾아줘',
    'Find all real-world Wrecks in the registered dataset',
    '현재 원천 목록에 등록된 모든 Wreck 중 가장 가까운 것을 찾아줘',
    'Find the nearest Wreck in the registered dataset',
    '2022 CSV에 수록된 모든 해양지명과 실제 해역 전체의 지명을 찾아줘',
    '2022 CSV에 수록된 해양지명은 설명하고 부산항의 모든 침선을 찾아줘',
    'Find all Wrecks near Busan; also explain names in the registered dataset',
    'Find all Wrecks in the registered dataset and all objects outside it',
    '2022 CSV에 수록된 해양지명을 참고해 부산항의 모든 침선을 찾아줘',
    '2022 CSV에 수록된 해양지명을참고해부산항주변 모든 침선을 찾아줘',
])
def test_world_or_nearest_and_vague_inventory_are_not_narrowed(query):
    assert not requests_source_corpus(request(query), registered_default=True)


def test_explicit_exhaustiveness_still_requires_full_source_identity(tmp_path):
    contract, registry, cursor, _ = fixture(tmp_path)
    qec = request('현재 원천 목록에 등록된 모든 Wreck를 반경 1000m에서 찾아줘')
    verifier = lambda binding, c: verify_s101_corpus(cursor, binding, c, root=tmp_path)
    receipt = assess_source_corpus(qec, registry, verifier)
    assert receipt['status'] == 'CORPUS_VERIFIED'
    assert receipt['source_corpus_status'] == 'VERIFIED'
    assert receipt['real_world_completeness'] == 'UNKNOWN'
    assert receipt['absence_certified'] is False
    cursor.fetchall.return_value[0]['attributes'] = {'changed': True}
    assert assess_source_corpus(qec, registry, verifier) is None


def test_explicit_source_words_do_not_create_a_registry_contract(tmp_path):
    _, registry, _, _ = fixture(tmp_path)
    registry['layers']['GBENC_S101_feature'].pop('corpus_contract')
    verifier = Mock()
    assert assess_source_corpus(request('Find all Wrecks in the registered dataset'), registry, verifier) is None
    verifier.assert_not_called()


def test_explicit_source_words_do_not_fill_missing_geometry_or_override_global_flag(tmp_path):
    _, registry, _, _ = fixture(tmp_path)
    qec=request('현재 원천 목록에 등록된 모든 Wreck를 찾아줘')
    qec.slots.reference_geometry=None
    verifier=Mock()
    assert assess_source_corpus(qec,registry,verifier) is None
    verifier.assert_not_called()
    qec=request('현재 원천 목록에 등록된 모든 Wreck를 찾아줘')
    qec.slots.filters['require_complete_coverage']=True
    assert not requests_source_corpus(qec,registered_default=True)
