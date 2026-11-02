"""Inventory mismatch failures; no holdout answers or geographic authority fixtures."""
import csv
import hashlib
import io
from pathlib import Path

import pytest

from services.orchestrator import gazetteer_corpus as corpus


class InventoryCursor:
    description = []

    def __init__(self):
        self.rows = []
        raw = (corpus.ROOT / corpus.SOURCE_COPY).read_bytes()
        for source in csv.DictReader(io.StringIO(raw.decode('cp949'))):
            if not source.get('공간정보') or not source.get('지명명'):
                continue
            key = hashlib.sha256(f"marine_gazetteer_mof|{source.get('공간정보일련번호')}|{source['지명명']}".encode()).hexdigest()[:24]
            self.rows.append(dict(source_id=key, layer_id='marine_gazetteer_mof', name=source['지명명'],
                name_en=source.get('지명영문명'), place_type=source.get('토지유형'),
                location_text=source.get('해양지위치정보'), properties=source,
                provenance=dict(source_asset=corpus.SOURCE_ASSET, source_sha256=corpus.SOURCE_SHA256,
                                native_srid=5179, encoding='cp949'),
                geometry_identity='fixture', geometry_matches=True))

    def execute(self, sql):
        assert 'ST_Equals' in sql and 'ST_Transform' in sql and 'ORDER BY source_id' in sql
        assert 'WHERE' not in sql  # Exact inventory includes unexpected extra rows.

    def fetchall(self):
        return self.rows


def test_exact_inventory_identity_is_not_geographic_coverage():
    receipt = corpus.verify_gazetteer_corpus(InventoryCursor())
    assert receipt['status'] == 'VERIFIED'
    assert receipt['row_count'] == 1146
    assert receipt['absence_certified'] is False
    assert receipt['snapshot_version'].startswith('sha256:')


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'name', 'properties', 'provenance', 'geometry', 'layer'])
def test_live_inventory_changes_fail_closed(mutation):
    cursor = InventoryCursor()
    if mutation == 'missing':
        cursor.rows.pop()
    elif mutation == 'extra':
        cursor.rows.append(dict(cursor.rows[0], source_id='unexpected'))
    elif mutation == 'name':
        cursor.rows[0]['name'] = 'altered'
    elif mutation == 'properties':
        cursor.rows[0]['properties']['extra'] = 'altered'
    elif mutation == 'provenance':
        cursor.rows[0]['provenance']['source_sha256'] = 'wrong'
    elif mutation == 'geometry':
        cursor.rows[0]['geometry_matches'] = False
    elif mutation == 'layer':
        cursor.rows[0]['layer_id'] = 'wrong'
    assert corpus.verify_gazetteer_corpus(cursor)['status'] == 'SOURCE_IDENTITY_MISMATCH'


def test_source_asset_missing_or_modified_fails_closed(tmp_path):
    cursor = InventoryCursor()
    assert corpus.verify_gazetteer_corpus(cursor, root=tmp_path)['status'] == 'SOURCE_IDENTITY_MISMATCH'
    asset = tmp_path / corpus.SOURCE_COPY
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b'changed')
    assert corpus.verify_gazetteer_corpus(cursor, root=tmp_path)['status'] == 'SOURCE_IDENTITY_MISMATCH'
