@echo off
setlocal
echo ===================================================
echo       GeoLLM Multi-Agent System Startup
echo ===================================================
echo.

pushd "%~dp0"

echo [1/4] Starting Docker containers...
docker compose -f docker\docker-compose.yml up -d db backend tile-server
if errorlevel 1 goto :error
echo.

echo [2/4] Verifying S-101 2.0 database target...
docker exec an_geollm_postgis psql -U postgres -d gbhd_s101 -Atc "select product_specification || ':' || count(*) from projection.s101_feature_current group by product_specification order by product_specification;"
if errorlevel 1 goto :error
echo.

echo [3/4] Verifying GeoLLM backend health...
curl.exe -fsS http://localhost:8000/health
if errorlevel 1 goto :error
echo.

echo [4/4] Starting LiDAR React development UI on port 5173...
start "GeoLLM LiDAR React UI (5173)" cmd /k "cd /d ""%~dp0lidar_platform\frontend"" && npm run dev -- --host 0.0.0.0 --port 5173"
echo.

echo GeoLLM is ready.
echo Main UI: http://localhost:8000/
echo API docs: http://localhost:8000/docs
echo LiDAR React UI: http://localhost:5173/vision/react_lidar/
echo S-101 target DB: an_geollm_postgis/gbhd_s101 filtered to INT.IHO.S-101.2.0
echo.
popd
endlocal
exit /b 0

:error
echo.
echo GeoLLM startup failed. Review the Docker or backend output above.
popd
endlocal
exit /b 1
