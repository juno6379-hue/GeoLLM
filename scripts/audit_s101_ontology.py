"""Validate the complete parsed FC reference graph; structural completeness is not human gold."""
import argparse
import json
from pathlib import Path


def audit(catalogue):
    groups = {'featureType':catalogue['features'], 'attribute':catalogue['attributes']}
    types = {'S100_FC_InformationType':'informationType','S100_FC_Role':'role',
             'S100_FC_FeatureAssociation':'association','S100_FC_InformationAssociation':'association'}
    for row in catalogue.get('other_types',[]):
        groups.setdefault(types[row['kind']],[]).append(row)
    indexes = {kind:{r['code']:r for r in rows} for kind,rows in groups.items()}
    errors=[]; edges=[]
    for kind,rows in groups.items():
        if len(indexes[kind])!=len(rows): errors.append({'code':'DUPLICATE_CODE','type':kind})
        for row in rows:
            for b in row.get('bindings',[]):
                target=indexes.get(b['type'],{}).get(b['ref'])
                if target is None:
                    errors.append({'code':'DANGLING_REFERENCE','owner':row['code'],'binding':b})
                if b['type']=='attribute' and target:
                    allowed={v['value'] for v in target['listed_values']}
                    if allowed and not set(b['permitted_values'])<=allowed:
                        errors.append({'code':'INVALID_ENUM_RESTRICTION','owner':row['code'],'binding':b})
                if b['lower'] is not None and b['upper'] is not None and int(b['lower'])>int(b['upper']):
                    errors.append({'code':'INVALID_MULTIPLICITY','owner':row['code'],'binding':b})
                edges.append({'subject':kind+':'+row['code'],'predicate':b['kind'],
                              'object':b['type']+':'+b['ref'],'constraints':b})
    return {'status':'PASS' if not errors else 'FAILED', 'scope':'S-101 FC 2.0.0 all parsed schema entities',
            'source':catalogue['metadata'],'counts':{k:len(v) for k,v in groups.items()},
            'edge_count':len(edges),'edges':edges,'errors':errors,'human_gold':False,
            'semantic_completeness':'NOT_ESTABLISHED_BY_SCHEMA_AUDIT'}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--catalogue',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); result=audit(json.loads(a.catalogue.read_text(encoding='utf-8')))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in {'edges','source'}},ensure_ascii=False))
    raise SystemExit(result['status']!='PASS')
