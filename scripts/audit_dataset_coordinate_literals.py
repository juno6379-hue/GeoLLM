"""Validate explicit coordinate syntax, never infer a place or spatial authority."""
import json
import re
from collections import Counter
from scripts.audit_dataset_locations import DEFAULT, sha, write

NUMBER=r'[+-]?\d{1,3}(?:\.\d+)?'
ANGLE=rf'(?P<degrees>{NUMBER})(?:\s*[°º도]\s*(?:(?P<minutes>\d{{1,2}}(?:\.\d+)?)\s*[\x27′분](?:\s*(?P<seconds>\d{{1,2}}(?:\.\d+)?)\s*[\x22″초])?)?)?'
PREFIX=re.compile(rf'(?P<label>북위|남위|동경|서경|위도|경도|Latitude|Longitude|Lat\.|Lon\.)\s*[:=]?\s*{ANGLE}',re.I)
SUFFIX=re.compile(rf'(?<![\d.]){ANGLE}\s*(?P<label>[NSEW])(?![A-Za-z])')


def axis_literal(match):
    label=match['label'].lower();axis='latitude' if label in {'북위','남위','위도','latitude','lat.','n','s'} else 'longitude'
    d=float(match['degrees']);m=float(match['minutes'] or 0);s=float(match['seconds'] or 0)
    max_value=90 if axis=='latitude' else 180
    reason=None
    if not 0<=m<60 or not 0<=s<60: reason='MINUTE_SECOND_OUT_OF_RANGE'
    elif abs(d)>max_value or (abs(d)==max_value and (m or s)): reason='AXIS_OUT_OF_RANGE'
    elif d<0 and label in {'북위','남위','동경','서경','n','s','e','w'}: reason='SIGN_AND_HEMISPHERE_AMBIGUOUS'
    value=abs(d)+m/60+s/3600
    if d<0 or label in {'남위','서경','s','w'}: value=-value
    return dict(axis=axis,label=match['label'],degrees=d,minutes=m,seconds=s,value=None if reason else value,syntax_status=reason or 'RANGE_VALID',text=match.group(),start=match.start(),end=match.end())


def parse(text):
    axes=[]
    for pattern in [PREFIX,SUFFIX]:
        for match in pattern.finditer(text):
            # A bare number followed by E/N may be a code. Require degree notation
            # for suffix-only forms; prefixed latitude/longitude remains explicit.
            if pattern is SUFFIX and not re.search('[°º도]',match.group()): continue
            if any(match.start()<a['end'] and match.end()>a['start'] for a in axes): continue
            axes.append(axis_literal(match))
    axes.sort(key=lambda a:a['start'])
    pairs=[]
    consumed=set()
    for first,second in zip(axes,axes[1:]):
        if first['start'] in consumed or second['start'] in consumed: continue
        if first['axis']==second['axis'] or second['start']-first['end']>80: continue
        by_axis={a['axis']:a for a in [first,second]}
        valid=all(a['syntax_status']=='RANGE_VALID' for a in [first,second])
        pairs.append(dict(start=first['start'],end=second['end'],text=text[first['start']:second['end']],axes=[first,second],longitude=by_axis['longitude']['value'] if valid else None,latitude=by_axis['latitude']['value'] if valid else None,status='EXPLICIT_PAIR_RANGE_VALID_LOCATION_UNVERIFIED' if valid else 'INVALID_OR_AMBIGUOUS_LITERAL',coordinate_authority=False))
        consumed.update([first['start'],second['start']])
    return axes,pairs


def main():
    axes_count=0;all_pairs=[];chunks=0
    for line in (DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'):
        row=json.loads(line);chunks+=1;axes,pairs=parse(row['content'] or '');axes_count+=len(axes)
        for pair in pairs:
            all_pairs.append(dict(chunk_id=row['chunk_id'],source_id=row['source_id'],source_file=row['source_file'],source_sha256=row['source_sha256'],content_sha256=sha((row['content'] or '').encode()),source_locator=dict(page_no=row['page_no'],section=row['section']),**pair))
    with (DEFAULT/'explicit_coordinate_pairs.jsonl').open('w',encoding='utf-8') as stream:
        for pair in all_pairs:stream.write(json.dumps(pair,ensure_ascii=False)+'\n')
    summary=dict(chunks_scanned=chunks,explicit_axes=axes_count,pairs=len(all_pairs),statuses=dict(Counter(p['status'] for p in all_pairs)),limitations=['Recognized syntax subset only; pairs can be unrelated adjacent statements.', 'Range validity does not prove location, CRS, object identity, or correct source transcription.', 'Unlabelled decimal pairs remain ambiguous and are never promoted.'])
    write(DEFAULT/'coordinate_literal_summary.json',summary);print(json.dumps(summary))


if __name__=='__main__':main()
