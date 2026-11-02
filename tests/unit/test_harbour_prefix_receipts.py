import copy
import importlib.util
import json
from pathlib import Path
import pytest

try:
    from services.orchestrator import harbour_prefix_receipts as module
except ImportError:
    spec=importlib.util.spec_from_file_location('proposed_harbour_prefix_receipts',Path(__file__).with_name('harbour_prefix_receipts.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


@pytest.fixture
def data(monkeypatch):
    if Path(__file__).with_name('prefix_receipts.json').exists():
        path=Path(__file__).with_name('prefix_receipts.json')
    else:
        path=Path(__file__).resolve().parents[2]/'data/source_verification/harbour_prefix_20261103_v1.json'
    monkeypatch.setattr(module,'RECEIPT_PATH',path)
    receipt=json.loads(path.read_text(encoding='utf8'))
    rows=[]
    for e in receipt['entries']:
        rows.append(({'source_id':e['source_id'],'properties':{e['field']:e['prefix']+'\ufffd'},
                      'provenance':{'source_file':e['source_file'],'source_sha256':e['source_sha256'],
                                    'component_hashes':{'TB_SAILER.dbf':e['dbf_sha256']}}},e))
    return rows


def test_all_18_receipts_return_only_exact_prefix(data):
    assert len(data)==18
    for row,e in data:
        found=module.verified_prefix(row,e['field'],row['properties'][e['field']])
        assert found['prefix']==e['prefix'] and '\ufffd' not in found['prefix']
        assert found['receipt']['raw_field_sha256']==e['raw_field_sha256']


@pytest.mark.parametrize('mutation',['source','source_sha','dbf_sha','path','value','middle_damage','field','missing_metadata'])
def test_wrong_identity_or_content_remains_withheld(data,mutation):
    row,e=copy.deepcopy(data[0]);field=e['field'];value=row['properties'][field]
    if mutation=='source':row['source_id']+='9'
    elif mutation=='source_sha':row['provenance']['source_sha256']='0'*64
    elif mutation=='dbf_sha':row['provenance']['component_hashes']['TB_SAILER.dbf']='0'*64
    elif mutation=='path':row['provenance']['source_file']='Dataset/other.shp'
    elif mutation=='value':value+='!';row['properties'][field]=value
    elif mutation=='middle_damage':value='\ufffd'+value;row['properties'][field]=value
    elif mutation=='field':field='UNRELATED'
    elif mutation=='missing_metadata':row['provenance']={}
    assert module.verified_prefix(row,field,value) is None


def test_tampered_or_missing_receipt_fails_closed(data,monkeypatch,tmp_path):
    row,e=data[0];path=tmp_path/'receipt.json'
    monkeypatch.setattr(module,'RECEIPT_PATH',path)
    assert module.verified_prefix(row,e['field'],row['properties'][e['field']]) is None
    path.write_text('{}',encoding='utf8')
    assert module.verified_prefix(row,e['field'],row['properties'][e['field']]) is None
