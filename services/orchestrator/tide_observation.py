"""KHOA observed/predicted tide source records, separate from forecasts/UKC."""
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

from fastapi import APIRouter, HTTPException, Query

ENDPOINT = 'https://apis.data.go.kr/1192136/surveyTideLevel/GetSurveyTideLevelApiService'
SOURCE = 'https://www.data.go.kr/data/15142507/openapi.do'
router = APIRouter(prefix='/observations/tide', tags=['Marine observations'])
MAX_BYTES = 2_000_000
_cache = {}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fail(code, status=502):
    raise HTTPException(status_code=status, detail={'code': code}) from None


def number(value):
    if value is None or value == '' or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def normalize(payload):
    if len(payload) > MAX_BYTES:
        fail('TIDE_RESPONSE_TOO_LARGE')
    try:
        text = payload.decode('utf-8-sig')
        if text.lstrip().startswith('<'):
            if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
                fail('TIDE_INVALID_RESPONSE')
            root = ElementTree.fromstring(text)
            code = root.findtext('.//returnReasonCode') or root.findtext('.//resultCode')
            if code in {'20', '30', '31'}:
                fail('TIDE_PROVIDER_AUTH_DENIED')
            fail('TIDE_PROVIDER_REJECTED')
        data = json.loads(text)
        data = data.get('response', data)
        code = str(data['header']['resultCode'])
        if code not in {'00', '0', '03', '3'}:
            fail('TIDE_PROVIDER_AUTH_DENIED' if code in {'20','30','31'} else 'TIDE_PROVIDER_REJECTED')
        body = data.get('body') or {}
        items = (body.get('items') or {}).get('item') or []
        if isinstance(items, dict):
            items = [items]
        rows = []
        for item in items:
            rows.append(dict(station_name=item.get('obsvtrNm'), observed_at=item.get('obsrvnDt'),
                             latitude=number(item.get('lat')), longitude=number(item.get('lot')),
                             observed_level=number(item.get('bscTdlvHgt')),
                             predicted_level=number(item.get('tdlvHgt'))))
        return rows, int(body.get('totalCount') or 0)
    except (ValueError, TypeError, KeyError, AttributeError, ElementTree.ParseError):
        fail('TIDE_INVALID_RESPONSE')


def fetch_tide(station, date, interval=60, page=1, page_size=300):
    if not re.fullmatch(r'DT_[0-9]{4}', station):
        fail('TIDE_INVALID_STATION', 422)
    try:
        datetime.strptime(date, '%Y%m%d')
        if len(date) != 8:
            raise ValueError()
    except ValueError:
        fail('TIDE_INVALID_DATE', 422)
    if not (1 <= interval <= 60 and 1 <= page <= 100 and 1 <= page_size <= 300):
        fail('TIDE_INVALID_PAGINATION', 422)
    key = os.getenv('KHOA_TIDE_SERVICE_KEY', '').strip()
    if not key:
        fail('TIDE_NOT_CONFIGURED', 503)
    cache_key = (station, date, interval, page, page_size)
    cached = _cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < 30:
        return {**cached[1], 'cached': True}
    params = dict(serviceKey=key, type='json', obsCode=station, reqDate=date,
                  min=interval, pageNo=page, numOfRows=page_size)
    request = Request(ENDPOINT+'?'+urlencode(params), headers={'Accept':'application/json'})
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            payload = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError):
        # Never expose exception text: request URLs include the service key.
        fail('TIDE_UPSTREAM_UNAVAILABLE')
    rows, total = normalize(payload)
    result = dict(status='COMPLETED' if rows else 'NO_DATA', source=SOURCE,
                  provider='국립해양조사원', endpoint=ENDPOINT, station_code=station,
                  requested_date=date, interval_minutes=interval, page=page, page_size=page_size,
                  total_count=total, returned_count=len(rows), has_more=page*page_size<total,
                  fetched_at=datetime.now(timezone.utc).isoformat(), cached=False,
                  unit=None, vertical_datum=None, rows=rows,
                  field_mapping={'observed_level':'bscTdlvHgt','predicted_level':'tdlvHgt'},
                  note='원천 관측시각과 조회시각은 다릅니다. 단위·수직기준면은 추가 확인 전 수심/UKC 계산에 사용하지 않습니다.')
    from services.orchestrator.tide_store import save
    try:
        result['storage'] = save(result)
    except Exception:
        result['storage'] = {'status':'FAILED', 'code':'TIDE_STORAGE_UNAVAILABLE'}
    if len(_cache) >= 128:
        _cache.pop(next(iter(_cache)))
    _cache[cache_key] = (time.monotonic(), result)
    return result


@router.get('')
def tide(station: str = Query(..., pattern=r'^DT_[0-9]{4}$'),
         date: str = Query(..., pattern=r'^[0-9]{8}$'),
         interval: int = Query(60, ge=1, le=60), page: int = Query(1, ge=1, le=100),
         page_size: int = Query(300, ge=1, le=300)):
    return fetch_tide(station, date, interval, page, page_size)


@router.get('/history')
def tide_history(station: str = Query(..., pattern=r'^DT_[0-9]{4}$'),
                 date: str = Query(..., pattern=r'^[0-9]{8}$'),
                 limit: int = Query(300, ge=1, le=1500)):
    from services.orchestrator.tide_store import history
    try:
        rows = history(station, date, limit)
    except Exception:
        fail('TIDE_STORAGE_UNAVAILABLE', 503)
    return dict(source=SOURCE, station_code=station, date=date, rows=rows,
                returned_count=len(rows), note='조회 이력이며 현재 실시간 관측을 의미하지 않습니다.')
