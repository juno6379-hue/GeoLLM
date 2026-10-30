"""Source-verified FC extracts; question-to-source interpretations remain AI DRAFT."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from research.marine_geollm_scie.runners.build_contracts_v4 import ROOT, BASE, REFERENCE, sha

PARSED = ROOT/'data/s101_feature_catalogue_v2_parsed.json'
SELECTION = {
 'Q1_01': ['Landmark','Building','LightAllAround','LightSectored','function'],
 'Q1_02': ['AnchorageArea'], 'Q1_03': ['Wreck'],
 'Q2_01': ['Landmark','Building','LightAllAround','LightSectored','colour'],
 'Q2_02': ['RestrictedArea','restriction','categoryOfRestrictedArea'],
 'Q2_03': ['Wreck'],
 'Q6_01': ['Wreck'],
 'Q6_02': ['Landmark','Building','LightAllAround','LightSectored','LateralBuoy','CardinalBuoy','IsolatedDangerBuoy','SafeWaterBuoy','SpecialPurposeGeneralBuoy','EmergencyWreckMarkingBuoy','InstallationBuoy','MooringBuoy'],
 'Q6_03': ['AnchorageArea'],
}


def local(e): return e.tag.rsplit('}',1)[-1]
def direct(e,name): return next((x for x in e if local(x)==name),None)
def text(e,name):
    child=direct(e,name)
    return child.text if child is not None else None


def catalogue(parsed_path=PARSED):
    parsed=json.loads(parsed_path.read_text(encoding='utf-8'));meta=parsed['metadata']
    xml_path=ROOT/meta['source'];raw=xml_path.read_bytes()
    if sha(raw)!=meta['sha256']:raise ValueError('FC XML hash differs from parsed source metadata')
    root=ET.fromstring(raw)
    nodes={text(e,'code'):e for e in root.iter() if local(e).startswith('S100_FC_') and text(e,'code')}
    # The version is read from the original XML, not inferred from a filename.
    for field in ('versionNumber','versionDate','productId'):
        if text(root,field)!=meta[field]:raise ValueError('FC version metadata mismatch: '+field)
    index={r['code']:(f'/{group}/{i}',r) for group in ('features','attributes') for i,r in enumerate(parsed[group])}
    return meta,xml_path,sha(raw),nodes,index


def record(code,meta,xml_path,xml_hash,nodes,index):
    e=nodes[code];locator=f"//*[local-name()='{local(e)}'][*[local-name()='code' and text()='{code}']]"
    definition=text(e,'definition')
    if code in index and definition!=index[code][1].get('definition'):
        raise ValueError('Parsed/XML definition mismatch: '+code)
    bindings=[]
    for i,b in enumerate(e):
        if local(b) not in ('attributeBinding','subAttributeBinding','featureBinding','informationBinding'):continue
        mult=direct(b,'multiplicity');lower=text(mult,'lower') if mult is not None else None
        upper=direct(mult,'upper') if mult is not None else None
        permitted=direct(b,'permittedValues')
        refs=[{'type':local(x),'ref':x.attrib['ref']} for x in b if 'ref' in x.attrib]
        binding={'kind':local(b),'references':refs,'lower':lower,
                 'upper':upper.text if upper is not None else None,
                 'unbounded':upper is not None and upper.get('infinite')=='true',
                 'permitted_values':[x.text for x in permitted] if permitted is not None else [],
                 'xml_child_index':i}
        bindings.append(binding)
    vals=direct(e,'listedValues')
    listed=[{'value':text(x,'code'),'label':text(x,'label'),'definition':text(x,'definition')} for x in vals] if vals is not None else []
    result={'code':code,'xml_type':local(e),'definition':definition,
            'permitted_primitives':[x.text for x in e if local(x)=='permittedPrimitives'],
            'bindings':bindings,'listed_values':listed,'version':meta['versionNumber'],
            'source_status':'VERIFIED_XML_EXTRACTION','source_path':str(xml_path),'source_sha256':xml_hash,
            'locator':locator,'parsed_locator':index[code][0] if code in index else None,
            'definition_sha256':sha((definition or '').encode('utf-8')),
            'xml_element_serialized_sha256':sha(ET.tostring(e,encoding='utf-8')),
            'element_hash_serialization':'xml.etree.ElementTree serialization; not a raw byte slice'}
    return result


def build():
    meta,path,digest,nodes,index=catalogue()
    refs={r['case_id']:r for r in map(json.loads,REFERENCE.read_text(encoding='utf-8').splitlines())}
    rows=[]
    for key,codes in SELECTION.items():
        cid='PILOT_'+key;ref=refs[cid];selected={};pending=list(codes)
        while pending:
            code=pending.pop(0)
            if code in selected:continue
            obj=record(code,meta,path,digest,nodes,index);selected[code]=obj
            # Include all actual attribute dependencies, including complex/nested light colour.
            for binding in obj['bindings']:
                for r in binding['references']:
                    if r['type']=='attribute' and r['ref'] in nodes and r['ref'] not in selected:pending.append(r['ref'])
        rows.append({'case_id':cid,'query':ref['query'],'annotation_status':'DRAFT','human_approval':False,
                     'review_kind':'SOURCE_VERIFIED_AI_REFERENCE_CANDIDATE','gold_promoted':False,
                     'source_reference_sha256':sha(REFERENCE.read_bytes()),
                     'fc_metadata':meta,'xml_sha256':digest,'parsed_sha256':sha(PARSED.read_bytes()),
                     'source_selection_status':'AI_INTERPRETATION_REQUIRES_REVIEW',
                     'selected_primary_codes':codes,'source_backed_claims':list(selected.values()),
                     'approved_answer_prose':ref['semantics']['approved_reference_text'],
                     'conditional_scope':ref['expected_behavior_reference_text'],
                     'unresolved':[ref['uncertainties_preserved'],
                        'FC 원문추출 검증은 질의별 필수정답집합·최소인용집합 승인과 구분한다.',
                        'DCEG 본문은 이번 XML 추출에서 검증하지 않았다. FC와 DCEG 근거를 혼용하지 않는다.'],
                     'global_codelist_is_not_feature_permission':True,
                     'spatial_instances_inferred':False})
    return rows


def run(output):
    rows=build();output.mkdir(parents=True,exist_ok=True)
    target=output/'evidence_reference_candidates.jsonl'
    with target.open('xb') as stream:stream.write(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode('utf-8'))
    lines=['# FC 원문 기반 9문항 근거·답안 후보', '',
           '원문 추출은 XML 및 판·파일 hash를 검증했다. 답안 선택과 완결성 판단은 AI 초안이며 기존 GOLD를 확대하지 않는다.', '',
           '| 사례 | 주요 원문 객체 | 검증 레코드 수 | 승인 원문 답안 | 남은 검토 |','|---|---|---|---|---|']
    for r in rows:
        cells=[r['case_id'],', '.join(r['selected_primary_codes']),str(len(r['source_backed_claims'])),r['approved_answer_prose'],r['unresolved'][0]]
        lines.append('| '+' | '.join(c.replace('|','\\|').replace('\n',' ') for c in cells)+' |')
    lines+=['','## 원문 확인값','']
    example=next(r for r in rows if r['case_id']=='PILOT_Q2_01')
    for obj in example['source_backed_claims']:
        for b in obj['bindings']:
            if any(r['ref']=='colour' for r in b['references']):
                lines.append(f"- `{obj['code']} → colour`: binding 허용코드 {', '.join(b['permitted_values']) or '(binding 제한 없음; 해당 코드목록과 구분)'}, 다중도 {b['lower']}..{'*' if b['unbounded'] else b['upper']}.")
    lines+=['','각 객체의 정확한 definition, 전체 직접 binding, 재귀 attribute 의존성, allowed code와 label, 판, XPath, 원문 hash는 JSONL에 있다. 전역 colour 코드목록 13개를 LightAllAround의 8개 허용값으로 대신하지 않는다. LightSectored는 복합 attribute 경로를 따라간다.']
    (output/'근거답안후보_KR.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    manifest={'rows':len(rows),'candidate_sha256':sha(target.read_bytes()),'xml_sha256':rows[0]['xml_sha256'],
              'generator_sha256':sha(Path(__file__).read_bytes()),'approved_v3_sha256':sha(REFERENCE.read_bytes()),'gold_modified':False}
    (output/'evidence_manifest.json').write_bytes(json.dumps(manifest,indent=2).encode('utf-8'))
    print(json.dumps(manifest))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
