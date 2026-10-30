import pytest
from research.marine_geollm_scie.runners.dokdo_spatial_reference import dms, coordinate_pair, vincenty


def test_coordinate_formats_and_exact_carry():
    assert dms('131-52-10.4E',False) == pytest.approx(131.86955555555556)
    assert dms('37°14\'26.8"N',True) == pytest.approx(37.24077777777778)
    assert dms('126-47-60E',False) == pytest.approx(126.8)
    assert dms('36-59.64-N',True) == pytest.approx(36.994)
    assert dms('36°59.64′N',True) == pytest.approx(36.994)
    with pytest.raises(ValueError):dms('38°25\'48.27\'\'',True)
    with pytest.raises(ValueError):dms('131-52-10E',True)


def test_source_fallback_is_recorded_and_disagreement_rejected():
    value,trace=coordinate_pair('35-31.0-00N3','35˚31.0´00˝N',True)
    assert value == pytest.approx(35+31/60)
    assert trace['selected_field']=='field2' and trace['parse_warnings']
    with pytest.raises(ValueError,match='disagree'):
        coordinate_pair('35-31-00N','35-32-00N',True)


def test_wgs84_geodesic_known_equatorial_and_reciprocal_distance():
    assert vincenty(0,0,0,1) == pytest.approx(111319.490793,abs=.001)
    assert vincenty(37.2,131.8,37.2,131.8) == 0
    a=vincenty(37.24077777777778,131.86955555555556,37.24944444444444,131.8661111111111)
    b=vincenty(37.24944444444444,131.8661111111111,37.24077777777778,131.86955555555556)
    assert a==pytest.approx(b,abs=.001)
