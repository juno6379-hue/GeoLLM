import json
from research.marine_geollm_scie.runners import full_pipeline
from research.marine_geollm_scie.runners.launch_model_graph import validate_profile,sha

def test_pipeline_generated_model_profile_matches_launcher_without_model_calls(tmp_path,monkeypatch):
    monkeypatch.setattr(full_pipeline,'ROOT',tmp_path)
    data=tmp_path/'data';data.mkdir()
    (data/'s101_feature_catalogue_v2_parsed.json').write_text('{}')
    (data/'public_place_anchors.json').write_text(json.dumps({'places':[{'place_id':'mof:dokdo:east-island','label':'synthetic name','aliases':[],'longitude':1,'latitude':2}]}))
    snapshot={'status':'LOADED_VERIFIED','db_identity':{'container':'marine-scie-pilot-db','database':'scie_model_v3'},'relations':[{'relation':'knowledge.capability_embeddings','rows':21,'embedding_rows':21,'min_embedding_dimension':1024,'max_embedding_dimension':1024},{'relation':'knowledge.document_chunks','rows':10,'embedding_rows':10}]}
    embedding={'status':'COMPLETED','pending':0,'total':10,'embedded':10,'min_dim':1024,'max_dim':1024,'model_digest_unchanged':True,'model_digest':full_pipeline.BGE}
    sp=tmp_path/'snapshot.json';ep=tmp_path/'embedding.json'
    sp.write_text(json.dumps(snapshot));ep.write_text(json.dumps(embedding))
    baseline,model=full_pipeline.build_profiles(sp,ep,tmp_path/'run')
    validate_profile(model,snapshot)
    assert model['snapshot_manifest_sha256']==sha(sp)
    assert model['historical_embedding_digest_unverified'] is True
    assert model['embedding_ready'] is True
    assert baseline['model_digest']==model['model_digests']['qwen2.5:1.5b']
