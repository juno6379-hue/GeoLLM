"""Operational-only referent review; never promote proximity to coordinate authority."""
import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader
import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import shape
from shapely.ops import transform
from shapely import wkt
from scripts.audit_dataset_coordinate_literals import parse
from scripts.audit_coordinate_object_candidates import TABLES


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compact(text):
    # Used only for locating a short quotation in a PDF, not whole-text approval.
    return re.sub(r'\s+', '', text)


def disposition(context, candidate_names):
    """Conservative rule-based evidence classification, not real-world authority."""
    before, after = context
    if '정박구역' in before or ('radius of 270m' in before and 'harbor limit' in before):
        return 'DIFFERENT_REFERENT_ANCHORAGE_CENTRE', None
    # A named section immediately preceding the coordinate, not any name nearby.
    heading = re.search(r'\d+\.\d+\.\d+\s+([가-힣]+항)(?:\([^)]*\))?\s*\(?\s*$', before)
    if heading:
        name = heading.group(1)
        exact = [n for n in candidate_names if n == name]
        if len(exact) == 1:
            return 'SOURCE_NAMED_REFERENT_SUPPORTED_CRS_PENDING', name
        return 'HEADING_AND_CANDIDATE_NAME_NOT_IDENTICAL', name
    if re.search(r'가거초\(可居礁\).*가거도항서쪽약48km\s*\(?\s*$', compact(before)):
        if '가거초' in candidate_names:
            return 'SOURCE_NAMED_REFERENT_SUPPORTED_CRS_PENDING', '가거초'
    return 'NAME_OR_REFERENT_UNRESOLVED', None


def verify_supported_object(obj, relation):
    """Independently reopen supported raw records and transform original geometry."""
    if relation == 'serving.marine_gazetteer_current':
        source = Path(obj['provenance']['source_asset'])
        assert digest(source.read_bytes()) == obj['provenance']['source_sha256']
        with source.open(encoding='cp949', newline='') as stream:
            matches = [(i, r) for i, r in enumerate(csv.DictReader(stream))
                       if r['공간정보일련번호'] == obj['properties']['공간정보일련번호']]
        assert len(matches) == 1
        index, props = matches[0]
        assert props == obj['properties']
        original = wkt.loads(props['공간정보'])
        crs = CRS.from_epsg(5179)
        source_hash = digest(source.read_bytes())
    else:
        assert relation == 'serving.small_harbour_guide'
        source = Path('Dataset/소형선항만 안내정보/TB_SAILER.shp')
        hashes = {source.with_suffix(e).name:digest(source.with_suffix(e).read_bytes())
                  for e in ('.shp','.shx','.dbf','.prj','.cpg')}
        source_hash = digest(json.dumps(hashes, sort_keys=True).encode())
        index = int(obj['source_id'].rsplit(':',1)[1])
        assert obj['source_id'] == f'small_harbour:{source_hash}:{index}'
        reader = shapefile.Reader(str(source), encoding='utf-8', encodingErrors='replace')
        raw = reader.shapeRecord(index)
        props = raw.record.as_dict()
        assert props == obj['properties']
        original = shape(raw.shape.__geo_interface__)
        crs = CRS.from_wkt(source.with_suffix('.prj').read_text())
    converted = transform(Transformer.from_crs(crs,4326,always_xy=True).transform,original)
    stored = shape(json.loads(obj['geojson']) if isinstance(obj['geojson'],str) else obj['geojson'])
    assert converted.equals_exact(stored, tolerance=1e-8)
    return dict(raw_record_verified=True, original_row_index=index, original_source=str(source),
                original_source_sha256=source_hash, original_crs=crs.to_string(),
                geometry_reprojection_matches=True, tolerance_degrees=1e-8,
                raw_properties_sha256=digest(json.dumps(props,sort_keys=True,ensure_ascii=False).encode()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', type=Path, default=Path('outputs/dataset_location_audit_20261102'))
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paths = [args.base/'source/revision_v2/compact_receipts.jsonl',
             args.base/'source/revision_v2/full_current_document_chunks.jsonl.gz',
             args.base/'coordinate_object_candidates_v2/candidates.jsonl',
             args.base/'spatial/manifest_v2.json']
    paths += [args.base/'spatial'/f'{table}.json' for table in TABLES]
    inputs = {str(p): digest(p.read_bytes()) for p in paths}
    receipts = {r['chunk_id']: r for line in paths[0].open(encoding='utf-8')
                if (r := json.loads(line))['status'] == 'UNVERIFIED'
                and r.get('retrieval_status') != 'SUPERSEDED'}
    assert len(receipts) == 3819
    with gzip.open(paths[1], 'rt', encoding='utf-8') as stream:
        rows = {r['chunk_id']: r for line in stream
                if (r := json.loads(line))['chunk_id'] in receipts}
    assert rows.keys() == receipts.keys()
    objects = {}
    for table, path in zip(TABLES, paths[4:]):
        for obj in json.loads(path.read_text(encoding='utf-8')):
            objects[('serving.'+table, obj['source_id'])] = obj
    names = sorted({o['name'] for o in objects.values() if len(o.get('name') or '') >= 2})
    # Exact inventory substrings are candidate mentions only (Korean spacing varies).
    names_re = re.compile('|'.join(re.escape(n) for n in sorted(names, key=len, reverse=True)))
    pair_counts = Counter()
    inventory_counts = Counter()
    with (args.output/'chunk_screening.jsonl').open('w', encoding='utf-8') as out:
        for cid, row in rows.items():
            receipt = receipts[cid]
            assert digest(row['content'].encode()) == receipt['content_sha256']
            assert row['source_sha256'] == receipt['source_sha256']
            axes, pairs = parse(row['content'])
            hits = sorted(set(names_re.findall(row['content'])))
            pair_counts.update(p['status'] for p in pairs)
            inventory_counts['chunks_with_name_candidates'] += bool(hits)
            inventory_counts['chunks_with_coordinate_pairs'] += bool(pairs)
            inventory_counts['explicit_axes'] += len(axes)
            result = dict(chunk_id=cid, content_sha256=receipt['content_sha256'],
                          source_sha256=receipt['source_sha256'], source_file=row['source_file'],
                          page_no=row['page_no'], exact_inventory_name_candidates=hits,
                          coordinate_pairs=pairs, source_text_status='UNVERIFIED',
                          object_identity_verified=False, coordinate_authority=False,
                          status='CANDIDATES_REQUIRE_REFERENT_CRS_CHECK' if pairs or hits else 'NO_RECOGNIZED_CANDIDATE_NOT_PROOF_OF_ABSENCE')
            out.write(json.dumps(result, ensure_ascii=False)+'\n')
    previous = [json.loads(line) for line in paths[2].open(encoding='utf-8')]
    candidates = [r for r in previous if r['chunk_id'] in rows]
    readers = {}
    reviews = []
    for candidate in candidates:
        row = rows[candidate['chunk_id']]
        source = Path(row['source_file'])
        assert digest(source.read_bytes()) == row['source_sha256']
        if source not in readers:
            readers[source] = PdfReader(source)
        page = readers[source].pages[row['page_no']-1].extract_text()
        before = row['content'][max(0,candidate['start']-180):candidate['start']]
        after = row['content'][candidate['end']:candidate['end']+180]
        quotation = before+candidate['text']+after
        quote_found = compact(quotation) in compact(page)
        # Whole quotation can cross a stored chunk boundary; never approve if absent.
        status, referent = disposition((before, after), [c['name'] for c in candidate['candidates']])
        if not quote_found:
            status = 'ORIGINAL_PAGE_QUOTE_UNRESOLVED'
        enriched = []
        for c in candidate['candidates']:
            obj = objects[(c['relation'], c['source_id'])]
            enriched.append({**c, 'properties': obj['properties'], 'provenance': obj['provenance'],
                             'geojson': obj['geojson'], 'object_record_sha256': digest(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode())})
            if status == 'SOURCE_NAMED_REFERENT_SUPPORTED_CRS_PENDING' and c['name'] == referent:
                enriched[-1]['independent_raw_recheck'] = verify_supported_object(obj,c['relation'])
        warnings = []
        if referent == '가거초':
            assert '7.8m' in after
            assert enriched[0]['properties']['수심높이너비설명'] == '수심 7.4m'
            warnings.append(dict(field='depth',document_value='7.8m',inventory_value='7.4m',
                                 status='SOURCE_ATTRIBUTE_CONFLICT_NO_AUTOMATIC_MERGE'))
        reviews.append(dict(chunk_id=row['chunk_id'], content_sha256=receipts[row['chunk_id']]['content_sha256'],
                            source_sha256=row['source_sha256'], source_file=row['source_file'],page_no=row['page_no'],
                            original_page_sha256=digest(page.encode()), original_quote_located_ignoring_whitespace=quote_found,
                            quotation=quotation, coordinate_literal=candidate['text'],
                            status=status, named_referent=referent, candidates=enriched,
                            warnings=warnings, source_referent_supported=status=='SOURCE_NAMED_REFERENT_SUPPORTED_CRS_PENDING',
                            document_coordinate_crs='NOT_ESTABLISHED', object_identity_verified=False,
                            coordinate_authority=False, runtime_promoted=False))
    outpath=args.output/'referent_reviews.jsonl'
    outpath.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reviews),encoding='utf-8')
    summary=dict(status='PARTIALLY_VERIFIED', chunks_screened=len(rows), inventory_objects=len(objects),
                 **inventory_counts, coordinate_pair_statuses=dict(pair_counts),
                 prior_proximity_pairs_total=len(previous), reviewed_target_proximity_pairs=len(reviews),
                 review_status_counts=dict(Counter(r['status'] for r in reviews)),
                 source_named_referents_supported=sum(r['source_referent_supported'] for r in reviews),
                 original_page_quote_located=sum(r['original_quote_located_ignoring_whitespace'] for r in reviews),
                 source_attribute_conflicts=sum(len(r['warnings']) for r in reviews),
                 verified_real_world_coordinate_identity=0, coordinate_authority=False,
                 paper_experiment=False, holdout_used=False, input_sha256=inputs,
                 artifact_sha256={p.name:digest(p.read_bytes()) for p in args.output.glob('*.jsonl')},
                 limitations=['Inventory name substring is only a candidate, not entity identity.',
                              'All 3819 chunks screened using recognized explicit syntax; not all possible location mentions.',
                              'Source named-referent support is distinct from CRS, current real-world identity and location accuracy.',
                              '100m candidates are inherited spherical-distance review aids; no hit does not mean real-world absence.',
                              'No database, receipt pointer, embedding, runtime source or research files changed.'])
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in {'input_sha256','artifact_sha256'}},ensure_ascii=False))


if __name__ == '__main__':
    main()
