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
        
        # Rule 1: Parse Context from Orchestrator
        input_assets = []
        if getattr(request, "available_datasets", None):
            for ds in request.available_datasets:
                # Mock converting DatasetVersion to asset dict for this demo
                input_assets.append({"role": "primary", "path": f"/data/{ds.dataset_id}.laz", "version": ds.version})
        else:
            # Fallback mock for testing
            input_assets = [{"role": "primary", "path": "d:/TEST_0708/TEST_0708/lidars/terra_las/pointcloud.laz", "version": "v1.0"}]

        # Rule 6: Asynchronous Job Placeholder (Currently blocking, intended for Celery)
        # In a real environment, we would return a task ID here and run in background.
        
        try:
            # Execute 15-step Preprocessing and Registration
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
            
            # Determine Status based on Quality (Rule 9)
            quality = result_data.get("quality_grade", "F")
            if quality in ["C", "F"]:
                status = AgentStatus.WAITING_FOR_REVIEW
                requires_human_review = True
            else:
                status = AgentStatus.COMPLETED
                requires_human_review = False
                
            metrics["registration_rmse"] = result_data.get("rmse")
            metrics["quality_grade"] = quality
            
            # Rule 3: Output standard Layer Specification
            processed_path = result_data.get("processed_path", "")
            output_layers.append(MapOutputLayer(layer_id="drone_processed_pc", type="PointCloudLayer", url=processed_path))

            # Rule 4: Validation Payload Generation
            val_res = self.tools.validation_payload_generation(metrics)
            tool_calls.append(ToolCallLog(tool_name="system.validation_payload", status="SUCCESS", execution_time_ms=10.0))
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
