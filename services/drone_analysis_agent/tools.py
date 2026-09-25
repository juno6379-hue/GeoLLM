"""LiDAR tools never report success without execution."""
from services.drone_analysis_agent.data_ingestion import parse_las_header
from services.drone_analysis_agent.module02_preprocessing import run_preprocessing

class DroneToolRegistry:
    @staticmethod
    def pdal_info(file_path):
        return {"status": "SUCCESS", "metadata": parse_las_header(file_path), "engine": "laspy"}

    @staticmethod
    def point_cloud_preprocessing(file_path):
        result = run_preprocessing("agent-request", file_path)
        return {"status": "SUCCESS", "output": result["output_path"], **result}

    @staticmethod
    def _unavailable(*args, **kwargs):
        raise NotImplementedError("요청한 LiDAR 처리 도구의 검증된 실행 구현이 등록되지 않았습니다.")

    point_cloud_registration = _unavailable
    ground_classification = _unavailable
    terrain_model_generation = _unavailable
    orthophoto_overlay = _unavailable
    object_extraction = _unavailable
    infrastructure_inspection = _unavailable
    change_detection = _unavailable
    generate_visualization = _unavailable

    @staticmethod
    def validation_payload_generation(metrics):
        return {"status": "NOT_EVALUATED", "metrics": metrics, "requires_human_review": True}
