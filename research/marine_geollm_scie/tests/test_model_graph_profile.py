import pytest
from research.marine_geollm_scie.runners.model_proxy import validate_request,clean
from research.marine_geollm_scie.runners.launch_model_graph import validate_profile

CAPABILITY={'relation':'knowledge.capability_embeddings','rows':21,'embedding_rows':21,'min_embedding_dimension':1024,'max_embedding_dimension':1024}
DIGESTS={'qwen2.5:1.5b':'a'*64,'bge-m3:latest':'b'*64}

def test_model_profile_requires_completed_matching_embeddings():
    snapshot={'relations':[CAPABILITY],'status':'LOADED_VERIFIED','db_identity':{'container':'marine-scie-pilot-db','database':'scie_model_v3'}}
    profile={'embedding_ready':True,'model_digests':DIGESTS,'embedding_model_digest':'b'*64}
    validate_profile(profile,snapshot)
    for replacement in ({'embedding_ready':False},{'embedding_model_digest':'c'*64}):
        with pytest.raises(ValueError):validate_profile({**profile,**replacement},snapshot)
    with pytest.raises(ValueError):validate_profile(profile,{**snapshot,'status':'EXPORTED'})
    for cap in ({}, {**CAPABILITY,'embedding_rows':20}, {**CAPABILITY,'max_embedding_dimension':768}):
        with pytest.raises(ValueError):validate_profile(profile,{**snapshot,'relations':[cap]})

@pytest.mark.parametrize('path,model',[('/api/pull','qwen2.5:1.5b'),('/api/generate','llama3.1'),('/api/embed','qwen2.5:1.5b'),('/v1/chat/completions','bge-m3')])
def test_proxy_rejects_unapproved_endpoint_model_or_role(path,model):
    with pytest.raises(ValueError):validate_request('POST',path,{'model':model},DIGESTS)

def test_proxy_accepts_only_pinned_model_operations():
    validate_request('POST','/api/embed',{'model':'bge-m3'},DIGESTS)
    validate_request('POST','/v1/chat/completions',{'model':'qwen2.5:1.5b'},DIGESTS)
    assert clean({'message':{'content':'observable','thinking':'private'}})=={'message':{'content':'observable'}}

def test_digest_gate_rejects_missing_or_replaced_model():
    from research.marine_geollm_scie.runners.model_proxy import validate_digests
    tags={'models':[{'name':name,'digest':digest} for name,digest in DIGESTS.items()]}
    validate_digests(tags,DIGESTS)
    with pytest.raises(ValueError):validate_digests({'models':[]},DIGESTS)
    with pytest.raises(ValueError):validate_digests(tags,{**DIGESTS,'qwen2.5:1.5b':'c'*64})

def test_partial_or_duplicate_observations_are_not_finished_run():
    from research.marine_geollm_scie.runners.launch_model_graph import validate_observations
    cases={str(i) for i in range(18)}
    rows=[{'case_id':case,'status':'GRAPH_ERROR'} for case in sorted(cases)]
    validate_observations(rows,cases)  # A captured failure is not falsely semantic success.
    with pytest.raises(ValueError):validate_observations(rows[:-1],cases)
    with pytest.raises(ValueError):validate_observations(rows[:-1]+[rows[0]],cases)
