from research.marine_geollm_scie.fault_injection.coverage_pilot import SPECS, diagnose


def case(name): return diagnose(*next(spec for spec in SPECS if spec[0] == name))


def test_unrepresentable_unit_and_generic_attribute_are_explicitly_unsupported():
    assert case("missing_unit")["status"] == "NOT_SUPPORTED"
    assert case("invalid_attribute")["predicted_invalid"] is None


def test_l3_slot_mutation_revokes_old_receipt_and_requires_fresh_validation():
    row = case("postapproval_distance")
    assert row["receipt_authorized_without_revalidation"] is False
    assert row["predicted_invalid"] is True


def test_external_registry_change_is_not_conflated_with_input_hash_mutation():
    row = case("tool_removed_after_approval")
    assert row["receipt_authorized_without_revalidation"] is True
    assert row["predicted_invalid"] is True
    assert any(issue["code"] == "TOOL_NOT_REGISTERED" for issue in row["typed_issues"])


def test_schema_fault_is_diagnostic_not_successful_gis_execution():
    row = case("schema_changed_after_approval")
    assert row["predicted_invalid"] is True
    assert row["execution_success"] is None and row["spatial_correct"] is None
