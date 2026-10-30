import hashlib
import pytest
from research.marine_geollm_scie.runners.binding_snapshot import verify_files, load


def test_snapshot_content_mutation_rejected_before_loading(tmp_path):
    f=tmp_path/'rows.csv'; f.write_bytes(b'id\n1\n')
    m={'relations':[{'csv_path':'rows.csv','sha256':hashlib.sha256(f.read_bytes()).hexdigest()}]}
    verify_files(m,tmp_path)
    f.write_bytes(b'id\n2\n')
    with pytest.raises(ValueError): verify_files(m,tmp_path)


def test_snapshot_cannot_read_outside_bundle(tmp_path):
    f=tmp_path/'outside.csv'; f.write_bytes(b'data')
    folder=tmp_path/'bundle';folder.mkdir()
    m={'relations':[{'csv_path':'../outside.csv','sha256':hashlib.sha256(f.read_bytes()).hexdigest()}]}
    with pytest.raises(ValueError): verify_files(m,folder)


def test_loader_rejects_production_target_before_docker(tmp_path):
    import json
    (tmp_path/'snapshot_manifest.json').write_text(json.dumps({'db_identity':{'container':'an_geollm_postgis','database':'gbhd_s101'}}))
    with pytest.raises(ValueError,match='Unapproved'):load(tmp_path)
