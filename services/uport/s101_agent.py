"""S-101 specialist for a selected, version-matched charted berth feature."""

import json

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.uport.map_router import S101_PRODUCT
from shared.schemas.agent import EvidenceItem, QueryExecutionContext


class S101AgentError(Exception):
    """Classified failure returned by the U-Port execution coordinator."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _database_error_code(exc: Exception, default: str) -> str:
    """Map PostgreSQL statement cancellation to a stable timeout error."""
    original = getattr(exc, "orig", None)
    return "TOOL_TIMEOUT" if getattr(original, "pgcode", None) == "57014" else default


class S101Agent:
    """Read one authoritative S-101 feature through the existing PostGIS path."""

    _filter_sql = """
        FROM projection.s101_feature_valid
        WHERE feature_instance_id = :feature_id
          AND dataset_id = :dataset_id
          AND dataset_version_id = :dataset_version_id
          AND feature_type_name = 'Berth'
          AND product_specification = :product
          AND geometry IS NOT NULL
    """

    def _params(self, qec: QueryExecutionContext) -> dict:
        """Take only typed IDs from the validated map-selection context."""
        ref = qec.slots.feature_instance_ref
        return {
            "feature_id": ref["feature_instance_id"],
            "dataset_id": ref["dataset_id"],
            "dataset_version_id": ref["dataset_version_id"],
            "product": S101_PRODUCT,
        }

    def validate(self, qec: QueryExecutionContext, db: Session) -> None:
        """Verify ID, dataset version and S-101 ontology class before a Tool runs."""
        try:
            db.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            row = db.execute(text("SELECT 1 " + self._filter_sql + " LIMIT 1"), self._params(qec)).first()
        except (SQLAlchemyError, UnicodeError) as exc:
            raise S101AgentError(_database_error_code(exc, "DATASET_NOT_AVAILABLE"),
                                 "S-101 database validation failed") from exc
        if row is None:
            raise S101AgentError("ENTITY_NOT_FOUND", "Selected berth was not found in the current S-101 dataset")

    def execute(self, qec: QueryExecutionContext, db: Session) -> tuple[dict, EvidenceItem]:
        """Return a factual GeoJSON feature and its source record evidence."""
        statement = text("""
            SELECT feature_instance_id, dataset_id, dataset_version_id,
                   GeometryType(geometry) AS geometry_type,
                   ST_AsGeoJSON(geometry)::json AS geometry,
                   rebuilt_at
        """ + self._filter_sql + " LIMIT 1")
        try:
            row = db.execute(statement, self._params(qec)).mappings().first()
        except (SQLAlchemyError, UnicodeError) as exc:
            raise S101AgentError(_database_error_code(exc, "TOOL_EXECUTION_ERROR"),
                                 "S-101 berth lookup failed") from exc
        if row is None:
            raise S101AgentError("ENTITY_NOT_FOUND", "Selected berth disappeared before lookup completed")
        geometry = row["geometry"]
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        if not isinstance(geometry, dict) or geometry.get("type") not in {"Point", "LineString", "Polygon", "MultiPolygon"}:
            raise S101AgentError("INVALID_GEOMETRY", "S-101 berth geometry is invalid")
        feature_id = str(row["feature_instance_id"])
        feature = {
            "type": "Feature", "id": feature_id, "geometry": geometry,
            "properties": {
                "feature_type": "Berth", "dataset_id": str(row["dataset_id"]),
                "dataset_version_id": str(row["dataset_version_id"]),
            },
        }
        evidence = EvidenceItem(
            evidence_id=f"s101-berth-{feature_id}", evidence_type="spatial_feature",
            summary="Verified S-101 Berth feature from PostGIS",
            source_ref="projection.s101_feature_valid",
            data={
                "feature_instance_id": feature_id,
                "dataset_id": str(row["dataset_id"]),
                "dataset_version_id": str(row["dataset_version_id"]),
                "product_specification": S101_PRODUCT,
                "rebuilt_at": str(row["rebuilt_at"]) if row["rebuilt_at"] else None,
            },
        )
        return feature, evidence
