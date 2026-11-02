"""Operational answer-source audit. Does not load benchmark or holdout inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from scripts.check_geollm_web_samples import observe

ROOT = Path(__file__).resolve().parents[1]
CASES = [('busan', '부산항 입구 정보를 알려줘'),
         ('dadaepo', '다대포항 소형선항만 안내정보를 알려줘'),
         ('plan', '해양공간관리계획을 설명해줘'),
         ('farm', '양식장 관련 정보를 알려줘'),
         ('waterway', '수로 관련 정보를 알려줘'),
         ('negative', '없는자료XYZ987654에 관한 자료를 찾아줘')]


def inspect(row, negative=False):
    final = (row.get('completion') or {}).get('final_result') or {}
    structured = final.get('structured_result') or {}
    documents = {d['chunk_id']: d for d in (final.get('coastal_evidence') or {}).get('documents', [])}
    passages = structured.get('source_passages') or []
    body = final.get('answer_text') or final.get('summary') or ''
    matches = bool(passages) and all(
        p.get('quote') and p['quote'] in body and p['quote'] in documents.get(p['chunk_id'], {}).get('content', '')
        and p.get('source_sha256') == documents[p['chunk_id']].get('source_sha256')
        and p.get('source_id') == documents[p['chunk_id']].get('source_id')
        and p.get('title') and p['title'] in body for p in passages)
    qec = (final.get('orchestrator_v2') or {}).get('query_execution_context') or {}
    try:
        from shared.schemas.agent import QueryExecutionContext
        from services.orchestrator.execution_validator import is_execution_authorized
        authorized = is_execution_authorized(QueryExecutionContext.model_validate(qec))
    except (ValueError, TypeError):
        authorized = False
    checks = dict(completion=row.get('observation') == 'COMPLETED_EVENT_RECEIVED',
                  validator_authorized=authorized,
                  source_only=structured.get('coordinate_authority') is False,
                  no_spatial_execution=(structured.get('search_execution') or {}).get('status') == 'NOT_RUN',
                  document_operation=(qec.get('route_plan') or {}).get('analysis_type') == 'dataset_document_lookup',
                  no_unnecessary_location_question=not final.get('clarification_questions'))
    if negative:
        checks.update(no_unrelated_answer=not passages and not documents,
                      explicit_evidence_failure=final.get('error_code') == 'DATASET_DOCUMENT_EVIDENCE_NOT_FOUND')
    else:
        checks.update(quotes_in_source_and_answer=bool(matches), partial_not_full_claim=final.get('status') == 'PARTIAL')
    return dict(passed=all(checks.values()), checks=checks, status=final.get('status'),
                passage_count=len(passages), document_count=len(documents),
                source_ids=sorted({str(p.get('source_id')) for p in passages}),
                limitation='Retrieved-text correspondence only; original source extraction and entity correctness are separate audits.')


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    # Windows readers may briefly hold the destination during dashboard polling.
    for attempt in range(20):
        try:
            temp.replace(path)
            break
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=args.resume)
    sources = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (ROOT / 'services/orchestrator').glob('*.py')}
    manifest = args.output / 'source_hashes.json'
    if manifest.exists():
        if json.loads(manifest.read_text(encoding='utf-8')) != sources:
            raise RuntimeError('Sources changed; use a new audit directory')
    else:
        write(manifest, sources)
    checks = []

    def status(state, summary):
        write(args.output / 'status.json', dict(status=state, updated_at=datetime.now(timezone.utc).isoformat(),
              counts={'sample_queries_planned': len(CASES), 'sample_queries_observed': len(checks),
                      'sample_contracts_passed': sum(x['passed'] for x in checks)},
              summary=summary, limitations=['운영 6개 표본의 인용·본문 연결 검사이며 Dataset 전체 의미 정확도가 아닙니다.',
                    '원문 추출 정확성·지명 및 좌표 의미 검수는 별도 source/spatial 감사입니다.',
                    '논문 실험 및 홀드아웃을 사용하지 않았습니다.'],
              evidence=[{'path': (args.output / 'summary.json').resolve().relative_to(ROOT).as_posix(),
                         'sha256': hashlib.sha256((args.output / 'summary.json').read_bytes()).hexdigest()
                         if (args.output / 'summary.json').exists() else None}]))

    status('RUNNING', '기존 운영 질의의 실제 답변·근거 연결을 확인 중입니다.')
    for number, (case, query) in enumerate(CASES):
        path = args.output / (case + '.json')
        if path.exists():
            row = json.loads(path.read_text(encoding='utf-8'))
        else:
            row = observe(args.base_url, number, query, socket_timeout=180, observation_timeout=300)
            write(path, row)
        checks.append(dict(case=case, raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                           **inspect(row, negative=case == 'negative')))
        write(args.output / 'summary.json', {'checks': checks, 'paper_experiment': False, 'holdout_used': False})
        status('RUNNING', case + ' 실제 응답 점검 완료')
        print(case, checks[-1]['passed'], flush=True)
        if row.get('observation') != 'COMPLETED_EVENT_RECEIVED':
            status('BLOCKED', '관측 실패 원본 보존. 백엔드 작업 상태 확인 전 중복 실행하지 않습니다.')
            return
    unchanged = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in sources.items())
    write(args.output / 'summary.json', {'checks': checks, 'source_unchanged': unchanged,
          'paper_experiment': False, 'holdout_used': False, 'semantic_accuracy': None})
    status('PARTIALLY_VERIFIED', '표본 답변 연결 점검 종료. 전체 원천의 의미·공간 연결 완료를 뜻하지 않습니다.'
           if unchanged else '점검 중 소스 변경: 최종 소스에서 새 감사가 필요합니다.')


if __name__ == '__main__':
    main()
