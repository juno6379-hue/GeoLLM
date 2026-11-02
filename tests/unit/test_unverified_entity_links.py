from scripts.audit_unverified_entity_links import disposition


def test_named_heading_support_not_arbitrary_nearby_name():
    assert disposition(('다른항 정보\n3.6.2 국도항\n(', ''), ['국도항'])[0] == 'SOURCE_NAMED_REFERENT_SUPPORTED_CRS_PENDING'
    assert disposition(('국도항 근처의 정박지 (', ''), ['국도항'])[0] == 'NAME_OR_REFERENT_UNRESOLVED'


def test_anchorage_not_port_identity():
    assert disposition(('하동항 (5) 정박구역 (항계내)', ''), ['하동항'])[0] == 'DIFFERENT_REFERENT_ANCHORAGE_CENTRE'
    assert disposition(('<Inside harbor limit> circle radius of 270m ', ''), ['하동항'])[0] == 'DIFFERENT_REFERENT_ANCHORAGE_CENTRE'


def test_nearby_reef_not_harbour():
    assert disposition(('7.2.5 군산항(群山港)\n(', ''), ['민야암'])[0] == 'HEADING_AND_CANDIDATE_NAME_NOT_IDENTICAL'


def test_alias_not_inferred():
    assert disposition(('2.5.4 울릉항(鬱陵港)\n(', ''), ['울릉항(사동)', '사동항'])[0] == 'HEADING_AND_CANDIDATE_NAME_NOT_IDENTICAL'
