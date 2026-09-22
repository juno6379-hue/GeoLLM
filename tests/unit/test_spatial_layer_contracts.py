from scripts.validate_spatial_layer_contracts import load_layers, validate_registry


def test_executable_spatial_layer_registry_contracts_are_complete():
    layers = load_layers()
    issues = validate_registry(layers)
    assert issues == []
    assert any(layer.get("execution_status") == "executable" for layer in layers.values())


def test_registry_validator_rejects_unsafe_executable_layer():
    issues = validate_registry({"test:bad": {"execution_status": "executable", "physical_table": "bad"}})
    codes = {issue["code"] for issue in issues}
    assert "INVALID_PHYSICAL_TABLE" in codes
    assert "MISSING_SUPPORTED_OPERATIONS" in codes
    assert "MISSING_GEOMETRY_COLUMN" in codes