"""Describe a frozen registry contract, not an actual clicked cell or live vessel."""
import re
import hashlib
from pathlib import Path
import yaml

SOURCE = 'data/traffic_layer_registry.yaml'


def is_hypothetical_traffic_description(query):
    text = str(query or '').strip()
    if not re.search(r'AIS|V[- ]?PASS|통항량|교통량', text, re.I):
        return False
    if not re.search(r'(지도|셀|격자)', text) or not re.search(r'클릭(?:했을|할|하는)\s*때|클릭하면|선택(?:했을|할)\s*때', text):
        return False
    if not re.search(r'설명(?:해\s*줘|해\s*주세요|하라|해주세요)?[.!?]*$', text):
        return False
    # Description can contain nominal '보여줄/표시할'; actual commands remain gated.
    if re.search(r'표시(?:해|하|하고|해줘)|보여\s*줘|그려|실행|계산|집계|검색|찾아|조회(?:해|하|하고)|이동|실제\s*지도.{0,30}표시|지금|현재값|최신값|선박별|개별\s*선박|MMSI|개인정보', text, re.I):
        return False
    return True


def read_traffic_description(path=None):
    path = Path(path) if path else Path(__file__).resolve().parents[2] / SOURCE
    raw = path.read_bytes()
    data = yaml.safe_load(raw)
    if not isinstance(data, dict) or not isinstance(data.get('layers'), dict):
        raise ValueError('INVALID_TRAFFIC_REGISTRY')
    rows = []
    keys = ('source', 'source_path', 'geometry_type', 'physical_table', 'geometry_column',
            'temporal_column', 'time_bucket_column', 'count_column', 'grid_id_column',
            'grid_level_column', 'tile_path_column', 'zoom_column', 'tile_x_column',
            'tile_y_column', 'available_months', 'supported_operations', 'crs', 'srid')
    for identifier, layer in data['layers'].items():
        if not isinstance(layer, dict) or layer.get('source') not in ('AIS', 'V-PASS'):
            continue
        if not layer.get('source_path') or not layer.get('physical_table'):
            raise ValueError('TRAFFIC_SOURCE_BINDING_MISSING')
        rows.append({'layer_id': identifier, **{key: layer[key] for key in keys if key in layer}})
    if not rows:
        raise ValueError('TRAFFIC_REGISTRY_EMPTY')
    return {'source_ref': SOURCE, 'source_sha256': hashlib.sha256(raw).hexdigest(),
            'version': str(data.get('version') or ''), 'rows': rows,
            'verification_scope': 'registry_contract_only', 'live_values_queried': False}


def describe_traffic_contract(evidence):
    lines = ['통항량 지도 셀을 클릭할 때 설명할 수 있는 정보는 현재 레이어 등록 계약을 기준으로 구분됩니다. 실제 클릭한 셀이나 최신 관측값을 조회한 결과는 아닙니다.']
    for row in evidence['rows']:
        months = ', '.join(str(m) for m in row.get('available_months', [])) or '등록 없음'
        if row.get('grid_id_column'):
            detail = f"셀 ID({row['grid_id_column']}), 격자 수준({row.get('grid_level_column','등록 없음')}), 통항량 필드({row.get('count_column','등록 없음')})"
        else:
            detail = f"타일 위치({row.get('tile_x_column','등록 없음')}/{row.get('tile_y_column','등록 없음')}), 확대 수준({row.get('zoom_column','등록 없음')}); 셀별 통항량 필드는 이 레이어 계약에 등록되어 있지 않습니다"
        lines.append(f"- {row['layer_id']} / {row['source']}: 원천 {row['source_path']}; 기간 필드 {row.get('time_bucket_column','등록 없음')}; 등록 월 {months}; {detail}.")
    lines.append('등록 월은 원천 계약의 기록이며 실제 DB 적재·연속성·최신성을 이번 조회에서 확인하지 않았습니다. vessel_count_total의 세부 집계 정의나 고유 선박 수 여부도 이 계약만으로 확정하지 않습니다. 개별 선박 식별정보·실시간 위치·개인정보가 제공된다고 해석하면 안 됩니다.')
    return '\n'.join(lines)
