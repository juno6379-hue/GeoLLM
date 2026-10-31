import io
import json
import socket
import urllib.error

import pytest

from research.marine_geollm_scie.runners import model_proxy
from research.marine_geollm_scie.runners.launch_model_graph import graph_source_files,sha,warmup_summary


DIGESTS={'qwen2.5:1.5b':'a'*64,'bge-m3:latest':'b'*64}


def response(digests=DIGESTS):
    return io.BytesIO(json.dumps({'models':[{'name':name,'digest':value} for name,value in digests.items()]}).encode())


def test_identity_transport_retry_is_bounded_and_preserved(monkeypatch):
    def failed(*args,**kwargs):raise urllib.error.URLError(socket.timeout('private-address'))
    monkeypatch.setattr(model_proxy.urllib.request,'urlopen',failed)
    monkeypatch.setattr(model_proxy.time,'sleep',lambda _:None)
    attempts=[]
    with pytest.raises(urllib.error.URLError):model_proxy.verified_tags('http://upstream',DIGESTS,attempts)
    assert len(attempts)==2
    assert [r['retry_same_request'] for r in attempts]==[True,False]
    assert attempts[0]['reason_type']=='TimeoutError'
    assert 'private-address' not in json.dumps(attempts)


def test_recovered_identity_check_still_verifies_digest(monkeypatch):
    answers=iter([urllib.error.URLError(ConnectionRefusedError(111,'sensitive host')),response()])
    def fetch(*args,**kwargs):
        value=next(answers)
        if isinstance(value,Exception):raise value
        return value
    monkeypatch.setattr(model_proxy.urllib.request,'urlopen',fetch)
    monkeypatch.setattr(model_proxy.time,'sleep',lambda _:None)
    attempts=[]
    model_proxy.verified_tags('http://upstream',DIGESTS,attempts)
    assert [r['status'] for r in attempts]==['FAILED','VERIFIED']
    assert attempts[0]['errno']==111


def test_digest_mismatch_is_never_retried(monkeypatch):
    monkeypatch.setattr(model_proxy.urllib.request,'urlopen',lambda *a,**k:response({'qwen2.5:1.5b':'c'*64}))
    attempts=[]
    with pytest.raises(ValueError):model_proxy.verified_tags('http://upstream',DIGESTS,attempts)
    assert len(attempts)==1 and attempts[0]['retry_same_request'] is False


def test_warmup_error_cannot_be_hidden_by_later_success():
    good={'case':{'case_id':'IMPORT_WARMUP'},'path':'/api/embeddings','status':'RETURNED','upstream_http_status':200,'call_id':'ok'}
    bad={**good,'status':'PROXY_ERROR','call_id':'failed','upstream_http_status':None}
    summary=warmup_summary([bad,good])
    assert summary['status']=='DEGRADED_WARMUP' and summary['failed_call_ids']==['failed']
    assert warmup_summary([good])['status']=='WARMUP_OBSERVED_WITHOUT_PROXY_ERRORS'
    assert warmup_summary([])['status']=='DEGRADED_WARMUP'


def test_tool_registry_is_a_frozen_runtime_dependency(tmp_path):
    registry=tmp_path/'data/tool_registry.yaml';registry.parent.mkdir();registry.write_text('tools: []')
    assert registry in graph_source_files(tmp_path)
    before=sha(registry);registry.write_text('tools: [changed]')
    assert sha(registry)!=before
