import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _json_loads(value: Optional[str], default: Any) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _status_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


class PersistentTaskStore:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            app_data_dir = Path(os.environ.get("APP_DATA_DIR", ".")).expanduser()
            db_path = os.environ.get("APP_STATE_DB_PATH", str(app_data_dir / "geollm_state.sqlite3"))

        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            # sqlite's connection context commits/rolls back but does not close.
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestrator_tasks (
                    task_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    organization_id TEXT,
                    user_id TEXT,
                    spatial_context_json TEXT,
                    state_history_json TEXT,
                    agent_result_json TEXT,
                    result_json TEXT,
                    final_result_json TEXT,
                    snapshot_json TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(orchestrator_tasks)")}
            if "result_json" not in columns:
                conn.execute("ALTER TABLE orchestrator_tasks ADD COLUMN result_json TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_orchestrator_tasks_updated_at "
                "ON orchestrator_tasks(updated_at)"
            )

    def __contains__(self, task_id: str) -> bool:
        return self.exists(task_id)

    def __getitem__(self, task_id: str) -> dict[str, Any]:
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        return task

    def __setitem__(self, task_id: str, value: dict[str, Any]) -> None:
        self.upsert(task_id, value)

    def exists(self, task_id: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM orchestrator_tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            return row is not None

    def get(self, task_id: str, default: Any = None) -> Any:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM orchestrator_tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                return default
            return self._row_to_task(row)

    def upsert(self, task_id: str, task: dict[str, Any]) -> None:
        existing = self.get(task_id, {})
        merged = {**existing, **task, "task_id": task_id}
        now = _utc_now()
        created_at = existing.get("created_at", now)

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO orchestrator_tasks (
                    task_id, query, status, organization_id, user_id, spatial_context_json,
                    state_history_json, agent_result_json, result_json, final_result_json, snapshot_json,
                    error_message, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    query = excluded.query,
                    status = excluded.status,
                    organization_id = excluded.organization_id,
                    user_id = excluded.user_id,
                    spatial_context_json = excluded.spatial_context_json,
                    state_history_json = excluded.state_history_json,
                    agent_result_json = excluded.agent_result_json,
                    result_json = excluded.result_json,
                    final_result_json = excluded.final_result_json,
                    snapshot_json = excluded.snapshot_json,
                    error_message = excluded.error_message,
                    updated_at = excluded.updated_at
                """,
                (
                    task_id,
                    merged.get("query", ""),
                    _status_value(merged.get("status", "PENDING_OR_NOT_STARTED")),
                    merged.get("organization_id"),
                    merged.get("user_id"),
                    _json_dumps(merged.get("spatial_context")),
                    _json_dumps(merged.get("state_history", [])),
                    _json_dumps(merged.get("agent_result")),
                    _json_dumps(merged.get("result")),
                    _json_dumps(merged.get("final_result")),
                    _json_dumps(merged.get("snapshot")),
                    merged.get("error_message"),
                    created_at,
                    now,
                ),
            )

    def update(self, task_id: str, **fields: Any) -> None:
        self.upsert(task_id, fields)

    def append_query(self, task_id: str, query: str) -> str:
        task = self.get(task_id, {})
        old_query = task.get("query", "")
        new_query = f"{old_query} {query}".strip() if old_query else query
        self.upsert(task_id, {**task, "query": new_query})
        return new_query

    def _row_to_task(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "task_id": row["task_id"],
            "query": row["query"],
            "status": row["status"],
            "organization_id": row["organization_id"],
            "user_id": row["user_id"],
            "spatial_context": _json_loads(row["spatial_context_json"], None),
            "state_history": _json_loads(row["state_history_json"], []),
            "agent_result": _json_loads(row["agent_result_json"], None),
            "result": _json_loads(row["result_json"], None),
            "final_result": _json_loads(row["final_result_json"], None),
            "snapshot": _json_loads(row["snapshot_json"], None),
            "error_message": row["error_message"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
