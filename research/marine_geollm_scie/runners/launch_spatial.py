"""Host launcher: isolated research DB and worker. No secret values are logged."""
import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, urlunsplit

ROOT=Path(__file__).resolve().parents[3]

def main(output, reuse_snapshot=False):
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    backend=json.loads(subprocess.check_output(['docker','inspect','geollm_backend']))[0]
    env=dict(item.split('=',1) for item in backend['Config']['Env'] if '=' in item)
    net=next(iter(backend['NetworkSettings']['Networks']))
    # Backend service DSN is consumed locally; not printed or written to results.
    source=env['S101_DB_URL']
    if not reuse_snapshot:
        subprocess.run(['docker','run','-d','--name','marine-scie-pilot-db',
                    '--label','marine.scie.research=true','--network',net,
                    '-e','POSTGRES_PASSWORD=scie_local_pilot','-e','POSTGRES_DB=scie_pilot',
                    'an-geollm-postgis:16-3.4-pgvector'],check=True,stdout=subprocess.DEVNULL)
    command=['docker','run','--rm','--name','marine-scie-spatial-worker','--network',net,
             '--label','marine.scie.research=true','-v',str(ROOT)+':/work:ro',
             '-v',str(output)+':/out','-w','/work','-e','PYTHONDONTWRITEBYTECODE=1',
             '-e','SCIE_SOURCE_DSN='+source,
             '-e','SCIE_TARGET_DSN=postgresql://postgres:scie_local_pilot@marine-scie-pilot-db:5432/scie_pilot',
             'docker-backend','python','-m','research.marine_geollm_scie.runners.spatial_pilot','--output-dir','/out']
    if reuse_snapshot:
        command.append('--reuse-snapshot')
    completed=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
    # Normal output only contains source metadata, never credentials.
    (output/'worker_stdout.log').write_text(completed.stdout,encoding='utf-8')
    (output/'worker_stderr.log').write_text(completed.stderr.replace(source,'[REDACTED_DSN]'),encoding='utf-8')
    print(json.dumps({'exit_code':completed.returncode,'output_dir':str(output)}))
    return completed.returncode

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--reuse-snapshot',action='store_true')
    args=parser.parse_args()
    raise SystemExit(main(args.output_dir,args.reuse_snapshot))
