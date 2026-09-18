from scripts.run_external_evidence_gap_fill import (
    DEFAULT_REGISTRY,
    detect_gap_domain,
    load_yaml,
    osm_supplemental_candidates,
    promotion_candidates,
    run_gap_fill,
)


QUERY = "\ub3c5\ub3c4 \ubd80\uadfc \ucc9c\uc5f0\ubcf4\ud638\uad6c\uc5ed\uc744 \ucc3e\uc544\uc918"


def test_detects_natural_heritage_gap_domain():
    registry = load_yaml(DEFAULT_REGISTRY)
    domain = detect_gap_domain(QUERY, registry)
    assert domain is not None
    assert domain["domain_id"] == "natural_heritage_protected_area"


def test_dokdo_natural_heritage_gap_fill_candidates_are_review_gated():
    report = run_gap_fill(QUERY, check_db=False)

    assert report["status"] == "OK"
    assert report["anchor"]["place_id"] == "dokdo"
    assert report["local_gap_confirmed"] is False
    assert report["external_candidate_generation_allowed"] is True

    public_candidates = [
        row for row in report["candidates"]
        if row["authority_level"] == "public_authoritative"
    ]
    assert public_candidates
    assert public_candidates[0]["name"] == "\ub3c5\ub3c4 \ucc9c\uc5f0\ubcf4\ud638\uad6c\uc5ed"
    assert public_candidates[0]["review_required"] is True
    assert public_candidates[0]["promotion_status"] == "NEEDS_GEOMETRY_REVIEW"

    supplemental = [
        row for row in report["candidates"]
        if row["authority_level"] == "supplemental"
    ]
    assert supplemental
    assert supplemental[0]["promotion_status"] == "SUPPLEMENTAL_ONLY_NOT_PROMOTABLE"


def test_promotion_candidates_require_geometry_review():
    report = run_gap_fill(QUERY, check_db=False)
    promotions = promotion_candidates(report["candidates"])

    assert promotions
    assert promotions[0]["promotion_status"] == "NEEDS_GEOMETRY_REVIEW"
    assert "official_polygon_or_boundary_review" in promotions[0]["required_reviews"]


def test_osm_live_fetch_requires_explicit_user_agent(monkeypatch):
    monkeypatch.delenv("GEOLLM_OSM_USER_AGENT", raising=False)
    report = run_gap_fill(QUERY, fetch_osm=True)

    assert report["osm_fetch_diagnostics"]["status"] == "blocked"
    assert "GEOLLM_OSM_USER_AGENT" in report["osm_fetch_diagnostics"]["reason"]


def test_osm_static_candidate_is_supplemental_only():
    registry = load_yaml(DEFAULT_REGISTRY)
    domain = detect_gap_domain(QUERY, registry)
    rows = osm_supplemental_candidates(
        "query",
        "natural_heritage_protected_area",
        {"canonical_name": "Dokdo"},
        domain,
    )

    assert rows
    assert rows[0]["authority_level"] == "supplemental"
    assert rows[0]["promotion_status"] == "SUPPLEMENTAL_ONLY_NOT_PROMOTABLE"


def test_ollama_review_is_skipped_by_default():
    report = run_gap_fill(QUERY)

    assert report["ollama_ambiguity_review"]["enabled"] is False
    assert report["ollama_ambiguity_review"]["status"] == "skipped"
