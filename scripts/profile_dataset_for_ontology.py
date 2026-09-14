"""Dataset 폴더를 온톨로지 자동 수집용 프로파일로 변환한다.

이 스크립트는 데이터의 실행 가능 여부를 판정하지 않는다. 파일명, 포맷,
압축 파일 구성, Shapefile 헤더, 필드명 같은 결정적 메타데이터만 수집하여
후속 온톨로지 바인딩 제안 단계의 입력으로 사용한다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import warnings
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUTPUT = ROOT / "outputs" / "ontology" / "dataset_profiles.jsonl"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\s()［］\[\]{}&#;,.]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return "zip"
    if suffix in {".csv", ".tsv"}:
        return "tabular"
    if suffix in {".xls", ".xlsx"}:
        return "spreadsheet"
    if suffix in {".pdf", ".docx", ".hwp"}:
        return "document"
    if suffix in {".xml", ".json", ".yaml", ".yml"}:
        return "structured_document"
    return suffix.lstrip(".") or "unknown"


def read_cpg(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="ascii", errors="ignore").strip().lower()
    if raw in {"949", "cp949"}:
        return "cp949"
    if raw in {"utf_8", "utf-8"}:
        return "utf-8"
    return raw or None


def srid_from_prj(text: str | None) -> int | None:
    if not text:
        return None
    lowered = text.lower()
    if "false_easting" in lowered and "1000000" in lowered and "central_meridian" in lowered and "127.5" in lowered:
        return 5179
    if "kgd2002_unified" in lowered or "korea_2000_unified" in lowered:
        return 5179
    if "wgs_1984" in lowered or "wgs 84" in lowered:
        return 4326
    return None


def shapefile_profile(shp_path: Path) -> dict[str, Any]:
    try:
        import shapefile
    except ImportError:
        return {"profile_status": "SKIPPED_MISSING_PYSHP"}

    encodings = [read_cpg(shp_path.with_suffix(".cpg")), "utf-8", "cp949", "euc-kr"]
    last_error: str | None = None
    for encoding in [item for item in dict.fromkeys(encodings) if item]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                reader = shapefile.Reader(str(shp_path), encoding=encoding, encodingErrors="replace")
            fields = [field[0] for field in reader.fields[1:]]
            prj = shp_path.with_suffix(".prj")
            profile = {
                "profile_status": "PROFILED",
                "member": shp_path.name,
                "record_count": len(reader),
                "shape_type": reader.shapeTypeName,
                "fields": fields,
                "encoding": encoding,
                "native_srid": srid_from_prj(prj.read_text(encoding="utf-8", errors="ignore") if prj.exists() else None),
            }
            reader.close()
            return profile
        except Exception as exc:  # pragma: no cover - 데이터별 예외 보존 목적
            last_error = str(exc)
    return {"profile_status": "FAILED", "member": shp_path.name, "error": last_error}


def zip_member_summary(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        extensions: dict[str, int] = {}
        for name in names:
            suffix = Path(name).suffix.lower() or "<none>"
            extensions[suffix] = extensions.get(suffix, 0) + 1
        return {
            "member_count": len(infos),
            "extensions": dict(sorted(extensions.items())),
            "sample_members": names[:40],
            "shapefile_stems": sorted({str(Path(name).with_suffix("")) for name in names if Path(name).suffix.lower() == ".shp"}),
            "has_shapefile": any(Path(name).suffix.lower() == ".shp" for name in names),
        }


def profile_zip(path: Path, max_archive_bytes: int) -> dict[str, Any]:
    summary = zip_member_summary(path)
    profile: dict[str, Any] = {"zip": summary, "spatial_profile": {"has_shapefile": summary["has_shapefile"]}}
    if not summary["has_shapefile"]:
        return profile
    if path.stat().st_size > max_archive_bytes:
        profile["spatial_profile"].update(
            {
                "profile_status": "SKIPPED_LARGE_ARCHIVE",
                "reason": f"archive_size>{max_archive_bytes}",
            }
        )
        return profile
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        with zipfile.ZipFile(path) as archive:
            archive.extractall(tmpdir)
        layers = [shapefile_profile(shp) for shp in sorted(Path(tmpdir).rglob("*.shp"))]
    profile["spatial_profile"].update(
        {
            "profile_status": "PROFILED" if layers else "NO_SHP_FOUND_AFTER_EXTRACT",
            "layers": layers,
            "record_count": sum(item.get("record_count", 0) for item in layers if item.get("profile_status") == "PROFILED"),
            "fields": sorted({field for item in layers for field in item.get("fields", [])}),
            "shape_types": sorted({item.get("shape_type") for item in layers if item.get("shape_type")}),
            "native_srids": sorted({item.get("native_srid") for item in layers if item.get("native_srid")}),
        }
    )
    return profile


def text_signals(path: Path, profile: dict[str, Any]) -> list[str]:
    signals = [path.name, path.stem, path.suffix]
    zip_info = profile.get("zip") or {}
    signals.extend(zip_info.get("sample_members") or [])
    spatial = profile.get("spatial_profile") or {}
    signals.extend(spatial.get("fields") or [])
    for layer in spatial.get("layers") or []:
        signals.extend(layer.get("fields") or [])
        if layer.get("member"):
            signals.append(layer["member"])
    return [str(item) for item in signals if item]


def profile_path(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    stat = path.stat()
    fmt = detect_format(path)
    profile: dict[str, Any] = {
        "dataset_id": slugify(path.stem),
        "source_asset": str(path.relative_to(ROOT)).replace("\\", "/"),
        "file_name": path.name,
        "format": fmt,
        "file_size": stat.st_size,
        "modified_at": utc_mtime(path),
        "source_sha256": sha256_file(path) if args.hash else "SKIPPED",
    }
    if fmt == "zip":
        profile.update(profile_zip(path, args.max_archive_bytes))
    profile["text_signals"] = text_signals(path, profile)
    return profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset 파일을 온톨로지 수집용 프로파일 JSONL로 변환한다.")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--max-archive-bytes", type=int, default=250_000_000)
    parser.add_argument("--hash", action="store_true", help="대용량 파일까지 SHA-256을 계산한다.")
    parser.add_argument("--max-files", type=int, default=0, help="0이면 전체 파일을 처리한다.")
    args = parser.parse_args()

    paths = [path for path in sorted(args.dataset_dir.iterdir(), key=lambda item: item.name.lower()) if path.is_file()]
    if args.max_files:
        paths = paths[: args.max_files]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = [profile_path(path, args) for path in paths]
    with args.output.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"profiles": len(rows), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
