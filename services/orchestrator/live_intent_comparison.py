"""Bounded, persisted web shadow comparison. Never grants execution permission."""
from __future__ import annotations

import json
import os
import queue
import re
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from services.orchestrator.intent_shadow import fingerprint, json_request, rankings, registry_snapshot, prepare_candidates
from services.orchestrator.slot_evidence import extract_quantities

router = APIRouter(tags=["intent-comparison"])
SHADOW_CONTRACT_VERSION = "bounded_scores_with_explicit_abstention_v3"
PROMPT = """한국어 지도/해양 질의의 의도를 평가한다. 제공한 동일 후보를 모두 한 번씩 평가한다.
원문과 문맥에 맞는 후보에 높은 점수를 준다. 맞는 후보가 없으면 abstain=true, 있으면 abstain=false.
selected 필드는 생성하지 않는다. 서버가 점수의 유일한 최댓값으로 표시용 후보를 정하며 동점이면 선택을 유보한다.
점수는 0부터 1까지 0.1 간격의 허용값 중 하나다. 확률이나 보정된 정확도가 아닌 표시용 순위 점수다.
quote와 location/radius/time 슬롯은 원문에서 그대로 인용하거나 null로 둔다. 좌표, 반경, 시간은 만들지 않는다.
이동은 지도 위치 이동이다. 분석/예측/필터/복합 작업을 단순 이동으로 대체하지 않는다.
capabilities에는 제공된 capability id만 쓴다. reason에는 해석과 미충족 작업을 간결하게 설명한다.
데이터나 도구 실행 여부는 추정하지 않는다. JSON만 출력한다."""


class Score(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str
    score: float = Field(ge=0, le=1, allow_inf_nan=False)


class Judgement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scores: list[Score] = Field(min_length=2, max_length=4)
    selected: str | None
    quote: str
    location: str | None
    radius: str | None
    time: str | None
    capabilities: list[str] = Field(max_length=6)
    reason: str = Field(max_length=400)
    needs_clarification: bool


def validate(raw, candidates, query):
    data = json.loads(raw)
    if isinstance(data.get("scores"), dict):
        data["scores"] = [{"candidate_id": key, "score": score} for key, score in data["scores"].items()]
    value = Judgement.model_validate(data)
    expected = {c["candidate_id"] for c in candidates}
    ids = [c.candidate_id for c in value.scores]
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("candidate coverage mismatch")
    if value.selected is not None:
        scores = {c.candidate_id: c.score for c in value.scores}
        if value.selected not in expected or scores[value.selected] < max(scores.values()):
            raise ValueError("selection/score mismatch")
    for span in (value.quote, value.location, value.radius, value.time):
        if span is not None and (not span or span not in query):
            raise ValueError("ungrounded query span")
    allowed = {c["id"] for row in candidates for c in row["capabilities"]}
    if set(value.capabilities) - allowed:
        raise ValueError("unknown capability")
    return value


def grounded_schema(query, candidates):
    """Constrain source spans and candidate coverage; does not certify slot meaning."""
    schema = Judgement.model_json_schema()
    ids = [row["candidate_id"] for row in candidates]
    schema["properties"]["scores"] = {"type": "object", "properties": {
        key: {"type": "number", "enum": [n / 10 for n in range(11)]} for key in ids},
        "required": ids, "additionalProperties": False}
    schema.pop("$defs", None)
    schema["properties"].pop("selected")
    schema["required"].remove("selected")
    schema["properties"]["abstain"] = {"type": "boolean"}
    schema["required"].append("abstain")
    schema["properties"]["quote"]["enum"] = [query]
    spans = set(re.findall(r"[가-힣A-Za-z0-9_.-]+", query))
    for token in list(spans):
        for particle in ("에서", "으로", "이내", "로", "를", "을", "은", "는", "의", "와", "과"):
            if token.endswith(particle) and len(token) > len(particle):
                spans.add(token[:-len(particle)])
    quantities = extract_quantities(query)
    radii = {q["raw_text"] for q in quantities if q["slot_type"] == "distance" and q["validation_status"] == "GROUNDED"}
    spans.update(q["raw_text"] for q in quantities)
    times = {span for span in spans if re.match(r"(?:오늘|어제|내일|최근|지난|올해|작년|이번주|다음주|\d.*(?:년|월|일|주|시간|분|초)|\d{4}-\d{2})", span)
             and span not in {"월별", "일별", "시간별", "구역별"}}
    for field, choices in (("location", spans), ("radius", radii), ("time", times)):
        schema["properties"][field] = {"type": ["string", "null"], "enum": [None, *sorted(choices)]}
    caps = sorted({cap["id"] for row in candidates for cap in row["capabilities"]})
    schema["properties"]["capabilities"]["items"]["enum"] = caps or ["NO_CAPABILITIES_AVAILABLE"]
    if not caps:
        schema["properties"]["capabilities"]["maxItems"] = 0
    return schema


def validate_ranked_response(raw, candidates, query):
    """The scores are the only ranking authority; never amend a model verdict.

    Legacy selected+scores responses retain their strict validator above. New
    raw responses have no selected field; derivation is explicit and shadow-only.
    """
    import jsonschema
    def unique_members(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate response member")
            result[key] = value
        return result
    data = json.loads(raw, object_pairs_hook=unique_members)
    jsonschema.validate(data, grounded_schema(query, candidates))
    scores = data["scores"]
    # Reject non-standard JSON numeric constants before deriving a ranking.
    json.dumps(data, allow_nan=False)
    maximum = max(scores.values())
    leaders = sorted(key for key, value in scores.items() if value == maximum)
    abstain = data.pop("abstain")
    selected = leaders[0] if not abstain and len(leaders) == 1 else None
    value = validate(json.dumps({**data, "selected": selected}), candidates, query)
    return value, {"contract_version": SHADOW_CONTRACT_VERSION,
                   "origin": "unique_score_argmax", "model_abstained": abstain,
                   "top_candidates": leaders, "tie_abstention": not abstain and len(leaders) > 1,
                   "used_for_execution": False, "semantic_accuracy_verified": False}


def compare(query, context, progress=None):
    from services.orchestrator.query_candidate_broker import QueryCandidateBroker, _load_registry
    trace = QueryCandidateBroker().build_trace(query, allow_ollama=False)
    candidates = prepare_candidates(trace, {"spatial_context": context}, _load_registry())
    model = os.getenv("GEOLLM_WEB_SHADOW_MODEL", "qwen2.5:1.5b")
    base = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/")
    shown = [{"candidate_id": row["candidate_id"], "capabilities": [c["id"] for c in row["capabilities"]]} for row in candidates]
    capabilities = {c["id"]: {"description": str(c.get("description") or "")[:160],
                              "input_slots": c.get("input_slots", []), "output_slots": c.get("output_slots", [])}
                    for row in candidates for c in row["capabilities"]}
    shown.sort(key=lambda row: fingerprint([query, row["candidate_id"]]))
    schema = grounded_schema(query, candidates)
    request = {"model": model, "system": PROMPT,
               "prompt": json.dumps({"query": query, "context": context, "candidates": shown, "capabilities": capabilities}, ensure_ascii=False, separators=(',', ':')),
               "format": schema, "think": False, "stream": False,
               "options": {"temperature": 0, "seed": 20260928, "num_predict": 500, "num_ctx": 4096, "num_thread": 4}}
    record = {"model": model, "candidates": candidates, "candidate_trace": trace,
              "registry_version": registry_snapshot(), "prompt_version": fingerprint(PROMPT),
              "implementation_version": {name: fingerprint((Path(__file__).parent / name).read_text(encoding="utf-8"))
                                         for name in ("live_intent_comparison.py", "query_candidate_broker.py", "semantic_prior.py", "intent_shadow.py")},
              "request": request, "request_hash": fingerprint(request), "called": False,
              "accepted": False, "calibration": "UNFITTED", "human_gold": None,
              "output_contract_version": SHADOW_CONTRACT_VERSION,
              "acceptance_scope": "structure_and_grounding_only", "semantic_review_required": True}
    start = time.monotonic()
    try:
        if progress:
            progress({**record, "phase": "MODEL_METADATA"})
        tags = json_request(base + "/api/tags", timeout=10)
        record["model_digest"] = next((m.get("digest") for m in tags.get("models", []) if m.get("name") == model), None)
        record["called"] = True
        if progress:
            progress({**record, "phase": "MODEL_INFERENCE"})
        response = json_request(base + "/api/generate", request, timeout=float(os.getenv("GEOLLM_WEB_SHADOW_TIMEOUT", "180")))
        record["raw_response"] = response
        if not response.get("done") or response.get("done_reason") == "length":
            raise ValueError("incomplete model response")
        value, derivation = validate_ranked_response(response.get("response", ""), candidates, query)
        record.update(accepted=True, judgement=value.model_dump(), selection_derivation=derivation)
        shadow = {"accepted": True, "judgement": {"assessments": [v.model_dump() for v in value.scores],
                  "selected_candidate": value.selected, "out_of_candidates": value.selected is None,
                  "requires_clarification": value.needs_clarification}}
        all_ranks = rankings(candidates, shadow)
        record["rankings"] = {k: all_ranks[k] for k in ("rule", "ollama", "simple_mix")}
        record["disagreement"] = len({v["ranking"][0] for v in record["rankings"].values()}) > 1
        record["status"] = "COMPLETED"
    except Exception as exc:
        record.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        record["rankings"] = rankings(candidates, {"accepted": False})
    record["latency_ms"] = round((time.monotonic() - start) * 1000)
    return record


class ComparisonStore:
    def __init__(self, path=None, capacity=8, worker=True):
        self.path = Path(path or os.getenv("GEOLLM_WEB_SHADOW_DB", "geollm_results/web_intent_comparison.sqlite3"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.jobs = queue.Queue(maxsize=capacity)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS comparisons (id TEXT PRIMARY KEY, record TEXT NOT NULL)")
            # The deployment uses one backend process. Do not claim interrupted work ran.
            for key, raw in db.execute("SELECT id, record FROM comparisons"):
                record = json.loads(raw)
                if record["status"] in {"QUEUED", "RUNNING"}:
                    record.update(status="INTERRUPTED", error="backend restarted before comparison completed")
                    db.execute("UPDATE comparisons SET record=? WHERE id=?", (json.dumps(record, ensure_ascii=False), key))
        if worker:
            threading.Thread(target=self.run, daemon=True, name="web-intent-shadow").start()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, key):
        with self.connect() as db:
            row = db.execute("SELECT record FROM comparisons WHERE id=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def recent(self, limit=30):
        with self.connect() as db:
            rows = db.execute("SELECT record FROM comparisons ORDER BY json_extract(record, '$.created_at') DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def update(self, key, **fields):
        with self.lock, self.connect() as db:
            row = db.execute("SELECT record FROM comparisons WHERE id=?", (key,)).fetchone()
            record = json.loads(row[0]) if row else {}
            record.update(fields)
            db.execute("INSERT OR REPLACE INTO comparisons VALUES (?,?)", (key, json.dumps(record, ensure_ascii=False, default=str)))

    def submit(self, task_id, query, context):
        key = str(uuid.uuid4())  # Every resume is a distinct request/attempt.
        self.update(key, comparison_id=key, task_id=task_id, query=query, context=context or {},
                    created_at=time.time(), status="QUEUED", mode="shadow", execution_authority=False,
                    execution={"status": "PENDING"}, human_gold=None)
        try:
            self.jobs.put_nowait(key)
        except queue.Full:
            self.update(key, status="QUEUE_FULL", called=False, error="shadow queue capacity exceeded")
        return key

    def run(self):
        while True:
            key = self.jobs.get()
            try:
                row = self.get(key)
                self.update(key, status="RUNNING", started_at=time.time())
                result = compare(row["query"], row["context"], progress=lambda fields: self.update(key, **fields))
                self.update(key, **result, finished_at=time.time())
            except Exception as exc:
                self.update(key, status="FAILED", error=f"{type(exc).__name__}: {exc}")
            finally:
                self.jobs.task_done()


_store = None
_store_lock = threading.Lock()


def store():
    global _store
    with _store_lock:
        if _store is None:
            _store = ComparisonStore()
    return _store


def observe(key, final):
    orch = final.get("orchestrator_v2") or {}
    structured = final.get("structured_result") or {}
    store().update(key, execution={"status": final.get("status"), "summary": final.get("summary"),
                   "normalized_query": (structured.get("normalization") or {}).get("normalized_query") or (orch.get("candidate_trace") or {}).get("normalized_query") or (orch.get("query_execution_context") or {}).get("normalized_query"),
                   "error_code": final.get("error_code") or structured.get("error_code"),
                   "route_plan": orch.get("route_plan"), "query_execution_context": orch.get("query_execution_context"),
                   "execution_permission": structured.get("execution_permission"), "decision_source": "existing_rules_and_execution_validator"})


@router.get("/intent-comparisons")
def list_comparisons(limit: int = Query(default=30, ge=1, le=100)):
    return {"items": store().recent(limit)}


@router.get("/intent-comparisons/{comparison_id}")
def get_comparison(comparison_id: uuid.UUID):
    result = store().get(str(comparison_id))
    if result is None:
        raise HTTPException(404, "Comparison not found")
    return result
