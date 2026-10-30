from pathlib import Path

import pytest

from research.marine_geollm_scie.runners.condition_metadata import build_metadata

BENCHMARK=Path(__file__).resolve().parents[1]/'benchmark/query_cases_v1.jsonl'


def test_metadata_is_posthoc_not_gold_or_holdout():
    before=BENCHMARK.read_bytes()
    rows=build_metadata(BENCHMARK)
    assert len(rows)==18 and len({r['case_id'] for r in rows})==18
    assert all(r['post_hoc'] and r['exposed_pilot'] and not r['holdout_eligible'] for r in rows)
    assert all(r['annotation_status']=='DRAFT' and not r['human_approval'] for r in rows)
    assert sum(r['information_availability']==['REFERENCE_GEOMETRY_MISSING'] for r in rows)==1
    assert not any('DATA_COMPLETE' in r['information_availability'] for r in rows)
    assert BENCHMARK.read_bytes()==before


def test_query_changes_require_version_review(tmp_path):
    path=tmp_path/'benchmark.jsonl';path.write_bytes(BENCHMARK.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='Benchmark changed'):build_metadata(path)
