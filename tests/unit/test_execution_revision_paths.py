"""Request revision survives creation of new lookup/place execution contracts."""
from services.orchestrator import execution_validator as validator
from shared.schemas.agent import QueryExecutionContext

def test_place_resolution_preserves_revision_on_blocked_path():
    qec = validator.validate_place_resolution("미확인항 위치", {"status": "NEEDS_CLARIFICATION"},
                                              task_id="same-task", revision=4)
    assert qec.revision == 4
    assert qec.provenance["execution_validation"]

def test_lookup_creation_does_not_reuse_revision_one(monkeypatch):
    monkeypatch.setattr(validator, "validate_execution_context", lambda qec, **kw: qec)
    qec = validator.validate_lookup_request({"task_id": "resumed", "query": "문서 검색",
                                            "execution_revision": 3}, "dataset_source_lookup")
    assert qec.revision == 3
    assert not qec.provenance.get("execution_validation")
