"""Compile explicit, source-backed search interpretations; never invent human approval."""
import json
from pathlib import Path
from services.orchestrator.reference_evaluation import load_reference_index


def build(index):
    pages = {'mof_dictionary_1':{326,309,323}, 'iho_s101_dceg_2_0_0':{205}}
    units=[u for u in index if u['locator'].get('page_1based') in pages.get(u['source_id'],set())]
    def refs(source,page):
        return [u['unit_id'] for u in units if u['source_id']==source and u['locator']['page_1based']==page]
    rows=[
        {'term':'잠제','feature':'ShorelineConstruction',
         'filters':{'categoryOfShorelineConstruction':['1'],'waterLevelEffect':['3']},
         'status':'SOURCE_BACKED_SEARCH_SUBSET','search_enabled':True,
         'scope':'Only encoded breakwaters explicitly marked always submerged; missing attributes are excluded. Not all real-world submerged dikes are covered.',
         'references':refs('mof_dictionary_1',326)+refs('iho_s101_dceg_2_0_0',205)},
        {'term':'물양장','feature':'ShorelineConstruction','filters':{'categoryOfShorelineConstruction':['6']},
         'status':'ADDITIONAL_SEMANTICS_REQUIRED','search_enabled':False,
         'scope':'Wharf is a broader candidate; small-vessel usage cannot be established from category 6 alone.',
         'references':refs('mof_dictionary_1',309)},
        {'term':'예선','feature':None,'filters':{},'status':'VESSEL_DATA_REQUIRED','search_enabled':False,
         'scope':'Tugboat is a vessel, not a fixed shoreline construction; vessel data and sense resolution are required.',
         'references':refs('mof_dictionary_1',323)},
        {'term':'선유장','feature':None,'filters':{},'status':'AMBIGUOUS_FEATURE_MAPPING','search_enabled':False,
         'scope':'A preferred label does not establish AnchorageArea, Berth or SmallCraftFacility identity.',
         'references':[]}]
    return {'contract':'marine_s101_bindings.v1','fc_sha256':
            next(u['source_sha256'] for u in index if u['source_id']=='iho_s101_fc_2_0_0'),
            'reviewer_kind':'AI_SOURCE_REVIEW','human_gold':False,'units':units,'mappings':rows}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--index',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    with a.output.open('x',encoding='utf-8') as f: json.dump(build(load_reference_index(a.index)),f,ensure_ascii=False,indent=2)
