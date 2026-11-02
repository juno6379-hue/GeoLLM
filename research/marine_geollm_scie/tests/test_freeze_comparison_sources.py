import json
import pytest
from research.marine_geollm_scie.runners import freeze_comparison_sources as module


def test_execution_sources_exclude_ui_and_runtime_feedback(tmp_path):
    for name in ('services/a.py','shared/a.py','services/static/a.js',
                 'data/x.yaml','data/feedback/a.jsonl','research/marine_geollm_scie/runners/a.py'):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('')
    paths={p.relative_to(tmp_path).as_posix() for p in module.execution_files(tmp_path)}
    assert paths=={'services/a.py','shared/a.py','data/x.yaml','research/marine_geollm_scie/runners/a.py'}


def test_existing_snapshot_never_overwritten(tmp_path):
    with pytest.raises(FileExistsError):
        module.freeze(tmp_path/'absent.json',tmp_path)


def test_review_and_measurement_contracts_are_frozen(tmp_path):
    expected = {'structured_review_v1.json', 'structured_review_v2.json',
                'eight_execution_contract_v3.json', 'eight_execution_contract_v4.json',
                'execution_success_v3_20261101_KR.md'}
    folder = tmp_path/'research/marine_geollm_scie/protocol'
    folder.mkdir(parents=True)
    for name in expected | {'unrelated_notes.md'}:
        (folder/name).write_text('{}')
    assert {p.name for p in module.execution_files(tmp_path)} == expected


def test_nonresearch_parent_rejected_before_export(tmp_path):
    parent=tmp_path/'parent.json';parent.write_text(json.dumps({'status':'LOADED_VERIFIED','db_identity':{'database':'production'}}))
    with pytest.raises(ValueError,match='verified research'):
        module.freeze(parent,tmp_path/'new')


@pytest.mark.parametrize('mutate_parent',[False,True])
def test_freeze_rechecks_parent_csv_after_all_exports(tmp_path,monkeypatch,mutate_parent):
    """No Docker/DB: real freeze gates, immutable synthetic DB exports."""
    from research.marine_geollm_scie.runners import binding_snapshot
    parent_dir=tmp_path/'parent';parent_dir.mkdir()
    code=tmp_path/'services/a.py';code.parent.mkdir();code.write_text('old')
    old_code=module.digest(code);code.write_text('new')
    frozen={};records=[]
    for index,relation in enumerate(module.RELATION_KEYS):
        name=f'relation_{index}.csv';payload=f'id\n{index}\n'.encode()
        path=parent_dir/name;path.write_bytes(payload);frozen[name]=payload
        records.append({'relation':relation,'csv_path':name,'sha256':module.digest(path),'rows':1})
    parent={'status':'LOADED_VERIFIED','db_identity':{'container':module.TARGET_CONTAINER,'database':'scie_model_v3'},
            'relations':records,'files':[{'path':'services/a.py','sha256':old_code}]}
    parent_path=parent_dir/'snapshot_manifest.json';parent_path.write_text(json.dumps(parent))
    parent_hash=module.digest(parent_path)
    original_verify=module.verify_parent_for_new_code
    monkeypatch.setattr(module,'ROOT',tmp_path);monkeypatch.setattr(binding_snapshot,'ROOT',tmp_path)
    monkeypatch.setattr(module,'execution_files',lambda:[code])
    monkeypatch.setattr(module,'verify_parent_for_new_code',lambda p,d,f:original_verify(p,d,f,root=tmp_path))
    def command(args,**kwargs):
        if args[:2]==['docker','inspect']:return json.dumps([{'Config':{'Labels':{'marine.scie.research':'true'}}}]).encode()
        if args[:2]==['git','rev-parse']:return 'fixture-sha\n'
        if args[:2]==['git','status']:return b''
        raise AssertionError('Unexpected external command')
    monkeypatch.setattr(module.subprocess,'check_output',command)
    exported=[]
    def export(record,destination):
        destination.write_bytes(frozen[record['csv_path']]);exported.append(record['relation'])
        if mutate_parent and len(exported)==6:(parent_dir/records[0]['csv_path']).write_bytes(b'changed during export')
        return {'relation':record['relation'],'content_match':True,'roundtrip_sha256':module.digest(destination)}
    monkeypatch.setattr(module,'export_relation',export)
    out=tmp_path/'new'
    if mutate_parent:
        with pytest.raises(ValueError,match='Parent source data changed'):module.freeze(parent_path,out)
        result=json.loads((out/'snapshot_manifest.json').read_text(encoding='utf-8'))
        assert result['status']=='FREEZE_FAILED'
    else:
        result=module.freeze(parent_path,out)
        assert result['status']=='LOADED_VERIFIED'
        assert len(result['execution_freeze']['explicit_execution_source_changes'])==1
    assert len(exported)==6 and module.digest(parent_path)==parent_hash
