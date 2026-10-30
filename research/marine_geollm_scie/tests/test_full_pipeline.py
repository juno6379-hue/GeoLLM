import pytest
from research.marine_geollm_scie.runners.full_pipeline import require_embedding_complete,build_profiles,BGE


def test_incomplete_or_unverified_embedding_never_starts_model_comparison():
    valid={'status':'COMPLETED','total':23215,'embedded':23215,'pending':0,'min_dim':1024,'max_dim':1024,'model_digest_unchanged':True}
    require_embedding_complete(valid)
    for override in ({'pending':1},{'status':'RUNNING'},{'embedded':17593},{'model_digest_unchanged':False},{'max_dim':768},{'total':0,'embedded':0}):
        with pytest.raises(ValueError):require_embedding_complete({**valid,**override})


def test_profile_cannot_use_partial_or_wrong_database(tmp_path):
    import json
    embed=tmp_path/'embedding.json';snapshot=tmp_path/'snapshot.json'
    embed.write_text(json.dumps({'status':'COMPLETED','total':2,'embedded':2,'pending':0,'min_dim':1024,'max_dim':1024,'model_digest_unchanged':True,'model_digest':BGE}))
    data={'status':'LOADED_VERIFIED','db_identity':{'container':'marine-scie-pilot-db','database':'scie_binding_v2'},
          'relations':[{'relation':'knowledge.document_chunks','rows':2,'embedding_rows':1}]}
    snapshot.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='research snapshot'):build_profiles(snapshot,embed,tmp_path/'run')
    data['db_identity']['database']='scie_model_v3';snapshot.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='count mismatch'):build_profiles(snapshot,embed,tmp_path/'run')
    assert not (tmp_path/'run').exists()
