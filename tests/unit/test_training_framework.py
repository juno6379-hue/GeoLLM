import copy

import pytest
from pydantic import ValidationError

from training.framework import expand_approved_seeds
from training.models import TrainingCase
from training.pipeline import read_jsonl


def seed():
    return read_jsonl(__import__("pathlib").Path("training/seeds/canonical_seeds.jsonl"))[0]


def test_canonical_seed_is_valid():
    assert TrainingCase.model_validate(seed()).case_id == "MGEO-SEED-0001"


def test_missing_required_slot_cannot_be_execution_ready():
    row = copy.deepcopy(seed())
    row["expected_slots"]["location_text"]["value"] = None
    with pytest.raises(ValidationError):
        TrainingCase.model_validate(row)


def test_dynamic_reference_answer_requires_frozen_fixture():
    row = copy.deepcopy(seed())
    row["expected_answer"]["reference_answer"] = "3건입니다."
    with pytest.raises(ValidationError):
        TrainingCase.model_validate(row)


def test_expansion_ids_are_unique_per_seed_family():
    first = seed()
    second = copy.deepcopy(first)
    second["case_id"] = "MGEO-SEED-NAV-999"
    candidates = expand_approved_seeds([first, second], limit=3)
    assert len({row["case_id"] for row in candidates}) == len(candidates)
    assert all(row["review_status"] == "CANDIDATE" for row in candidates)
