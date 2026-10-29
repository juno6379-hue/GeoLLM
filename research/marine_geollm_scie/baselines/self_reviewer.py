"""Research-only B4 reviewer. Only observable answer and usage are retained."""
import json
import time
import urllib.request

PROMPT_VERSION = "b4-contract-review-v1"


def review_prompt(qec, environment):
    return (
        'Review this marine GIS execution contract. Return JSON only: '
        '{"invalid": true or false, "reason": "brief observable contract violation or valid"}. '
        'Do not supply private reasoning. A radius query needs a valid reference geometry, '
        'a distance in meters greater than zero and at most 50000, a target feature, '
        'existing data geometry columns and registered tools. Respect SELECT permission. '
        'Compare the input against the supplied registry/environment. This is a diagnostic '
        'fixture, not evidence of successful GIS execution.\n'
        + json.dumps({"qec": qec, "environment": environment}, ensure_ascii=False)
    )


def parse_review(response):
    try:
        parsed = json.loads(response)
        if type(parsed.get("invalid")) is not bool:
            return None
        return parsed["invalid"]
    except (ValueError, AttributeError):
        return None


def review(qec, environment, model="qwen2.5:1.5b", timeout=40):
    prompt = review_prompt(qec, environment)
    payload = {"model": model, "prompt": prompt, "format": "json", "stream": False,
               "options": {"temperature": 0, "seed": 42, "num_predict": 192, "num_ctx": 8192}}
    start = time.perf_counter()
    result = {"prompt": prompt, "prompt_version": PROMPT_VERSION, "request_options": payload["options"],
              "predicted_invalid": None, "input_tokens": None, "output_tokens": None}
    try:
        request = urllib.request.Request("http://localhost:11434/api/generate",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = json.load(response)
        answer = raw.get("response", "")
        result.update(response=answer, predicted_invalid=parse_review(answer),
            input_tokens=raw.get("prompt_eval_count"), output_tokens=raw.get("eval_count"),
            done=raw.get("done"), done_reason=raw.get("done_reason"))
        result["status"] = "completed" if result["predicted_invalid"] is not None else "invalid_response"
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
    result["latency_ms"] = (time.perf_counter() - start) * 1000
    return result
