"""보호수역을 hazard table에서 분리한 뒤 protected table만 사용하도록 정리한다."""
from __future__ import annotations

import os

import psycopg2


def main() -> None:
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise RuntimeError("S101_DB_URL 또는 POSTGIS_URL 환경변수가 필요합니다.")
    with psycopg2.connect(url, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("delete from serving.hazard_area_current where layer_id = %s", ("protected_sea_area",))
            deleted = cur.rowcount
        conn.commit()
    print(f"deleted={deleted}")


if __name__ == "__main__":
    main()
