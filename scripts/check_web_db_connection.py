"""Check the running website and its PostGIS-backed map API without writes.

Run with Python's standard library: python scripts/check_web_db_connection.py
"""

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen


def check(base_url: str) -> dict:
    def request(path):
        try:
            with urlopen(base_url.rstrip("/") + path, timeout=20) as response:
                return response.status, response.read(), response.headers.get_content_type()
        except HTTPError as exc:
            return exc.code, exc.read(), exc.headers.get_content_type()

    checks = []
    for path in ("/", "/uport/"):
        status, body, content_type = request(path)
        checks.append({"path": path, "status": status,
                       "passed": status == 200 and content_type == "text/html" and b"<html" in body.lower()})
    status, body, _ = request("/health")
    checks.append({"path": "/health", "status": status,
                   "passed": status == 200 and json.loads(body).get("status") == "ok"})
    for name, bbox in (("busan", "128.98,35.02,129.18,35.18"),
                       ("incheon", "126.50,37.35,126.70,37.55")):
        path = "/api/v1/uport/map/berths?bbox=" + bbox
        status, body, _ = request(path)
        result = json.loads(body)
        features = result.get("features", [])
        checks.append({"region": name, "path": path, "status": status,
                       "feature_count": len(features), "source": result.get("source"),
                       "passed": status == 200 and bool(features)
                       and result.get("type") == "FeatureCollection"
                       and result.get("source") == "projection.s101_feature_valid"
                       and result.get("product_specification") == "INT.IHO.S-101.2.0"
                       and all(f.get("geometry") and f.get("id") for f in features)})
    for bbox in ("invalid", "0,0,100,80"):
        path = "/api/v1/uport/map/berths?bbox=" + bbox
        status, _, _ = request(path)
        checks.append({"path": path, "status": status, "passed": status == 422})
    return {"base_url": base_url, "passed": all(item["passed"] for item in checks), "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    try:
        report = check(args.base_url)
    except (OSError, ValueError) as exc:
        report = {"passed": False, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["passed"] else 1)
