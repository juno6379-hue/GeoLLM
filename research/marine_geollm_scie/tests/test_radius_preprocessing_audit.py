from research.marine_geollm_scie.fault_injection.radius_preprocessing_audit import compare_case


def test_invalid_feature_is_rejected_upstream_but_generic_gate_accepts_string():
    row = compare_case("invalid_feature")
    assert row["select_targets"]["code"] == "UNSUPPORTED_TARGET"
    assert row["prepare_radius_request"]["status"] == "REJECTED"
    assert row["direct_generic_validator"]["authorized"] is True


def test_crs_rejection_is_preprocessing_not_generic_gate():
    row = compare_case("invalid_crs")
    assert row["prepare_radius_request"]["status"] == "REJECTED"
    assert row["direct_generic_validator"]["authorized"] is True


def test_fixed_radius_preparation_does_not_preserve_conflicting_operator():
    row = compare_case("operator_mismatch")
    assert row["prepare_radius_request"]["status"] == "RETURNED"
    assert row["prepare_radius_request"]["spatial_relation_preserved"] is False
    assert row["prepare_radius_request"]["operation"] == "feature_search_by_radius"
    assert row["unsafe_execution_demonstrated"] is False
