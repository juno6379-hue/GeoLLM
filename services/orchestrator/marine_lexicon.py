"""Shared existing marine/S-101 vocabulary; preserves ambiguous feature candidates."""
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]


def load_terms():
    marine=yaml.safe_load((ROOT/'data/marine_term_dictionary.yaml').read_text(encoding='utf-8'))['terms']
    spatial=yaml.safe_load((ROOT/'data/s101_feature_dictionary.yaml').read_text(encoding='utf-8'))['s101_features']
    catalogue=yaml.safe_load((ROOT/'data/s101_feature_dictionary_v2.yaml').read_text(encoding='utf-8'))
    known={f['code'] for f in catalogue['features']}
    terms={label:dict(entry,registry_ref=f'data/marine_term_dictionary.yaml#terms/{label}')
           for label,entry in marine.items()}
    for label,entry in spatial.items():
        if label in terms or entry.get('verification_status')=='NEEDS_REVIEW':
            continue
        features=[code for code in entry.get('feature_candidates',[]) if code in known]
        if not features:
            continue
        terms[label]={'canonical_id':features[0] if len(features)==1 else None,
                      'maps_to_features':features,'aliases':[],
                      'registry_ref':f'data/s101_feature_dictionary.yaml#s101_features/{label}',
                      'ambiguity_policy':entry.get('ambiguity_policy'),
                      'attribute_filters':entry.get('attribute_filters',{}),
                      'catalogue_version':catalogue['version']}
    return terms,{'marine':marine,'spatial':spatial,'catalogue':catalogue}
