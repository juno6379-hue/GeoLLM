import pytest

from services.orchestrator.fast_path_policy import instant_place_navigation_decision


@pytest.mark.parametrize('query', [
    '부산 가장 가까운 항만', '인천항에서 가장 가까운 항만으로 이동',
    'show the nearest harbour', '항로 안전성 분석',
])
def test_relations_and_analysis_do_not_become_literal_place_names(query):
    assert instant_place_navigation_decision(query)['allowed'] is False


def test_normal_harbour_navigation_still_allowed():
    assert instant_place_navigation_decision('인천항으로 이동')['allowed'] is True
