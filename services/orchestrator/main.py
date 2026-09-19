from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv

load_dotenv()

from services.orchestrator.router import router as orchestrator_router
from shared.observability.logger import configure_logger
from shared.observability.telemetry import setup_telemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

configure_logger()
setup_telemetry()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Marine Geospatial Intelligence Platform - Orchestrator",
    description="Orchestrator MVP API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orchestrator_router, prefix="/api/v1")
from services.uport.map_router import router as uport_map_router
app.include_router(uport_map_router, prefix="/api/v1")
from services.uport.planning_router import router as uport_planning_router
app.include_router(uport_planning_router, prefix="/api/v1")
from services.orchestrator.place_router import router as place_router
app.include_router(place_router, prefix="/api/v1")

from services.orchestrator.lidar_router import router as lidar_router
app.include_router(lidar_router, prefix="/api/v1")

# FastAPI 라우팅에 대해 자동으로 Span을 생성하도록 계측
FastAPIInstrumentor.instrument_app(app)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/test_reload")
def test_reload():
    return {"reloaded": True}

# 결과 데이터 디렉토리 마운트 (GeoJSON 파일 다운로드 용)
# 디렉토리가 없으면 생성 (최초 구동 시 에러 방지)
os.makedirs("geollm_results", exist_ok=True)
app.mount("/data", StaticFiles(directory="geollm_results"), name="data")

from fastapi.responses import FileResponse

def _local_file_api_enabled() -> bool:
    return os.environ.get("ENABLE_LOCAL_FILE_API", "false").lower() in {"1", "true", "yes", "on"}


def _allowed_file_roots() -> list[Path]:
    raw_roots = os.environ.get("APP_ALLOWED_FILE_ROOTS")
    roots = raw_roots.split(os.pathsep) if raw_roots else [os.getcwd()]
    return [Path(root).expanduser().resolve() for root in roots if root.strip()]


def _resolve_allowed_path(path_value: str) -> Path:
    if not _local_file_api_enabled():
        raise HTTPException(status_code=404, detail="Local file API is disabled")

    candidate = Path(path_value).expanduser().resolve()
    allowed_roots = _allowed_file_roots()
    for root in allowed_roots:
        try:
            if os.path.commonpath([str(candidate), str(root)]) == str(root):
                return candidate
        except ValueError:
            continue

    raise HTTPException(status_code=403, detail="Path is outside allowed file roots")


def _filter_allowed_paths(paths: list[str]) -> list[str]:
    allowed = []
    for path in paths:
        try:
            allowed.append(str(_resolve_allowed_path(path)))
        except HTTPException:
            continue
    return allowed


@app.get("/api/v1/system/list-dir")
def list_directory(path: str = "."):
    safe_path = _resolve_allowed_path(path)
    if not safe_path.exists() or not safe_path.is_dir():
        return {"error": "Invalid path", "path": str(safe_path), "folders": []}
    
    folders = []
    try:
        for entry in os.scandir(safe_path):
            if entry.is_dir() and not entry.name.startswith('$') and not entry.name.startswith('.'):
                folders.append(entry.name)
        folders.sort()
        
        parent_path = safe_path.parent if safe_path.parent != safe_path else None
        parent = str(parent_path) if parent_path else None
        if parent:
            try:
                _resolve_allowed_path(parent)
            except HTTPException:
                parent = None
        
        return {"path": str(safe_path), "folders": folders, "parent": parent}
    except Exception as e:
        return {"error": str(e), "path": str(safe_path), "folders": []}

@app.get("/api/v1/system/pick-files")
def pick_files():
    if not _local_file_api_enabled():
        raise HTTPException(status_code=404, detail="Local file API is disabled")

    import subprocess
    import json
    import os
    import sys
    
    picker_script = os.path.join(os.path.dirname(__file__), "folder_picker.py")
    result = subprocess.run([sys.executable, picker_script], capture_output=True, text=True)
    
    try:
        paths = json.loads(result.stdout.strip())
        return {"files": _filter_allowed_paths(paths)}
    except Exception as e:
        print("Subprocess picker error:", e)
        return {"files": []}

@app.get("/api/v1/system/scan-project")
def scan_project(folder: str):
    import os
    import json
    safe_folder = _resolve_allowed_path(folder)
    
    result = {
        "ortho": None,
        "pointcloud": None,
        "dsm": None,
        "min_z": 0.0
    }
    
    if not safe_folder.is_dir():
        return result
        
    # Recursive search up to depth 3
    folder_str = str(safe_folder)
    for root, dirs, files in os.walk(safe_folder):
        root_str = str(root)
        depth = root_str[len(folder_str):].count(os.sep)
        if depth > 3:
            dirs.clear() # don't go deeper
            continue
            
        if "terra_dom" in dirs and not result["ortho"]:
            result["ortho"] = os.path.join(root, "terra_dom").replace("\\", "/")
            
        if "terra_pnts" in dirs and not result["pointcloud"]:
            ts_path = os.path.join(root, "terra_pnts", "tileset.json")
            if os.path.isfile(ts_path):
                result["pointcloud"] = ts_path.replace("\\", "/")
                
        if "terra_dsm" in dirs and not result["dsm"]:
            ts_path = os.path.join(root, "terra_dsm", "tileset.json")
            if os.path.isfile(ts_path):
                result["dsm"] = ts_path.replace("\\", "/")

    # Find min_z from tileset.json
    try:
        tileset_to_check = result["dsm"] if result["dsm"] else result["pointcloud"]
        if tileset_to_check and os.path.isfile(tileset_to_check):
            with open(tileset_to_check, "r", encoding="utf-8") as f:
                ts_data = json.load(f)
                region = ts_data.get("root", {}).get("boundingVolume", {}).get("region", [])
                if len(region) == 6:
                    # region is [west, south, east, north, minHeight, maxHeight]
                    result["min_z"] = region[4]
    except Exception as e:
        print("Error reading min_z:", e)
        
    return result

@app.get("/api/v1/local_fs/{full_path:path}")
def serve_local_fs(full_path: str):
    # Windows absolute paths from browser will look like /api/v1/local_fs/D:/path/to/file
    # full_path might be parsed as "D:/path/to/file"
    safe_path = _resolve_allowed_path(full_path)
    if safe_path.is_file():
        return FileResponse(safe_path)
    return {"error": f"File not found: {safe_path}"}

from pydantic import BaseModel
class LogMsg(BaseModel):
    level: str
    message: str

@app.post("/api/v1/system/log")
def receive_frontend_log(log: LogMsg):
    msg = f"[FRONTEND {log.level.upper()}] {log.message}\n"
    print(msg, end="")
    try:
        with open("frontend_errors.log", "a", encoding="utf-8") as f:
            f.write(msg)
    except:
        pass
    return {"status": "ok"}

# Optional local LiDAR sample mount for Windows development.
if os.path.isdir("d:/TEST_0708"):
    app.mount("/TEST_0708", StaticFiles(directory="d:/TEST_0708"), name="tiles")

class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers) -> bool:
        return False
    
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/vision", NoCacheStaticFiles(directory="ui", html=True), name="vision")

# 프론트엔드 정적 파일 마운트 (UI 용) - 루트 경로이므로 가장 마지막에 마운트해야 합니다.
# Mount the U-Port dashboard before the catch-all GeoLLM UI. StaticFiles with
# html=True serves index.html for /uport/ on direct visits and page reloads.
app.mount("/uport", NoCacheStaticFiles(directory="services/orchestrator/static/uport", html=True), name="uport")
app.mount("/", NoCacheStaticFiles(directory="services/orchestrator/static", html=True), name="static")
