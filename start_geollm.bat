@echo off
echo ===================================================
echo       GeoLLM Multi-Agent System Startup
echo ===================================================
echo.

echo [1/2] Starting Docker containers (PostGIS, ENC WMS)...
docker start an_geollm_postgis geollm-container-1
echo.

echo [2/2] Starting GeoLLM Orchestrator (FastAPI + UI) on Port 8000...
start "GeoLLM Backend Server (8000)" cmd /k "python -m uvicorn services.orchestrator.main:app --port 8000 --reload"
echo.

echo All GeoLLM services have been initiated!
echo You can now access the Main UI at http://localhost:8000/
echo You can access the Drone Lidar Analysis UI at http://localhost:8000/vision/index.html
echo.
pause
