import json
import pytest
from fastapi import HTTPException
from services.orchestrator import tide_observation as tide


def payload(item, code='00'):
    return json.dumps(dict(header={'resultCode':code},body={'items':{'item':item},'totalCount':1})).encode()


def test_observed_predicted_missing_zero_negative():
    rows,total = tide.normalize(payload([{'bscTdlvHgt':0,'tdlvHgt':-12.5}, {'bscTdlvHgt':None,'tdlvHgt':''}]))
    assert rows[0]['observed_level'] == 0
    assert rows[0]['predicted_level'] == -12.5
    assert rows[1]['observed_level'] is None and rows[1]['predicted_level'] is None


@pytest.mark.parametrize('body', [payload([], '30'), b'<OpenAPI_ServiceResponse><returnReasonCode>30</returnReasonCode></OpenAPI_ServiceResponse>'])
def test_auth_error_is_not_no_data(body):
    with pytest.raises(HTTPException) as error:
        tide.normalize(body)
    assert error.value.detail['code'] == 'TIDE_PROVIDER_AUTH_DENIED'


def test_empty_and_invalid():
    assert tide.normalize(payload([], '03'))[0] == []
    with pytest.raises(HTTPException): tide.normalize(b'not json')
    with pytest.raises(HTTPException): tide.fetch_tide('DT_0001','20260230')
    with pytest.raises(HTTPException): tide.fetch_tide('http://other','20261006')


def test_transport_error_never_exposes_key(monkeypatch):
    tide._cache.clear()
    monkeypatch.setenv('KHOA_TIDE_SERVICE_KEY','test-secret')
    class Opener:
        def open(self,*args,**kwargs): raise tide.URLError('serviceKey=test-secret')
    monkeypatch.setattr(tide,'build_opener',lambda *_:Opener())
    with pytest.raises(HTTPException) as error: tide.fetch_tide('DT_0001','20261006')
    assert 'test-secret' not in str(error.value.detail)


def test_fetch_persists_once_and_reports_cache(monkeypatch):
    from services.orchestrator import tide_store
    tide._cache.clear(); saved=[]
    monkeypatch.setenv('KHOA_TIDE_SERVICE_KEY','test-secret')
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,*args): return payload({'bscTdlvHgt':10,'tdlvHgt':11})
    class Opener:
        def open(self,*args,**kwargs): return Response()
    monkeypatch.setattr(tide,'build_opener',lambda *_:Opener())
    monkeypatch.setattr(tide_store,'save',lambda value:saved.append(value) or {'status':'STORED'})
    result=tide.fetch_tide('DT_0001','20261006')
    assert result['storage']['status']=='STORED' and not result['cached']
    assert tide.fetch_tide('DT_0001','20261006')['cached'] and len(saved)==1
    assert 'test-secret' not in json.dumps(result)
