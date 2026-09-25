"""Resolve analysis areas from request geometry and named S-101 harbour areas."""
import math
import os
import re

import psycopg2
from psycopg2.extras import RealDictCursor
from shapely import wkt
from shapely.geometry import box, shape


class PortContextError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def request_geometry(spatial):
    """Priority: selected feature, clicked point, explicit geometry, viewport, centre."""
    if spatial.get("crs", "EPSG:4326") not in ("EPSG:4326", "4326"):
        raise PortContextError("INVALID_CRS", "분석 위치를 EPSG:4326 좌표로 제공해 주세요.")
    selected = spatial.get("selected_feature") or {}
    candidates = [
        ("selected_feature", selected.get("geometry") if isinstance(selected, dict) else None),
        ("clicked_location", spatial.get("clicked_location")),
        ("request_geometry", spatial.get("geometry")),
        ("viewport_polygon", spatial.get("viewport_polygon")),
    ]
    for method, value in candidates:
        if value is not None:
            try:
                if isinstance(value, str):
                    geom = wkt.loads(value)
                elif isinstance(value, (list, tuple)):
                    from shapely.geometry import Point
                    geom = Point(*value)
                else:
                    geom = shape(value)
            except Exception as exc:
                raise PortContextError("INVALID_GEOMETRY", "선택한 분석 위치의 좌표가 유효하지 않습니다.") from exc
            break
    else:
        bounds = spatial.get("map_bounds") or spatial.get("bbox") or spatial.get("bounds")
        if bounds is not None:
            try:
                west, south, east, north = map(float, bounds)
                if not (west < east and south < north):
                    raise ValueError()
                geom = box(west, south, east, north)
                method = "viewport_bounds"
            except (TypeError, ValueError) as exc:
                raise PortContextError("INVALID_GEOMETRY", "지도 범위를 다시 선택해 주세요.") from exc
        elif spatial.get("map_center") is not None:
            from shapely.geometry import Point
            try:
                geom = Point(*spatial["map_center"])
                method = "map_center"
            except Exception as exc:
                raise PortContextError("INVALID_GEOMETRY", "지도 중심 좌표가 유효하지 않습니다.") from exc
        else:
            return None, None
    if geom.is_empty or not geom.is_valid or len(geom.bounds) != 4:
        raise PortContextError("INVALID_GEOMETRY", "분석 위치의 geometry가 유효하지 않습니다.")
    west, south, east, north = geom.bounds
    if not all(math.isfinite(v) for v in geom.bounds) or not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise PortContextError("INVALID_GEOMETRY", "경도·위도 좌표 범위를 확인해 주세요.")
    if east - west > 2 or north - south > 2:
        raise PortContextError("AREA_TOO_LARGE", "분석할 항만 주변으로 지도 범위를 좁혀 주세요.")
    return geom.wkt, method


def resolve_port_context(query, spatial):
    """Explicit named harbour wins over map context; no seed-coordinate fallback."""
    explicit_port = re.search(r"(?<![가-힣])([가-힣]+항)(?=$|\s|의|에서|주변|반경)", query)
    supplied_geometry = None
    if not explicit_port or explicit_port.group(1) == "통항":
        supplied_geometry, _ = request_geometry(spatial)
    if not supplied_geometry and (not explicit_port or explicit_port.group(1) == "통항"):
        raise PortContextError("LOCATION_REQUIRED", "분석할 항만명 또는 지도 범위를 알려주세요.")
    url = os.getenv("S101_DB_URL")
    if not url:
        raise PortContextError("PORT_SOURCE_UNAVAILABLE", "S-101 항만 DB가 연결되지 않았습니다.")
    predicate = "product_specification = %s AND feature_type_name = 'HarbourAreaAdministrative' AND geometry IS NOT NULL AND coalesce(attributes->>'name','') <> ''"
    product = os.getenv("S101_PRODUCT_SPECIFICATION", "INT.IHO.S-101.2.0")
    compact = re.sub(r"\s+", "", query)
    try:
        with psycopg2.connect(url, connect_timeout=3) as conn:
            conn.set_session(readonly=True)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SET LOCAL statement_timeout = '5000ms'")
                cur.execute(f"SELECT DISTINCT attributes->>'name' AS name FROM projection.s101_feature_valid WHERE {predicate}", (product,))
                names = [r["name"] for r in cur.fetchall()]
                hits = [name for name in names if re.sub(r"\s+", "", name) in compact]
                hits = [name for name in hits if not any(name != other and re.sub(r"\s+", "", name) in re.sub(r"\s+", "", other) for other in hits)]
                if len(hits) > 1:
                    raise PortContextError("MULTIPLE_PORTS", "분석할 항만을 하나만 선택해 주세요: " + ", ".join(hits))
                if hits:
                    cur.execute(f"""SELECT min(feature_instance_id)::text AS source_id,
                        ST_AsText(ST_UnaryUnion(ST_Collect(geometry))) AS geometry
                        FROM projection.s101_feature_valid WHERE {predicate} AND attributes->>'name' = %s""", (product, hits[0]))
                    row = dict(cur.fetchone())
                    port, distance, method = hits[0], None, "explicit_s101_harbour"
                    # A qualified harbour entrance is not the entire harbour area.
                    if any(term in query for term in ("입구", "출구", "entrance", "exit")):
                        raise PortContextError("QUALIFIED_LOCATION_REQUIRED", "항만 입구·출구는 지도에서 분석 위치와 범위를 선택해 주세요.")
                    analysis_geometry, _ = request_geometry({"geometry": row["geometry"]})
                else:
                    unknown = re.search(r"(?<![가-힣])([가-힣]+항)(?=$|\s|의|에서|주변|반경)", query)
                    if unknown and unknown.group(1) not in {"통항"}:
                        raise PortContextError("PORT_NOT_FOUND", "요청한 항만을 S-101 항만 자료에서 확인하지 못했습니다. 지도에서 위치를 선택해 주세요.")
                    analysis_geometry, method = request_geometry(spatial)
                    if not analysis_geometry:
                        raise PortContextError("LOCATION_REQUIRED", "분석할 항만명 또는 지도 범위를 알려주세요.")
                    max_distance = float(os.getenv("NAVIGATION_PORT_MAX_DISTANCE_M", "25000"))
                    if not math.isfinite(max_distance) or max_distance <= 0:
                        raise PortContextError("INVALID_PORT_POLICY", "항만 거리 정책 설정이 유효하지 않습니다.")
                    cur.execute(f"""SELECT feature_instance_id::text AS source_id,
                        attributes->>'name' AS name, ST_AsText(geometry) AS geometry,
                        ST_Distance(geometry::geography, ST_PointOnSurface(ST_GeomFromText(%s,4326))::geography) AS distance_m
                        FROM projection.s101_feature_valid WHERE {predicate}
                        ORDER BY distance_m, feature_instance_id LIMIT 1""", (analysis_geometry, product))
                    result = cur.fetchone()
                    if not result or result["distance_m"] > max_distance:
                        raise PortContextError("PORT_TOO_DISTANT", "지도 위치 주변에 확인 가능한 항만이 없습니다. 항만 주변 범위를 선택해 주세요.")
                    row = dict(result)
                    port, distance = row["name"], float(row["distance_m"])
                return {"port": port, "geometry": analysis_geometry, "port_geometry": row["geometry"],
                        "distance_m": distance, "method": method, "source_id": row["source_id"],
                        "source_ref": "projection.s101_feature_valid", "product_specification": product}
    except psycopg2.Error as exc:
        raise PortContextError("PORT_SOURCE_UNAVAILABLE", "S-101 항만 자료를 조회할 수 없습니다. DB 연결을 확인해 주세요.") from exc
