"""Preprocessing reports explicitly that registration remains unperformed."""
import time

class PointCloudProcessor:
    def __init__(self, tool_registry):
        self.tools = tool_registry

    def execute_preprocessing_and_registration(self, input_assets):
        asset = next((a for a in input_assets if a.get("role") in {"primary", "before", "pointcloud"}), None)
        if not asset or not asset.get("path"):
            raise ValueError("등록된 입력 점군을 선택해 주세요.")
        start = time.monotonic()
        result = self.tools.point_cloud_preprocessing(asset["path"])
        if result.get("status") != "SUCCESS":
            raise RuntimeError("점군 전처리가 완료되지 않았습니다.")
        return {"result": {**result, "processed_path": result["output"], "quality_grade": None},
                "provenance": {"input_file": asset["path"], "engine_version": result.get("engine_version"),
                               "pipeline_path": result.get("pipeline_path")},
                "tool_calls": [{"tool_name": "pdal.preprocessing", "status": "SUCCESS",
                                "execution_time_ms": (time.monotonic() - start) * 1000}]}
