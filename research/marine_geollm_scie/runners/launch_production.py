"""Launch restricted actual graph on an internal DB-only Docker network."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
from research.marine_geollm_scie.baselines.production_adapter import ALLOWED_DATABASES


def snapshot_selection(database, snapshot_manifest=None):
    if database not in ALLOWED_DATABASES:
        raise ValueError("Research database is not allowlisted")
    if database != "scie_pilot" and not snapshot_manifest:
        raise ValueError("Expanded research database requires explicit snapshot manifest")
    path = Path(snapshot_manifest).resolve() if snapshot_manifest else ROOT / "research/marine_geollm_scie/runs/20261029_pilot/spatial/snapshot_manifest.json"
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if database != "scie_pilot":
        if snapshot.get("status") != "LOADED_VERIFIED" or snapshot.get("db_identity") != {"container":"marine-scie-pilot-db", "database":database}:
            raise ValueError("Snapshot must be loaded and match the selected research database")
        from research.marine_geollm_scie.runners.binding_snapshot import verify_files
        verify_files(snapshot, path.parent)
    return path, snapshot


def isolation_metadata(empty_env, network_info):
    if network_info.get("Internal") is not True:
        raise RuntimeError("Research graph network must be Docker internal")
    empty_env = Path(empty_env)
    if not empty_env.is_file() or empty_env.stat().st_size != 0:
        raise RuntimeError("Dotenv mask must be an existing empty regular file")
    return {"network_internal": network_info["Internal"], "network_id": network_info.get("Id"),
        "dotenv_mask_source_size_bytes": empty_env.stat().st_size,
        "dotenv_file_blocked_by_empty_bind_mount": True}


def main(output=None, session=False, repeats=1, database="scie_pilot", snapshot_manifest=None):
    snapshot_path, snapshot = snapshot_selection(database, snapshot_manifest)
    output = (Path(output) if output else ROOT / "research/marine_geollm_scie/runs/20261030_comparison_v2/production").resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "production_rows.jsonl").exists(): raise FileExistsError(output)
    empty_env = output / "isolation.empty.env"
    empty_env.write_text("", encoding="utf-8")
    network_info = json.loads(subprocess.check_output(["docker", "network", "inspect", "marine-scie-graph-isolated"], text=True))[0]
    isolation = isolation_metadata(empty_env, network_info)
    db = "postgresql://postgres:scie_local_pilot@marine-scie-pilot-db:5432/" + database
    command = ["docker", "run", "--rm", "--name", "marine-scie-production-worker",
        "--network", "marine-scie-graph-isolated", "--label", "marine.scie.research=true",
        "--mount", f"type=bind,source={ROOT},target=/work,readonly",
        "--mount", f"type=bind,source={output},target=/out",
        "--mount", f"type=bind,source={empty_env},target=/work/.env,readonly",
        "--mount", f"type=bind,source={snapshot_path},target=/research_snapshot_manifest.json,readonly",
        "--tmpfs", "/work/data/feedback:rw", "--tmpfs", "/work/logs:rw", "--workdir", "/work",
        "--env", "SCIE_RESEARCH_DATABASE="+database, "--env", "SCIE_SNAPSHOT_MANIFEST=/research_snapshot_manifest.json",
        "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONPATH=/work",
        "--env", "OMP_NUM_THREADS=1", "--env", "OPENBLAS_NUM_THREADS=1", "--env", "MKL_NUM_THREADS=1",
        "--env", "HF_HUB_OFFLINE=1", "--env", "TRANSFORMERS_OFFLINE=1",
        "--env", "SCIE_ISOLATED_GRAPH=1", "--env", "DISABLE_LLM_API=1", "--env", "PYTHON_DOTENV_DISABLED=1",
        "--env", "OLLAMA_BASE_URL=http://127.0.0.1:9", "--env", "OPENAI_BASE_URL=http://127.0.0.1:9/v1",
        "--env", "OPENAI_API_KEY=research-no-model", "--env", "GEOLLM_CAPABILITY_PGVECTOR=false",
        "--env", "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=10000",
        "--env", "S101_DB_URL="+db, "--env", "POSTGIS_URL="+db,
        "docker-backend", "python", "-m", ("research.marine_geollm_scie.runners.production_session" if session else "research.marine_geollm_scie.baselines.production_adapter"),
        "--benchmark", "/work/research/marine_geollm_scie/benchmark/query_cases_v1.jsonl", "--output-dir", "/out"]
    if session: command += ["--repeats", str(repeats)]
    metadata = {"method": "P_current_production_no_llm", "image_id": subprocess.check_output(
        ["docker", "image", "inspect", "docker-backend", "--format", "{{.Id}}"], text=True).strip(),
        **isolation, "production_envfile_used": False, "source_mount": "/work read-only",
        "differences_from_model_baselines": ["LLM APIs disabled", "pgvector capability retrieval disabled",
            "external dependencies unreachable", "HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1; uncached Hugging Face assets cannot be downloaded",
            "frozen source subset; measured size is referenced in snapshot_manifest"],
        "import_diagnostic": {"enabled_for_session": session, "delay_seconds": 45,
            "output": "/out/import_stack.log", "contents": "stack frames only; no locals or environment; cancelled after import"},
        "research_database": database, "ephemeral_logs": "/work/logs tmpfs",
        "snapshot_manifest": {"path": str(snapshot_path),
            "sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(), "measured_metadata": snapshot},
        "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            ROOT/"services/orchestrator/graph.py", ROOT/"research/marine_geollm_scie/baselines/production_adapter.py",
            ROOT/"research/marine_geollm_scie/benchmark/query_cases_v1.jsonl"]}}
    (output / "adapter_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=2000)
    for name, content in (("launcher_stdout.log", process.stdout), ("launcher_stderr.log", process.stderr)):
        (output / name).write_text(content.replace(db, "[REDACTED_RESEARCH_DSN]"), encoding="utf-8")
    if database != "scie_pilot":
        try:
            snapshot_selection(database, snapshot_path)
            if hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != metadata['snapshot_manifest']['sha256']:
                raise ValueError("Snapshot manifest changed during observation")
        except Exception:
            (output / "snapshot_integrity_after.json").write_text(json.dumps({"verified":False}), encoding="utf-8")
            raise
        (output / "snapshot_integrity_after.json").write_text(json.dumps({"verified":True}), encoding="utf-8")
    print(json.dumps({"exit_code": process.returncode, "output_dir": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir"); parser.add_argument("--session", action="store_true")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--database", default="scie_pilot", choices=sorted(ALLOWED_DATABASES))
    parser.add_argument("--snapshot-manifest")
    args = parser.parse_args()
    main(args.output_dir, args.session, args.repeats, args.database, args.snapshot_manifest)
