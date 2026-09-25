"""Build reproducible page/XML locators from archived originals without creating gold labels."""
import argparse
from collections import Counter
import hashlib
import io
import json
import logging
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from services.orchestrator.reference_evaluation import make_unit


def local_name(node):
    return node.tag.rsplit('}',1)[-1]


def units_for(raw, fmt):
    if fmt=='pdf':
        from pypdf import PdfReader
        class Capture(logging.Handler):
            def __init__(self):
                super().__init__(); self.messages=[]
            def emit(self,record):
                self.messages.append(record.getMessage())
        logger=logging.getLogger('pypdf'); capture=Capture()
        old_handlers,old_propagate=logger.handlers[:],logger.propagate
        logger.handlers=[capture]; logger.propagate=False
        try:
            for number,page in enumerate(PdfReader(io.BytesIO(raw)).pages,1):
                capture.messages=[]
                text=page.extract_text() or ''
                yield {'kind':'pdf_page','page_1based':number,
                       '_warnings':sorted(set(capture.messages))},text,[]
        finally:
            logger.handlers=old_handlers; logger.propagate=old_propagate
    elif fmt in {'hml','hwpx'}:
        members=[('',raw)] if fmt=='hml' else []
        if fmt=='hwpx':
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members=[(n,archive.read(n)) for n in sorted(archive.namelist())
                         if re.fullmatch(r'Contents/section\d+\.xml',n)]
        for member,content in members:
            root=ET.fromstring(content)
            # A paragraph ordinal is an extraction locator, not a legal article number.
            for ordinal,node in enumerate((n for n in root.iter() if local_name(n) in {'P','p'}),1):
                texts=[n.text or '' for n in node.iter() if local_name(n) in {'CHAR','t'}]
                text=''.join(texts)
                if text.strip():
                    yield {'kind':'xml_paragraph','member':member,'paragraph_1based':ordinal},text,[]
    elif fmt=='fc_xml':
        root=ET.fromstring(raw)
        version=next((n.text for n in root if local_name(n)=='versionNumber'),None)
        product=next((n.text for n in root if local_name(n)=='productId'),None)
        if version!='2.0.0' or product!='S-101':
            raise ValueError('Expected S-101 Feature Catalogue 2.0.0')
        for node in root.iter():
            if local_name(node) not in {'S100_FC_FeatureType','S100_FC_SimpleAttribute','S100_FC_ComplexAttribute'}:
                continue
            values={local_name(n):n.text for n in node if local_name(n) in {'code','name','definition'}}
            if values.get('code') and values.get('definition'):
                text='\n'.join(f'{k}: {v}' for k,v in values.items())
                yield {'kind':'fc_code','element':local_name(node),'code':values['code']},text,[values['code']]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--review',type=Path,required=True)
    p.add_argument('--fc',type=Path,required=True)
    p.add_argument('--dceg',type=Path)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    manifest=json.loads((args.archive/'manifest.json').read_text(encoding='utf-8'))
    review=json.loads(args.review.read_text(encoding='utf-8'))
    statuses={f['artifact_id']:f['status'] for f in review['findings']}
    sources=[]
    for row in manifest['records']:
        if row['format']=='html':
            continue
        sources.append((dict(row,source_review_status=statuses.get(row['artifact_id'],'UNREVIEWED')),
                        args.archive/Path(row['path']).name))
    raw=args.fc.read_bytes()
    sources.append(({'artifact_id':'iho_s101_fc_2_0_0','sha256':hashlib.sha256(raw).hexdigest(),
                     'edition':'2.0.0','format':'fc_xml','source_review_status':'LOCAL_EDITION_VERIFIED_SIGNATURE_UNVERIFIED'},args.fc))
    if args.dceg:
        raw=args.dceg.read_bytes()
        sources.append(({'artifact_id':'iho_s101_dceg_2_0_0','sha256':hashlib.sha256(raw).hexdigest(),
                         'edition':'2.0.0','format':'pdf','source_review_status':'LOCAL_SOURCE_REVIEW_REQUIRED'},args.dceg))
    args.output.mkdir(parents=True,exist_ok=False)
    totals=Counter(); empty=[]
    with (args.output/'units.jsonl').open('x',encoding='utf-8') as stream:
        for source,path in sources:
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=source['sha256']:
                raise ValueError(f'Source hash mismatch: {source["artifact_id"]}')
            for locator,text,canonical in units_for(raw,source['format']):
                extraction_warnings=locator.pop('_warnings',[])
                unit=make_unit(source,locator,text,canonical)
                unit['extraction_flags']=[]
                if extraction_warnings:
                    unit['extraction_flags'].append('PARSER_WARNING_REVIEW_REQUIRED')
                    unit['parser_warnings']=extraction_warnings
                if not text.strip():
                    unit['extraction_flags'].append('EMPTY_TEXT_REQUIRES_VISUAL_OR_OCR_REVIEW')
                    empty.append(unit['unit_id'])
                if any(ord(c)<32 and c not in '\n\r\t' for c in text):
                    unit['extraction_flags'].append('CONTROL_CHARACTERS')
                stream.write(json.dumps(unit,ensure_ascii=False)+'\n')
                totals[source['artifact_id']]+=1
    import importlib.metadata
    dependencies={}
    for package in ('pypdf','fonttools'):
        try: dependencies[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: dependencies[package]=None
    report={'source_counts':dict(totals),'units':sum(totals.values()),'empty_units':empty,'extractor_dependencies':dependencies,
            'manifest_sha256':hashlib.sha256((args.archive/'manifest.json').read_bytes()).hexdigest(),
            'review_sha256':hashlib.sha256(args.review.read_bytes()).hexdigest(),
            'units_sha256':hashlib.sha256((args.output/'units.jsonl').read_bytes()).hexdigest(),
            'human_gold':False,'execution_authorized':False,
            'limitations':['PDF page text and XML paragraph ordinals are not approved legal article labels.',
                           'Extraction does not validate legal currency, document signature or semantic accuracy.']}
    (args.output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'units':report['units'],'sources':len(totals),'empty':len(empty)}))


if __name__=='__main__':
    main()
