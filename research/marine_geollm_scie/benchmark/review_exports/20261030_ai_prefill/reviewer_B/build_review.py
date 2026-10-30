"""AI 검수자 B의 독립 사전검토. A 답안과 모델 예측은 읽지 않는다."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).parent
FC_PATH = ROOT / 'data/s101_feature_catalogue_v2_parsed.json'
fc = json.loads(FC_PATH.read_text(encoding='utf-8'))
features = {r['code']: (i, r) for i, r in enumerate(fc['features'])}
attributes = {r['code']: (i, r) for i, r in enumerate(fc['attributes'])}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence(section, code):
    i, record = (features if section == 'features' else attributes)[code]
    return {'path': str(FC_PATH.relative_to(ROOT)), 'sha256': sha(FC_PATH),
        'locator': f'/{section}/{i}', 'code': code, 'record_sha256': hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        'source_role': 'FC 2.0.0 원문 파생 레코드', 'record': record}


# 독립적으로 작성한 작업 의미. 라벨 하나보다 수행할 작업과 근거 계약을 우선한다.
spec = {
'PILOT_Q1_01': ('개념 정의 조회', ['Landmark','Building','LightAllAround','LightSectored'], None, None,
 '등대 구조물과 광원/등화는 구분한다. 고정 구조물의 형태·기능에 따라 Landmark 또는 Building, 등화 특성에 따라 LightAllAround/LightSectored를 설명하며 단일 Lighthouse feature로 단정하지 않는다.'),
'PILOT_Q1_02': ('개념 정의 조회', ['AnchorageArea'], None, None,
 '정박 가능하거나 정박하는 구역의 FC 정의를 AnchorageArea와 연결한다. 개별 계류부표나 특정 선박 위치를 정박지의 동의어로 대체하지 않는다.'),
'PILOT_Q1_03': ('개념 정의 조회', ['Wreck'], None, None,
 'Wreck의 FC 정의와 허용 기하형식을 설명한다. 모든 침수 물체 또는 모든 장애물을 Wreck로 확대하지 않는다.'),
'PILOT_Q2_01': ('속성 소유관계 및 허용값 조회', ['Landmark','LightAllAround','LightSectored'], None, None,
 '구조물 표면색과 등화색을 구분한다. Landmark.colour와 LightAllAround.colour의 허용값 집합은 다르다. LightSectored는 sectorCharacteristics/lightSector 하위 colour 경로를 따라 검토한다.'),
'PILOT_Q2_02': ('속성 소유관계 및 허용값 조회', ['RestrictedArea'], None, None,
 '행위 제한은 restriction, 제한구역의 법적/분류상 종류는 categoryOfRestrictedArea로 구별한다. 두 code list의 숫자를 교환하지 않고 RestrictedArea binding의 실제 permitted_values만 설명한다.'),
'PILOT_Q2_03': ('객체 속성 목록 조회', ['Wreck'], None, None,
 'Wreck의 attributeBinding을 추출하여 필수/선택, 다중도, 열거값을 구별한다. featureBinding의 연관 객체나 informationBinding을 Wreck의 단순 속성으로 혼합하지 않는다.'),
'PILOT_Q3_01': ('최근접 객체 검색', ['Landmark','LightAllAround','LightSectored'], 'nearest', None,
 '독도 기준점과 등대의 대상 범주를 정한 뒤 최근접 순위를 계산한다. 반경은 원문에 없으므로 임의의 거리 제한으로 최근접을 바꾸지 않는다. 같은 시설의 구조물/등화 중복 식별 정책도 필요하다.'),
'PILOT_Q3_02': ('영역 내 객체 검색', ['AnchorageArea'], 'within', None,
 '부산항의 검증된 영역 polygon 안의 AnchorageArea를 검색한다. 항만 중심점으로 대체하거나 임의 반경 원으로 바꾸지 않는다. 영역경계와 맞닿은 객체 포함정책을 명시한다.'),
'PILOT_Q3_03': ('선택영역 교차 검색', ['Wreck'], 'intersects', None,
 'selected area는 입력 spatial_context에 없다. 선택 AOI를 요청하고 공간검색을 실행하지 않는 것이 적절하다. Wreck의 point/surface 모두 교차 판정을 지원해야 한다.'),
'PILOT_Q4_01': ('지명 반경 검색', [], 'dwithin', 5000,
 '해양지명 원천의 독도 기준점으로부터 5000m 이내 명명 객체를 검색한다. 해양지명을 Wreck 등 위험객체로 바꾸지 않는다.'),
'PILOT_Q4_02': ('지명 반경 검색', [], 'dwithin', 5000,
 '5000m는 5km와 동일한 거리다. 같은 snapshot·독도 기준점·지명범주를 적용하면 Q4_01 및 Q4_03과 동등한 공간조건이어야 한다.'),
'PILOT_Q4_03': ('지명 반경 검색', [], 'dwithin', 5000,
 '영어 marine place names와 Dokdo를 지명/기준점 의미로 해석하고 5km를 5000m로 정규화한다. 언어만 달라져 검색범주가 달라지면 안 된다.'),
'PILOT_Q5_01': ('복수 객체 반경 검색 및 객체별 근거', ['Landmark','LightAllAround','LightSectored','Wreck'], 'dwithin', 5000,
 '등대와 난파선의 두 작업을 모두 보존하고 각 반환 객체의 실제 원천을 연결한다. 등대 유형 모호성이나 한 데이터 원천의 부재를 다른 작업의 완료로 숨기지 않는다.'),
'PILOT_Q5_02': ('복수 영역 반경 검색 및 비교', ['AnchorageArea','RestrictedArea'], 'dwithin', 2000,
 '부산항 기준점과 2000m 거리조건을 고정하고 정박지/제한구역을 각각 검색·비교한다. 영역 객체를 중심점 거리만으로 판정할지 실제 geometry 최소거리로 판정할지 계약을 공개한다.'),
'PILOT_Q5_03': ('침선 반경 검색 및 속성 설명', ['Wreck'], 'dwithin', 5000,
 '독도 5000m 이내 실제 Wreck를 검색하고 반환 레코드의 속성을 FC 정의와 연결한다. FC가 허용하는 속성 목록과 개별 객체에 실제 저장된 값은 서로 다르다.'),
'PILOT_Q6_01': ('표준 원문 및 출처 조회', ['Wreck'], None, None,
 'Wreck 정의의 정확한 영문 원문과 FC 버전·파일·locator를 제공한다. 한국어 설명은 번역/해설임을 표시하며 KG 요약을 원문 인용으로 제시하지 않는다.'),
'PILOT_Q6_02': ('개념 비교 및 표준 근거', ['Landmark','Building','LightAllAround','LightSectored','LateralBuoy','CardinalBuoy','SafeWaterBuoy'], None, None,
 '등대 구조물·등화 equipment와 부유 표지의 구조/기능을 분리하여 설명한다. 부표에도 등화가 결합될 수 있으므로 빛의 존재만으로 양자를 나누지 않는다. 나열한 부표 feature는 예시이며 전체 유형 목록이라는 주장을 하지 않는다.'),
'PILOT_Q6_03': ('표준 정의 출처 조회', ['AnchorageArea'], None, None,
 'AnchorageArea의 정의를 FC2.0.0 feature 레코드와 원 XML로 역추적한다. KG의 mapsToProduct 간선만으로 정의를 입증하지 않는다.')}

blank_path = ROOT/'research/marine_geollm_scie/benchmark/review_exports/20261030_pilot18/reviewer_B/annotations_DRAFT.jsonl'
blank_rows = [json.loads(s) for s in blank_path.read_text(encoding='utf-8').splitlines()]
xml_path = ROOT/fc['metadata']['source']
xml_verified = xml_path.exists() and sha(xml_path) == fc['metadata']['sha256']
rows = []
for original in blank_rows:
    row = dict(original); case = row['case_id']; intent, targets, relation, distance, explanation = spec[case]
    spatial = relation is not None
    fc_sources = [evidence('features', code) for code in targets]
    attrs = []
    if case == 'PILOT_Q2_01': attrs = ['colour','sectorCharacteristics','lightSector']
    if case == 'PILOT_Q2_02': attrs = ['restriction','categoryOfRestrictedArea']
    if case in {'PILOT_Q2_03','PILOT_Q5_03'}: attrs = sorted({b['ref'] for b in features['Wreck'][1]['bindings'] if b['kind']=='attributeBinding' and b['ref'] in attributes})
    if case in {'PILOT_Q1_01','PILOT_Q6_02'}: attrs += ['function','categoryOfLandmark']
    fc_sources += [evidence('attributes', code) for code in attrs]
    qec = {'analysis_requirement': intent, 'target_features': targets, 'target_feature_selection_status': '모호한 등대 유형은 조건부 후보이며 확정 단일 feature가 아님' if 'Landmark' in targets else '원문 및 FC에 따른 사전검토',
        'spatial_relation': relation, 'distance_m': distance, 'reference_geometry': None,
        'crs': None, 'data_bindings': None, 'tool_bindings': None,
        'unresolved_reason': '실제 dataset/geometry/tool snapshot을 조회하지 않은 검토이므로 실행 binding 및 좌표를 확정하지 않음' if spatial else '문서/정의 조회이므로 공간 기하와 거리 및 GIS 실행 binding은 불필요',
        'execution_authority': '실제 실행 허용은 ExecutionValidator 및 원천/도구 확인 뒤에만 결정'}
    if case == 'PILOT_Q3_01': qec['nearest_k'] = 1
    notes = ['본 행은 AI 검수자B의 독립 사전검토이며 인간 정답 승인이 아니다.', 'A 답안 및 모델 실험 예측을 읽거나 사용하지 않았다.', 'KG 레코드 존재/간선 연결은 검색 보조이고 FC 의미/현재 데이터 가용성/실행 정답의 증명이 아니다.']
    uncertainty = ['human 검수에서 업무 의미와 허용 대안을 승인해야 함', 'FC2.0.0은 이 검토의 고정 버전이며 다른 판의 내용을 혼합하지 않음']
    if 'Landmark' in targets: uncertainty.append('등대가 구조물/광원/시설 전체 중 어느 의미인지 미확정. tower 또는 Light Support만으로 모든 등대를 판별할 수 없음')
    if spatial: uncertainty += ['실제 object ID·geometry·거리·빈 결과 여부는 조회하지 않아 미확정', '거리계산 CRS/측지방식·경계 포함·중복 제거·반환한도 정책은 독립 공간 oracle 작성 시 확정']
    if '독도' in row['query'] or 'Dokdo' in row['query']:
        p = ROOT/'data/public_place_anchors.json'
        fc_sources.append({'path': str(p.relative_to(ROOT)), 'sha256': sha(p), 'locator': '/places/0', 'source_role': '해양수산부 공개 좌표를 인용한 로컬 동도 기준점 후보. 독도 전체 경계/공간 gold 아님'})
        uncertainty.append('독도에는 로컬 공공원천 동도 기준점 후보가 있으나 이를 이번 oracle 기준으로 채택할지는 human 확인 필요. 기준점 존재만으로 실제 검색결과를 확정하지 않음')
    if '부산항' in row['query']: uncertainty.append('부산항 대표점/법적 항역 polygon의 원천·판본을 이번 검토에서 확정하지 않음')
    if case == 'PILOT_Q3_03': uncertainty.append('selected area가 빈 spatial_context에 제공되지 않았다. AOI를 임의 생성하지 않음')
    if not targets and spatial: uncertainty.append('marine place names는 지명 원천 범주이며 단일 S-101 feature로 고정할 수 없음')
    expected = 'FC 원문/버전/locator와 설명을 제공하며 공간검색은 요구되지 않음.'
    if spatial: expected = '기준 geometry와 대상 의미 및 dataset/tool이 확인되면 요청한 공간 연산을 실행하고 목록·근거를 제시한다. 미확정이면 구체적 확인 요청 또는 데이터 미지원 상태를 표시하며 검색0건으로 바꾸지 않는다.'
    if case == 'PILOT_Q3_03': expected = '선택 영역 geometry가 없으므로 AOI를 요청하고 공간 연산은 미실행. Wreck 정의 설명은 가능하지만 교차검색 완료를 대신하지 못한다.'
    if case.startswith('PILOT_Q5'): expected += ' 복합 하위작업별 완료/차단/미지원 상태와 근거를 따로 남기며 하나의 성공으로 전체를 성공 처리하지 않는다.'
    alternatives = ['의도 라벨 이름이 달라도 필수 작업·입출력 계약·근거가 같으면 허용한다.', '근거 부족을 명확히 밝힌 확인 요청은 근거 없는 실행 완료보다 적절하다.']
    if 'Landmark' in targets: alternatives.append('구조물 중심 설명과 등화 중심 설명을 조건부로 함께 제시하거나, 그 차이를 설명한 뒤 대상 범주를 확인받는 응답을 허용한다.')
    if case.startswith('PILOT_Q4'): alternatives.append('Q4_01/02/03은 언어·단위만 다른 동일5000m 질의로 취급하되 동일 기준점·snapshot이어야 한다.')
    row.update(annotation_status='DRAFT', annotator_id='AI_REVIEWER_B', review_kind='AI_PRE_REVIEW', human_approval=False,
        reviewed_at='2026-10-30', semantics={'intent_description': intent, 'interpretation': explanation, 'feature_candidates': targets,
        'relation': relation, 'normalized_distance_m': distance, 'fc_version': '2.0.0', 'gold_intent_label': None},
        qec_fields=qec, spatial_oracle={'status': 'UNCONFIRMED' if spatial else 'NOT_APPLICABLE', 'object_ids': None, 'geometry': None,
        'distances_m': None, 'expected_empty': None, 'reason': 'DB/실제 공간질의를 실행하지 않아 object-set·좌표·거리 gold 없음' if spatial else '표준문서 질의이므로 공간 oracle 적용 대상 아님'},
        required_evidence={'sources': fc_sources, 'xml_path': str(xml_path.relative_to(ROOT)), 'xml_sha256': fc['metadata']['sha256'],
        'xml_file_hash_verified': xml_verified, 'execution_evidence_required': spatial,
        'requirements': ['원문 record와 해설을 구분', 'FC feature-attribute binding과 하위속성 경로 확인', 'KG 근거는 원천으로 재추적'] + (['실제 반환object ID→도구→QEC→원천 lineage', '빈 결과도 실제 실행 receipt/검색범위 근거 필요'] if spatial else [])},
        expected_execution_behavior=expected, acceptable_alternatives=alternatives, uncertainties=uncertainty, review_notes=notes)
    rows.append(row)

assert len(rows) == 18 and len({r['case_id'] for r in rows}) == 18
OUT.mkdir(parents=True, exist_ok=True)
target = OUT/'annotations_DRAFT.jsonl'
with target.open('x', encoding='utf-8') as stream:
    for row in rows: stream.write(json.dumps(row, ensure_ascii=False)+'\n')
(OUT/'review_manifest.json').write_text(json.dumps({'reviewer': 'AI_REVIEWER_B', 'review_kind': 'AI_PRE_REVIEW', 'human_approval': False,
    'rows': len(rows), 'blank_source_sha256': sha(blank_path), 'output_sha256': sha(target), 'fc_parsed_sha256': sha(FC_PATH),
    'fc_xml_hash_verified': xml_verified, 'independence': 'A answers/model predictions not read; only B blank packet/query/FC/source anchor read',
    'limitations': '현재 대화의 시스템 개발 맥락은 알고 있으므로 인간 검수자 간 독립성 또는 통계적 blinded human review로 주장하지 않음'}, ensure_ascii=False, indent=2), encoding='utf-8')
print('AI_REVIEWER_B DRAFT 18 rows; XML hash verified:', xml_verified)
