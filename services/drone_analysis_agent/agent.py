import time
from typing import Dict, Any, List
from shared.schemas.agent import AgentRequest, AgentResult, AgentStatus, MapOutputLayer, ToolCallLog
from services.drone_analysis_agent.tools import DroneToolRegistry
from services.drone_analysis_agent.point_cloud_processor import PointCloudProcessor

class DroneLiDARAnalysisAgent:
    """
    Independent Specialist Agent
    Platform Role: GeoLLM Orchestrator가 호출하는 드론 LiDAR/영상 분석 전문 Agent
    """
    
    def __init__(self):
        self.agent_name = "Drone LiDAR Analysis Agent"
        self.agent_version = "3.0.0"
        self.tools = DroneToolRegistry()

    def process(self, request: AgentRequest) -> AgentResult:
        tool_calls: List[ToolCallLog] = []
        provenance = {}
        output_layers = []
        metrics = {}
        
        input_assets = []
        from data.database import get_postgis_db
        from data.models.lidar_dataset import LiDARDataset
        try:
            generator = get_postgis_db()
            try:
                db = next(generator)
                if db is not None:
                    for ds in request.available_datasets or []:
                        row = db.query(LiDARDataset).filter(LiDARDataset.dataset_id == ds.dataset_id).first()
                        if row:
                            input_assets.append({"role": "primary", "path": row.file_path, "version": ds.version})
            finally:
                generator.close()
            # Execute only the implemented PDAL preprocessing.
            pc_processor = PointCloudProcessor(self.tools)
            pc_res = pc_processor.execute_preprocessing_and_registration(input_assets)
            
            result_data = pc_res["result"]
            provenance.update(pc_res["provenance"])
            
            # Map tool calls from processor
            for tc in pc_res["tool_calls"]:
                tool_calls.append(ToolCallLog(
                    tool_name=tc["tool_name"],
                    status=tc["status"],
                    execution_time_ms=tc["execution_time_ms"]
                ))
            
            quality = None
            status = AgentStatus.PARTIAL
            requires_human_review = True
            metrics["registration_rmse"] = result_data.get("rmse")
            metrics["quality_grade"] = quality
            
            # Rule 3: Output standard Layer Specification
            processed_path = result_data.get("processed_path", "")
            output_layers.append(MapOutputLayer(layer_id="drone_processed_pc", type="PointCloudLayer", url=processed_path))

            # Rule 4: Validation Payload Generation
            val_res = self.tools.validation_payload_generation(metrics)
            tool_calls.append(ToolCallLog(tool_name="system.validation_payload", status="NOT_EVALUATED", execution_time_ms=0.0))
            validation_payload = val_res
            
            structured_result = {
                "point_cloud_processing": result_data
            }
            
            # Rule 5: No final user textual answer (summary is None or minimal technical)
            return AgentResult(
                task_id=request.task_id,
                trace_id=request.trace_id,
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=status,
                summary=None,
                structured_result=structured_result,
                metrics=metrics,
                output_layers=output_layers,
                tool_calls=tool_calls,
                provenance=provenance,
                validation_payload=validation_payload,
                evidence=[processed_path]
            )

        except ValueError as ve:
            # Rule 8: Unclear CRS, Datum, etc -> FAILED
            return AgentResult(
                task_id=request.task_id,
                trace_id=request.trace_id,
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED,
                summary=None,
                warnings=[str(ve)],
                tool_calls=tool_calls,
                provenance=provenance
            )
        except Exception as e:
            return AgentResult(
                task_id=request.task_id,
                trace_id=request.trace_id,
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                status=AgentStatus.FAILED,
                summary=None,
                warnings=[f"Unexpected error: {str(e)}"],
                tool_calls=tool_calls,
                provenance=provenance
            )
