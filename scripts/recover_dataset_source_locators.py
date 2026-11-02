"""Additional read-only HWP/worksheet adapters; preserve first audit findings."""
import json
import struct
import zlib
from collections import Counter, defaultdict
from scripts.audit_dataset_locations import ROOT, DEFAULT, source_sections, compare, norm, write


def hwp_sections(path):
    import olefile
    result={}
    with olefile.OleFileIO(path) as doc:
        flags=struct.unpack_from('<I',doc.openstream('FileHeader').read(),36)[0]
        if flags&2:raise ValueError('Encrypted HWP')
        for section in sorted(p for p in doc.listdir() if p[0]=='BodyText' and p[-1].startswith('Section')):
            raw=doc.openstream(section).read()
            if flags&1:raw=zlib.decompress(raw,-15)
            pos=0;paragraphs=[]
            while pos+4<=len(raw):
                header=struct.unpack_from('<I',raw,pos)[0];pos+=4
                tag=header&1023;size=header>>20
                if size==4095:size=struct.unpack_from('<I',raw,pos)[0];pos+=4
                if pos+size>len(raw):raise ValueError('Truncated HWP record')
                payload=raw[pos:pos+size];pos+=size
                if tag!=67:continue
                units=struct.unpack('<'+'H'*(len(payload)//2),payload[:len(payload)//2*2]);clean=[];i=0
                extended={1,2,3,4,5,6,7,8,9,11,12,14,15,16,17,18,19,20,21,22,23}
                while i<len(units):
                    code=units[i]
                    if code in extended:clean.append(' ');i+=8
                    else:clean.append(chr(code) if code>=32 else '\n' if code in {10,13} else ' ');i+=1
                paragraphs.append(''.join(clean).encode('utf-16-le',errors='surrogatepass').decode('utf-16-le',errors='replace'))
            result['/'.join(section)]='\n'.join(paragraphs)
    return result


def main():
    rows={r['chunk_id']:r for r in map(json.loads,(DEFAULT/'document_chunks.jsonl').open(encoding='utf-8'))}
    grouped=defaultdict(list)
    for path in (DEFAULT/'checkpoints').glob('*.json'):
        cache=json.loads(path.read_text(encoding='utf-8'))
        for check in cache['checks']:
            if check['text_status'] in {'LOCATOR_UNSUPPORTED','LOCATOR_NOT_FOUND'} and check['source_hash_status']=='MATCH_FULL':
                if (ROOT/check['source_file']).suffix.lower() in {'.hwp','.xls','.xlsx'}:grouped[check['source_file']].append(check)
    results=[]
    for source,checks in grouped.items():
        path=ROOT/source;sections={};error=None
        try:sections=hwp_sections(path) if path.suffix.lower()=='.hwp' else source_sections(path,[rows[c['chunk_id']] for c in checks])
        except Exception as exc:error=type(exc).__name__+': '+str(exc)[:300]
        for check in checks:
            row=rows[check['chunk_id']];locator=row['section']
            if path.suffix.lower()=='.hwp':
                expected=sections.get(locator)
                state='MATCH_NORMALIZED_HWP_SECTION' if expected is not None and norm(row['content']) in norm(expected) else 'UNVERIFIED_ADAPTER_REEXTRACTION_MISMATCH'
            else:
                state,locator=compare(row,sections)
                if state=='TEXT_MISMATCH':state='UNVERIFIED_ADAPTER_REEXTRACTION_MISMATCH'
            results.append(dict(chunk_id=check['chunk_id'],v1_status=check['text_status'],v2_status=state,source_file=source,locator=locator,extraction_error=error))
    write(DEFAULT/'recovered_locator_checks.json',dict(rows=results,counts=dict(Counter(r['v2_status'] for r in results))))
    print(json.dumps(dict(rows=len(results),counts=dict(Counter(r['v2_status'] for r in results)))))


if __name__=='__main__':main()
