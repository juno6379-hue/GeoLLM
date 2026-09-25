"""Real PDAL outlier filtering; no copied-input or synthetic metrics fallback."""
import json
import math
import shutil
import subprocess
import time
import uuid
from pathlib import Path
import laspy

def run_preprocessing(dataset_id, input_path, mean_k=50, std_dev_mul=1.0):
    start = time.monotonic()
    source = Path(input_path).resolve()
    if not source.is_file():
        raise FileNotFoundError("등록된 점군 파일이 서버에 없습니다.")
    if source.suffix.lower() not in {".las", ".laz"}:
        raise ValueError("전처리는 LAS/LAZ 파일만 지원합니다.")
    if mean_k < 2 or not math.isfinite(std_dev_mul) or std_dev_mul <= 0:
        raise ValueError("노이즈 필터 매개변수가 유효하지 않습니다.")
    executable = shutil.which("pdal")
    if not executable:
        raise RuntimeError("PDAL 실행 엔진이 설치되지 않아 전처리를 실행할 수 없습니다.")
    with laspy.open(source) as reader:
        before = int(reader.header.point_count)
    if before <= mean_k:
        raise ValueError("입력 점 수가 이웃 점 수보다 많아야 합니다.")
    output_dir = source.parent / "processed"
    output_dir.mkdir(exist_ok=True)
    job = uuid.uuid4().hex
    output = output_dir / f"{source.stem}_{job}.las"
    pipeline_path = output_dir / f"{job}_pipeline.json"
    pipeline = {"pipeline": [
        {"type": "readers.las", "filename": str(source)},
        {"type": "filters.outlier", "method": "statistical", "mean_k": mean_k, "multiplier": std_dev_mul},
        {"type": "filters.expression", "expression": "Classification != 7"},
        {"type": "writers.las", "filename": str(output), "forward": "all"}]}
    pipeline_path.write_text(json.dumps(pipeline, indent=2), encoding="utf-8")
    version = subprocess.run([executable, "--version"], check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    subprocess.run([executable, "pipeline", str(pipeline_path)], check=True, capture_output=True, text=True, timeout=600)
    if not output.is_file():
        raise RuntimeError("PDAL이 출력 파일을 생성하지 않았습니다.")
    with laspy.open(output) as reader:
        after = int(reader.header.point_count)
    if after > before:
        raise RuntimeError("전처리 출력 점 수가 입력 점 수보다 큽니다.")
    return {"dataset_id": dataset_id, "before_points": before, "after_points": after,
            "removed_points": before - after, "rmse": None, "unit": None,
            "processing_time": round(time.monotonic() - start, 3),
            "output_path": str(output), "pipeline_path": str(pipeline_path),
            "engine": "PDAL", "engine_version": version,
            "registration_status": "NOT_PERFORMED", "crs_transformation_status": "NOT_PERFORMED",
            "steps_completed": [{"name": "통계적 이상점 제거", "detail": f"mean_k={mean_k}, multiplier={std_dev_mul}", "status": "success"}],
            "warnings": ["정합·좌표변환·고도기준 검증은 수행하지 않았으며 RMSE를 산정하지 않았습니다."]}
