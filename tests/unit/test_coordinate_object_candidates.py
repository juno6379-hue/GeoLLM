import numpy as np
import pytest
from scripts.audit_coordinate_object_candidates import point, distances


@pytest.mark.parametrize('coords', [[35, 129], [float('nan'), 35], [190, 35], [129], [None, 35]])
def test_invalid_or_swapped_axis_point_is_excluded(coords):
    assert point({'geojson': {'type': 'Point', 'coordinates': coords}}) is None


def test_distance_is_only_a_numerical_candidate_filter():
    result = distances(129, 35, np.array([[129, 35], [130, 35]]))
    assert result[0] == 0
    assert result[1] > 80000


def test_polygon_is_not_silently_replaced_by_centroid():
    assert point({'geojson': {'type': 'Polygon', 'coordinates': []}}) is None
