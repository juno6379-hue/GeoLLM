from scripts.run_external_evidence_gap_fill import (
    DEFAULT_REGISTRY,
    detect_gap_domain,
    load_yaml,
    promotion_candidates,
    run_gap_fill,
)


def test_detects_natural_heritage_gap_domain():
    registry = load_yaml(DEFAULT_REGISTRY)
    domain = detect_gap_domain("독도 부근 천연보호구역을 찾아줘", registry)
    assert domain is not None
    assert domain["domain_id"] == "natural_heritage_protected_area"


def test_dokdo_natural_heritage_gap_fill_candidates_are_review_gated():
    report = run_gap_fill("독도 부근 천연보호구역을 찾아줘", check_db=False)

    assert report["status"] == "OK"
    assert report["anchor"]["place_id"] == "dokdo"
    assert report["local_gap_confirmed"] is False
    assert report["external_candidate_generation_allowed"] is True

    public_candidates = [
        row for row in report["candidates"]
        if row["authority_level"] == "public_authoritative"
    ]
    assert public_candidates
    assert public_candidates[0]["name"] == "독도 천연보호구역"
    assert public_candidates[0]["review_required"] is True
    assert public_candidates[0]["promotion_status"] == "NEEDS_GEOMETRY_REVIEW"

    supplemental = [
        row for row in report["candidates"]
        if row["authority_level"] == "supplemental"
    ]
    assert supplemental
    assert supplemental[0]["promotion_status"] == "SUPPLEMENTAL_ONLY_NOT_PROMOTABLE"


def test_promotion_candidates_require_geometry_review():
    report = run_gap_fill("독도 부근 천연보호구역을 찾아줘", check_db=False)
    promotions = promotion_candidates(report["candidates"])

    assert promotions
    assert promotions[0]["promotion_status"] == "NEEDS_GEOMETRY_REVIEW"
    assert "official_polygon_or_boundary_review" in promotions[0]["required_reviews"]
