import os
from typing import Dict, Any, List, Optional
import time

class PointCloudProcessor:
    """
    드론 LiDAR Analysis Agent의 15단계 세부 전처리 및 정합 전담 클래스.
    모든 대용량 작업은 비동기 전환을 대비해 모듈화되어 있음.
    """

    def __init__(self, tool_registry):
        self.tools = tool_registry
        self.tool_calls = []

    def log_tool(self, name: str, start_time: float, status: str):
        duration_ms = (time.time() - start_time) * 1000
        self.tool_calls.append({
            "tool_name": name,
            "status": status,
            "execution_time_ms": duration_ms
        })

    def execute_preprocessing_and_registration(self, input_assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        result_payload = {}
        provenance = {}
        
        # 1. LAS/LAZ/E57/PLY/XYZ/COPC 입력 확인
        # Find primary point cloud asset
        pc_asset = next((a for a in input_assets if a.get("role") in ["primary", "before", "pointcloud"]), None)
        if not pc_asset:
            raise ValueError("No valid point cloud asset provided in input_assets.")
        
        file_path = pc_asset.get("path", "")
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".las", ".laz", ".e57", ".ply", ".xyz", ".copc"]:
            raise ValueError(f"Unsupported point cloud format: {ext}")
        
        provenance["input_file"] = file_path
        provenance["file_format"] = ext

        # 2. Metadata 추출
        t0 = time.time()
        metadata_res = self.tools.pdal_info(file_path)
        self.log_tool("pdal.info", t0, metadata_res.get("status", "FAILED"))
        
        if metadata_res.get("status") != "SUCCESS":
            raise RuntimeError("Failed to extract metadata from point cloud.")
            
        metadata = metadata_res.get("metadata", {})
        provenance["pdal_version"] = "2.5.3" # Mock version

        # 3 & 4. 좌표계(CRS) 및 고도기준 확인 (규칙 8)
        crs = metadata.get("srs", "")
        if not crs or "EPSG" not in crs:
            raise ValueError("CRS is missing or invalid. Needs Review or Failed.")
            
        vertical_datum_ok = True # Mock check
        if not vertical_datum_ok:
            raise ValueError("Vertical Datum is unclear.")

        # 5 & 6. 점밀도 및 Coverage 계산
        bounds = metadata.get("bounds", [0,0,0,0])
        point_count = metadata.get("point_count", 0)
        area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        density = point_count / area if area > 0 else 0
        
        if density < 1.0:
            raise ValueError(f"Point density too low: {density} pts/m2")
            
        coverage_pct = 95.0 # Mock calculation

        result_payload["metadata"] = {
            "crs": crs,
            "point_count": point_count,
            "density_pts_m2": density,
            "coverage_pct": coverage_pct
        }

        # 7, 8, 9. 노이즈 제거, 중복스캔 제거, Outlier 필터링
        t0 = time.time()
        prep_res = self.tools.point_cloud_preprocessing(file_path)
        self.log_tool("pdal.preprocessing", t0, prep_res.get("status", "FAILED"))
        clean_path = prep_res.get("output", file_path)
        
        # 10. Ground / Non-ground 분류
        t0 = time.time()
        ground_res = self.tools.ground_classification(clean_path)
        self.log_tool("pdal.ground_filter", t0, ground_res.get("status", "FAILED"))
        classified_path = ground_res.get("output", clean_path)

        # 11 & 12. Boresight Calibration & ICP Registration 지원 구조
        # 13. 전후 시점 정합
        t0 = time.time()
        reference_path = "/data/reference_terrain.laz" # Mock reference
        reg_res = self.tools.point_cloud_registration(classified_path, reference_path)
        self.log_tool("open3d.icp_registration", t0, reg_res.get("status", "FAILED"))
        provenance["open3d_version"] = "0.17.0"

        # 14. 정합오차 RMSE 계산
        rmse = reg_res.get("rmse", 999.9)
        result_payload["rmse"] = rmse

        # 15. 정합 품질등급 산정
        if rmse < 0.05:
            quality_grade = "A"
        elif rmse < 0.10:
            quality_grade = "B"
        elif rmse < 0.20:
            quality_grade = "C"
        else:
            quality_grade = "F"
            
        result_payload["quality_grade"] = quality_grade
        result_payload["processed_path"] = classified_path
        
        return {
            "result": result_payload,
            "provenance": provenance,
            "tool_calls": self.tool_calls
        }
