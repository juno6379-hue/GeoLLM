"""Source-bound harbour cards; media is served only from existing Dataset files."""
from pathlib import Path
from urllib.parse import urlencode
import hashlib
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from services.orchestrator.harbour_prefix_receipts import verified_prefix

router = APIRouter(tags=['coastal-evidence'])
DATASET_ROOT = Path(__file__).resolve().parents[2] / 'Dataset'
LABELS = {'INTRODU':'항만 소개','VOYAGE_INF':'항해 안내','FLT_STTUS':'시설 현황',
          'TRAFFIC_IN':'교통 안내','SEA_WETHER':'해상 기상','SUPPLY_REP':'보급·수리',
          'EBBF_INFO':'조석 안내','TOUR_INFO':'주변 안내'}


def photo_path(properties, index, root=None):
    """Never turn DB paths into remote fetches or paths outside Dataset."""
    root = (root or DATASET_ROOT).resolve()
    name = str(properties.get(f'PHOTO{index}_PAT') or '').strip()
    prefix = str(properties.get('PPATH') or '').strip()
    if not name or index not in range(1, 6):
        return None
    parts = (prefix + '/' + name).replace('\\', '/').split('/')
    if any(p in ('.', '..') or ':' in p for p in parts) or name.startswith(('/', '\\')) or prefix.startswith(('/', '\\')):
        return None
    for base in (root, root / '소형선항만 안내정보'):
        candidate = base.joinpath(*[p for p in parts if p]).resolve()
        if candidate.is_relative_to(root) and candidate.suffix.lower() in {'.jpg','.jpeg','.png','.webp'} and candidate.is_file():
            return candidate
    return None


def harbour_card(row, root=None):
    props, provenance = row.get('properties') or {}, row.get('provenance') or {}
    damaged = set(provenance.get('damaged_fields') or [])
    fields, unavailable = [], []
    for key, label in LABELS.items():
        value = str(props.get(key) or '').strip()
        if not value:
            continue
        if key in damaged or '\ufffd' in value:
            partial = verified_prefix(row, key, value)
            if partial is not None:
                fields.append({'field':key,'label':label + ' · 원문 일부',
                               'text':partial['prefix'] + '\n\n[원문 일부: DBF 길이 제한으로 뒷부분 누락]',
                               'partial':True, 'prefix_receipt':partial['receipt'],
                               'missing_text_reconstructed':False})
            else:
                unavailable.append({'field':key,'label':label,'reason':'SOURCE_TEXT_DAMAGED'})
        else:
            fields.append({'field':key,'label':label,'text':value})
    sid = row['source_id']
    photos = []
    for index in range(1,6):
        reference = str(props.get(f'PHOTO{index}_PAT') or '').strip()
        if not reference:
            continue
        path = photo_path(props,index,root)
        photo = {'field':f'PHOTO{index}_PAT','reference':reference,'source_id':sid,
                 'status':'LOCAL_SOURCE_FILE_AVAILABLE' if path else 'SOURCE_ASSET_UNAVAILABLE',
                 'caption':reference, 'depiction_verified':False}
        if path:
            photo.update(url='/api/v1/harbour-photo?' + urlencode({'source_id':sid,'index':index}),
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        photos.append(photo)
    return {'source_id':sid,'name':row.get('name'),'address':props.get('ADR_KNM'),
            'publisher':props.get('ORIORG'),'source_year':props.get('ORIYR'),
            'source_file':provenance.get('source_file'),
            'source_sha256':provenance.get('source_sha256'),
            'geometry':row.get('geometry'),'geometry_role':'harbour_reference_point_not_entrance',
            'fields':fields,'unavailable_fields':unavailable,'photos':photos,
            'limitations':['원문 수록 정보이며 현행성은 확인되지 않았습니다.',
                           'DBF 필드는 길이 제한으로 일부 내용이 잘렸을 수 있습니다.',
                           '좌표는 항만 대표점이며 입구 위치가 아닙니다.',
                           '사진은 원문 필드 연결 기준이며 주변 관광지 사진이 포함될 수 있습니다.']}


@router.get('/harbour-photo')
def harbour_photo(source_id: str, index: int):
    if index not in range(1,6) or not source_id.startswith('small_harbour:') or len(source_id)>180:
        raise HTTPException(404,'사진 원본을 확인할 수 없습니다.')
    from services.orchestrator.coastal_knowledge import engine
    with engine().begin() as conn:
        row = conn.execute(text('SELECT properties FROM serving.small_harbour_guide WHERE source_id=:sid'),{'sid':source_id}).mappings().first()
    path = photo_path(row['properties'],index) if row else None
    if path is None:
        raise HTTPException(404,'사진 경로는 기록되어 있으나 연결된 원본 파일이 없습니다.')
    return FileResponse(path, headers={'X-Content-Type-Options':'nosniff'})
