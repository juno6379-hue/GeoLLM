"""Run the real web SSE path and wait for separately persisted Qwen comparison."""
import argparse
import json
import time
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    ready = time.monotonic() + 120
    while True:
        try:
            with urllib.request.urlopen(args.base_url + "/", timeout=5) as response:
                assert response.status == 200
            break
        except (OSError, AssertionError):
            if time.monotonic() >= ready:
                raise
            time.sleep(2)
    cases = [("해운대구로 이동", "COMPLETED"), ("해운대구 주변 위험객체를 찾아줘", None)]
    pending = []
    for index, (query, expected) in enumerate(cases):
        request = urllib.request.Request(args.base_url + "/api/v1/tasks/stream", data=json.dumps({"query": query}, ensure_ascii=False).encode(), headers={"Content-Type": "application/json"})
        events = []
        with urllib.request.urlopen(request, timeout=180) as response:
            for line in response:
                if not line.startswith(b"data: "):
                    continue
                event = json.loads(line[6:])
                events.append(event)
                if event.get("event") in {"completed", "error"}:
                    break
        (output / f"{index}-events.json").write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        started = next(e for e in events if e.get("event") == "started")
        final = events[-1]
        assert final["event"] == "completed", final
        if expected:
            assert final["status"] == expected, final.get("status")
        print(json.dumps({"query": query, "execution_status": final.get("status"), "comparison_id": started["comparison_id"]}, ensure_ascii=False), flush=True)
        pending.append((index, started["comparison_id"]))
    deadline = time.monotonic() + 600
    failures = []
    while pending and time.monotonic() < deadline:
        for index, key in pending[:]:
            with urllib.request.urlopen(args.base_url + "/api/v1/intent-comparisons/" + key, timeout=20) as response:
                record = json.load(response)
            if record["status"] in {"COMPLETED", "FAILED", "INTERRUPTED", "QUEUE_FULL"}:
                (output / f"{index}-comparison.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({"comparison_id": key, "status": record["status"], "called": record.get("called"), "rankings": record.get("rankings"), "error": record.get("error"), "latency_ms": record.get("latency_ms")}, ensure_ascii=False), flush=True)
                if record["status"] != "COMPLETED":
                    failures.append({"comparison_id": key, "error": record.get("error")})
                    pending.remove((index, key))
                    continue
                assert record["called"] and record["accepted"] and not record["execution_authority"]
                assert set(record["rankings"]) == {"rule", "ollama", "simple_mix"}
                if index == 0:
                    assert record["execution"]["execution_permission"]["scope"] == "map_view_only"
                else:
                    assert not (record["execution"].get("execution_permission") or {}).get("allowed")
                pending.remove((index, key))
        if pending:
            time.sleep(2)
    assert not pending, "Comparison deadline exceeded"
    assert not failures, failures
    print("2/2 live web comparison contracts passed", flush=True)


if __name__ == "__main__":
    main()
