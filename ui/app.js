document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize CesiumJS Viewer
    const viewer = new Cesium.Viewer('cesiumContainer', {
        imageryProvider: new Cesium.UrlTemplateImageryProvider({
            url: 'https://xdworld.vworld.kr/2d/Satellite/service/{z}/{x}/{y}.jpeg',
            credit: 'VWorld'
        }),
        baseLayerPicker: false,
        animation: false,
        timeline: false,
        geocoder: false,
        navigationHelpButton: false,
        homeButton: true,
        sceneModePicker: false
    });

    // 전역 변수
    let currentOrthoLayer = null;
    let loadedTilesets = []; 
    let aiDataSource = null;
    let currentTerrainModel = null;

    let tilesetInitialTransform = null;
    let currentZOffset = 0;

    // --- 프로젝트 로드 공통 함수 ---
    async function loadProjectData(projectData) {
        try {
            if (!projectData.ortho && !projectData.pointcloud && !projectData.dsm) {
                alert('해당 폴더에서 드론 3D 데이터(terra_dom, terra_pnts, terra_dsm)를 찾을 수 없습니다.');
                return;
            }
            
            // 초기화
            if (currentOrthoLayer) { viewer.imageryLayers.remove(currentOrthoLayer); currentOrthoLayer = null; }
            loadedTilesets.forEach(ts => viewer.scene.primitives.remove(ts));
            loadedTilesets = [];
            if (currentTerrainModel) { viewer.scene.primitives.remove(currentTerrainModel); currentTerrainModel = null; }
            
            const loadPromises = [];
            
            // 정사영상 로드
            if (projectData.ortho) {
                const orthoUrl = `/api/v1/local_fs/${projectData.ortho}/tile/{z}/{x}/{y}.png`;
                const provider = new Cesium.UrlTemplateImageryProvider({
                    url: orthoUrl,
                    minimumLevel: 12,
                    maximumLevel: 22,
                    rectangle: Cesium.Rectangle.fromDegrees(129.0414, 35.1046, 129.0502, 35.1133)
                });
                currentOrthoLayer = viewer.imageryLayers.addImageryProvider(provider);
            }
            
            // 점군 로드
            if (projectData.pointcloud) {
                const pcUrl = `/api/v1/local_fs/${projectData.pointcloud}`;
                const p = Cesium.Cesium3DTileset.fromUrl(pcUrl).then(ts => {
                    viewer.scene.primitives.add(ts);
                    loadedTilesets.push(ts);
                    if (ts.root) ts.initialTransform = Cesium.Matrix4.clone(ts.root.transform);
                });
                loadPromises.push(p);
            }
            
            // DSM 지형 로드
            if (projectData.dsm) {
                const dsmUrl = `/api/v1/local_fs/${projectData.dsm}`;
                const p = Cesium.Cesium3DTileset.fromUrl(dsmUrl).then(ts => {
                    viewer.scene.primitives.add(ts);
                    currentTerrainModel = ts;
                    if (ts.root) ts.initialTransform = Cesium.Matrix4.clone(ts.root.transform);
                });
                loadPromises.push(p);
            }
            
            await Promise.all(loadPromises);
            
            // 3. 자동 Z-Offset 적용
            if (projectData.min_z !== undefined && projectData.min_z !== null) {
                currentZOffset = -parseFloat(projectData.min_z);
                zOffsetSlider.value = currentZOffset.toFixed(1);
                zOffsetValueLabel.innerText = `${currentZOffset.toFixed(1)} m`;
                updateZOffset();
            }
            
            // 카메라 이동
            if (loadedTilesets.length > 0) {
                viewer.zoomTo(loadedTilesets[0]);
            } else if (currentTerrainModel) {
                viewer.zoomTo(currentTerrainModel);
            } else if (currentOrthoLayer) {
                viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(129.0458, 35.1090, 500) });
            }
        } catch (error) {
            console.error('Project loading error:', error);
            alert('프로젝트 로드 중 오류가 발생했습니다: ' + error.message);
        }
    }

    // --- React Iframe 메시지 수신 연동 ---
    window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'LOAD_3D_DATA') {
            const projectData = event.data.payload;
            
            // 1. React UI를 숨기고 Cesium 뷰어로 전환
            if(window.loadOriginalViewer) {
                window.loadOriginalViewer();
            }
            
            // 2. 3D 데이터 로드
            loadProjectData(projectData);
        }
    });

    // --- 통합 프로젝트 로드 (One-Click Project Loading) ---
    document.querySelectorAll('.btnLoadProject, #btnLoadProject').forEach(btn => btn.addEventListener('click', async () => {
        try {
            const folderPath = await pickFolderFromWeb();
            if (!folderPath) return;
            const scanResponse = await fetch(`/api/v1/system/scan-project?folder=${encodeURIComponent(folderPath)}`);
            const projectData = await scanResponse.json();
            await loadProjectData(projectData);
            alert('프로젝트 통합 로딩이 완료되었으며, 고도가 자동으로 정합(Offset) 되었습니다!');
        } catch (error) {
            console.error('Project loading error:', error);
        }
    }));

    // --- Web Folder Picker Logic ---
    let pickerResolve = null;
    let currentPickerPath = 'D:/';

    async function loadPickerDir(path) {
        try {
            const res = await fetch(`/api/v1/system/list-dir?path=${encodeURIComponent(path)}`);
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            
            currentPickerPath = data.path;
            document.getElementById('pickerCurrentPath').textContent = currentPickerPath;
            
            const listEl = document.getElementById('pickerFolderList');
            listEl.innerHTML = '';
            
            if (data.parent) {
                const backBtn = document.createElement('div');
                backBtn.style.cssText = 'padding:8px; cursor:pointer; color:#94a3b8; border-bottom:1px solid #334155;';
                backBtn.innerHTML = '<i class="fa-solid fa-level-up-alt"></i> .. (상위 폴더)';
                backBtn.onclick = () => loadPickerDir(data.parent);
                listEl.appendChild(backBtn);
            }
            
            for (let folder of data.folders) {
                const item = document.createElement('div');
                item.style.cssText = 'padding:8px; cursor:pointer; border-bottom:1px solid #334155; display:flex; align-items:center; gap:10px; transition:background 0.2s;';
                item.onmouseover = () => item.style.background = '#334155';
                item.onmouseout = () => item.style.background = 'transparent';
                item.innerHTML = `<i class="fa-solid fa-folder" style="color:#eab308;"></i> ${folder}`;
                
                let targetPath = currentPickerPath.endsWith('/') || currentPickerPath.endsWith('\\') 
                                 ? currentPickerPath + folder 
                                 : currentPickerPath + '/' + folder;
                
                item.onclick = () => loadPickerDir(targetPath);
                listEl.appendChild(item);
            }
        } catch(e) {
            alert('폴더를 불러오는 중 오류가 발생했습니다: ' + e.message);
        }
    }

    function pickFolderFromWeb() {
        return new Promise((resolve) => {
            pickerResolve = resolve;
            document.getElementById('folderPickerModal').style.display = 'flex';
            loadPickerDir('D:/');
        });
    }

    document.getElementById('btnClosePicker').addEventListener('click', () => {
        document.getElementById('folderPickerModal').style.display = 'none';
        if (pickerResolve) pickerResolve(null);
    });

    document.getElementById('btnSelectPickerFolder').addEventListener('click', () => {
        document.getElementById('folderPickerModal').style.display = 'none';
        if (pickerResolve) pickerResolve(currentPickerPath);
    });

    // --- 정사영상 단일 로드 ---
    document.querySelectorAll('.btnOrthomosaic, #btnOrthomosaic').forEach(btn => btn.addEventListener('click', async () => {
        try {
            let folderPath = await pickFolderFromWeb();
            if (!folderPath) return;
            const scanResponse = await fetch(`/api/v1/system/scan-project?folder=${encodeURIComponent(folderPath)}`);
            const projectData = await scanResponse.json();
            if (projectData.ortho) folderPath = projectData.ortho;
            
            const orthoUrl = `/api/v1/local_fs/${folderPath}/tile/{z}/{x}/{y}.png`;
            if (currentOrthoLayer) viewer.imageryLayers.remove(currentOrthoLayer);
            
            const provider = new Cesium.UrlTemplateImageryProvider({
                url: orthoUrl,
                minimumLevel: 12,
                maximumLevel: 22,
                rectangle: Cesium.Rectangle.fromDegrees(129.0414418, 35.1046503, 129.0502246, 35.1133895)
            });
            currentOrthoLayer = viewer.imageryLayers.addImageryProvider(provider);
            viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(129.0458, 35.1090, 500) });
        } catch (error) {
            console.error('Orthomosaic loading error:', error);
        }
    }));

    // --- 3D 점군 단일 로드 ---
    document.querySelectorAll('.btnPointCloud, #btnPointCloud').forEach(btn => btn.addEventListener('click', async () => {
        try {
            const folderPath = await pickFolderFromWeb();
            if (!folderPath) return;

            loadedTilesets.forEach(ts => viewer.scene.primitives.remove(ts));
            loadedTilesets = [];

            const scanResponse = await fetch(`/api/v1/system/scan-project?folder=${encodeURIComponent(folderPath)}`);
            const projectData = await scanResponse.json();
            
            let filePath = folderPath.endsWith('tileset.json') ? folderPath : `${folderPath}/tileset.json`;
            if (projectData.pointcloud) filePath = projectData.pointcloud;
            
            const tilesetUrl = `/api/v1/local_fs/${filePath}`;
            const newTileset = await Cesium.Cesium3DTileset.fromUrl(tilesetUrl);
            viewer.scene.primitives.add(newTileset);
            loadedTilesets.push(newTileset);
            
            if (newTileset.root) {
                newTileset.initialTransform = Cesium.Matrix4.clone(newTileset.root.transform);
                updateZOffset();
            }
            if (loadedTilesets.length > 0) viewer.zoomTo(loadedTilesets[0]);
        } catch (error) {
            console.error('Error loading 3D tileset:', error);
        }
    }));

    // --- Z-Offset 조절 로직 ---
    const zOffsetSlider = document.getElementById('zOffsetSlider');
    const zOffsetValueLabel = document.getElementById('zOffsetValue');
    
    function updateZOffset() {
        const translation = Cesium.Cartesian3.fromArray([0, 0, currentZOffset]);
        const offsetMatrix = Cesium.Matrix4.fromTranslation(translation);
        
        if (loadedTilesets && loadedTilesets.length > 0) {
            loadedTilesets.forEach(tileset => {
                if (tileset.initialTransform) {
                    Cesium.Matrix4.multiply(tileset.initialTransform, offsetMatrix, tileset.modelMatrix);
                }
            });
        }
        
        if (currentTerrainModel && currentTerrainModel.initialTransform) {
            Cesium.Matrix4.multiply(currentTerrainModel.initialTransform, offsetMatrix, currentTerrainModel.modelMatrix);
        }
    }

    zOffsetSlider.addEventListener('input', (e) => {
        currentZOffset = parseFloat(e.target.value);
        zOffsetValueLabel.innerText = `${currentZOffset} m`;
        updateZOffset();
    });

    // --- AI 객체 탐지 결과 로드 ---
    document.querySelectorAll('.btnAiResults, #btnAiResults').forEach(btn => btn.addEventListener('click', async () => {
        try {
            if (aiDataSource) viewer.dataSources.remove(aiDataSource);
            const geoJsonUrl = '/agent_output/detection_results.geojson';
            aiDataSource = await Cesium.GeoJsonDataSource.load(geoJsonUrl, {
                stroke: Cesium.Color.RED,
                fill: Cesium.Color.RED.withAlpha(0.2),
                strokeWidth: 3
            });
            viewer.dataSources.add(aiDataSource);
        } catch (error) {
            console.error('Error loading GeoJSON:', error);
        }
    }));

    // --- 3D DSM 지형 모델 로드 ---
    document.querySelectorAll('.btnLoadTerrain, #btnLoadTerrain').forEach(btn => btn.addEventListener('click', async () => {
        try {
            const folderPath = await pickFolderFromWeb();
            if (!folderPath) return;
            
            const scanResponse = await fetch(`/api/v1/system/scan-project?folder=${encodeURIComponent(folderPath)}`);
            const projectData = await scanResponse.json();
            
            let filePath = folderPath.endsWith('tileset.json') ? folderPath : `${folderPath}/tileset.json`;
            if (projectData.dsm) filePath = projectData.dsm;
            
            if (currentTerrainModel) {
                viewer.scene.primitives.remove(currentTerrainModel);
                currentTerrainModel = null;
            }
            
            const terrainUrl = `/api/v1/local_fs/${filePath}`;
            currentTerrainModel = await Cesium.Cesium3DTileset.fromUrl(terrainUrl);
            viewer.scene.primitives.add(currentTerrainModel);
            
            if (currentTerrainModel.root) {
                currentTerrainModel.initialTransform = Cesium.Matrix4.clone(currentTerrainModel.root.transform);
                updateZOffset();
            }
            viewer.zoomTo(currentTerrainModel);
        } catch (error) {
            console.error('Error loading DSM GLB/Tileset:', error);
        }
    }));

    // --- S-101 전자해도 (ENC) 중첩 기능 ---
    let encImageryLayer = null;
    document.querySelectorAll('.btnEncOverlay, #btnEncOverlay').forEach(btn => btn.addEventListener('click', (e) => {
        try {
            if (encImageryLayer) {
                viewer.imageryLayers.remove(encImageryLayer);
                encImageryLayer = null;
                document.querySelectorAll('.btnEncOverlay, #btnEncOverlay').forEach(b => b.style.backgroundColor = '');
            } else {
                const s101EncUrl = 'http://localhost:11000/encService';
                const encProvider = new Cesium.WebMapServiceImageryProvider({
                    url: s101EncUrl,
                    layers: 'enc101',
                    parameters: {
                        format: 'image/png',
                        transparent: true,
                        version: '1.3.0',
                        displayMode: 'base,standard,others',
                        showTeText: 'true',
                        colorPalette: 'DAY',
                        simplifiedPoint: 'false'
                    }
                });
                
                encImageryLayer = viewer.imageryLayers.addImageryProvider(encProvider);
                document.querySelectorAll('.btnEncOverlay, #btnEncOverlay').forEach(b => b.style.backgroundColor = 'rgba(96, 165, 250, 0.2)');
                
                if (!currentOrthoLayer && loadedTilesets.length === 0) {
                    viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(129.0458, 35.1090, 5000) });
                }
            }
        } catch (error) {
            console.error('Error toggling ENC Layer:', error);
        }
    }));
});
