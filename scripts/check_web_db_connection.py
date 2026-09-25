"""Check the running website and its PostGIS-backed map API without writes.

Run with Python's standard library: python scripts/check_web_db_connection.py
"""

import argparse
import json
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def check(base_url: str) -> dict:
    def request(path, payload=None):
        try:
            data = json.dumps(payload).encode() if payload is not None else None
            req = Request(base_url.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=20) as response:
                return response.status, response.read(), response.headers.get_content_type()
        except HTTPError as exc:
            return exc.code, exc.read(), exc.headers.get_content_type()

    checks = []
    for path in ("/", "/uport/", "/vision/react_lidar/"):
        status, body, content_type = request(path)
        checks.append({"path": path, "status": status,
                       "passed": status == 200 and content_type == "text/html" and b"<html" in body.lower()})
        if path == "/vision/react_lidar/":
            asset = re.search(rb'<script[^>]+src="([^"]+)"', body)
            if asset:
                asset_path = asset.group(1).decode()
                asset_status, _, _ = request(asset_path)
                checks.append({"path": asset_path, "status": asset_status, "passed": asset_status == 200})
            else:
                checks.append({"path": path, "passed": False, "error": "No application bundle"})
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
    for action in ("preprocess", "classify"):
        path = "/api/v1/lidar/" + action
        status, body, _ = request(path, {"dataset_id": "__connection_check_unregistered__"})
        checks.append({"path": path, "status": status,
                       "passed": status == 404 and "job_id" not in json.loads(body)})
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
