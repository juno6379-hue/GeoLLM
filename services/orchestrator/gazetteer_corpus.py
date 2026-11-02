"""Read-only identity verification of the ingested marine place inventory.

Matching this CSV establishes a bounded inventory, never geographic coverage.
Every row, attribute and transformed geometry is checked in the query transaction.
"""
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ASSET = 'Dataset/해양수산부_공동활용체계_해양지명_20221231.csv'
SOURCE_SHA256 = 'bbc3f1c347f6048b0befdf5102959078ffc29c22cdc4412a98586e76cddb0464'
SOURCE_COPY = 'data/source_inventory/marine_gazetteer_20221231.csv'
RELATION = 'serving.marine_gazetteer_current'


def verify_gazetteer_corpus(cursor, *, root=ROOT):
    receipt = dict(status='SOURCE_IDENTITY_MISMATCH', dataset_id='marine_gazetteer',
                   relation=RELATION, source_asset=SOURCE_ASSET, source_sha256=SOURCE_SHA256,
                   absence_certified=False)
    try:
        raw = (Path(root) / SOURCE_COPY).read_bytes()
        if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
            raise ValueError('source digest mismatch')
        rows = list(csv.DictReader(io.StringIO(raw.decode('cp949'))))
        expected = {}
        for row in rows:
            if not row.get('공간정보') or not row.get('지명명'):
                continue  # Same explicitly documented ingestion filter.
            key = hashlib.sha256(f"marine_gazetteer_mof|{row.get('공간정보일련번호')}|{row['지명명']}".encode()).hexdigest()[:24]
            if key in expected:
                raise ValueError('duplicate source identity')
            expected[key] = row
        cursor.execute("""SELECT source_id, layer_id, name, name_en, place_type, location_text,
            properties, provenance, ST_AsEWKB(geometry)::text AS geometry_identity,
            COALESCE(ST_SRID(geometry)=4326 AND ST_IsValid(geometry)
                AND NOT ST_IsEmpty(geometry) AND ST_Equals(geometry,
                  ST_Transform(ST_SetSRID(ST_GeomFromText(properties->>'공간정보'),5179),4326)),false)
                AS geometry_matches
            FROM serving.marine_gazetteer_current ORDER BY source_id""")
        names = [item[0] for item in cursor.description]
        actual = [dict(row) if isinstance(row, dict) else dict(zip(names, row)) for row in cursor.fetchall()]
        if len(actual) != len(expected) or {row['source_id'] for row in actual} != set(expected):
            raise ValueError('source membership mismatch')
        for item in actual:
            source = expected[item['source_id']]
            provenance = item.get('provenance') or {}
            if (item['properties'] != source or item['layer_id'] != 'marine_gazetteer_mof'
                    or item['name'] != source['지명명'] or item['name_en'] != source.get('지명영문명')
                    or item['place_type'] != source.get('토지유형')
                    or item['location_text'] != source.get('해양지위치정보')
                    or provenance.get('source_asset') != SOURCE_ASSET
                    or provenance.get('source_sha256') != SOURCE_SHA256
                    or provenance.get('native_srid') != 5179
                    or provenance.get('encoding') != 'cp949' or item['geometry_matches'] is not True):
                raise ValueError('source row/geometry/provenance mismatch')
        digest = hashlib.sha256(json.dumps(actual, ensure_ascii=False, sort_keys=True,
                                          separators=(',', ':')).encode()).hexdigest()
        receipt.update(status='VERIFIED', row_count=len(actual), snapshot_version='sha256:' + digest,
                       content_sha256=digest, source_locator=SOURCE_ASSET,
                       verification='full_csv_membership_attributes_provenance_postgis_geometry')
    except Exception as exc:
        # Do not expose DB connection strings or driver exception messages.
        receipt['reason'] = 'SOURCE_IDENTITY_UNVERIFIED'
        receipt['error_type'] = type(exc).__name__
    return receipt
