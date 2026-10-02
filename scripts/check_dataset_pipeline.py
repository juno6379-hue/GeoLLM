"""Live evidence/Qwen comparison; observations are not human gold accuracy."""
import argparse
import json
import time
import urllib.parse
import urllib.request
from scripts.dataset_pipeline import OUT, dump


def get(endpoint,query,semantic=False):
    params=urllib.parse.urlencode(dict(query=query,**({'semantic':'true'} if semantic else {})))
    with urllib.request.urlopen('http://localhost:8000/api/v1/'+endpoint+'?'+params,timeout=240) as response:
        return json.load(response)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',action='store_true');parser.add_argument('--semantic',action='store_true')
    args=parser.parse_args(); rows=[]
    for attempt in range(90):
        try:
            with urllib.request.urlopen('http://localhost:8000/health',timeout=5) as response:
                if response.status==200:break
        except Exception:
            time.sleep(2)
    else:
        raise RuntimeError('API readiness timed out')
    for query in ['부산항 입구','해양공간관리계획','양식장','수로','없는자료XYZ987654']:
        started=time.time()
        try:
            evidence=get('dataset-evidence',query,args.semantic)
            row=dict(query=query,evidence=evidence,seconds=round(time.time()-started,3))
            if args.model and query in {'부산항 입구','해양공간관리계획'}:
                row['qwen_source_selection']=get('dataset-explanation',query)
            if args.model and query=='해양공간관리계획':
                payload=dict(model='qwen2.5:1.5b',stream=False,options=dict(num_thread=4,num_predict=220,temperature=0),
                    prompt='해양공간관리계획을 한국어로 간단히 설명하세요. 자료를 제공받지 않았으므로 모르는 수치·시행연도·법 조항은 추측하지 마세요.')
                request=urllib.request.Request('http://localhost:11434/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=240) as response:
                    raw=json.load(response)
                row['qwen_without_sources']=dict(request=payload,response=raw,authority='UNVERIFIED_MODEL_EXPLANATION',
                    comparison='Compare manually with retrieved source passages; this is not an accuracy score or execution input')
            docs=evidence.get('documents',[])
            row['checks']=dict(lookup_approved=evidence.get('execution_validation',{}).get('authority')=='ExecutionValidator',
                               no_coordinate_authority=evidence.get('coordinate_authority') is False,
                               negative_empty=not docs if query=='없는자료XYZ987654' else None)
        except Exception as exc:
            row=dict(query=query,error=str(exc))
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in {'evidence','qwen_source_selection','qwen_without_sources'}},ensure_ascii=False),flush=True)
        dump(f'runtime-{int(started)}.json',rows)


if __name__=='__main__':main()
