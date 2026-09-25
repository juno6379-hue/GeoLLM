import { useState } from 'react';
import { FolderSearch, Database, CheckCircle, Search, Settings, MountainSnow, MapPin } from 'lucide-react';

const KpiWidget = ({ icon: Icon, label, value, sub, color }: any) => (
  <div className="bg-white border border-slate-200 rounded p-2 flex items-center gap-3 w-40 shadow-sm shrink-0">
    <div className={`p-1.5 rounded-full ${color}`}>
      <Icon size={18} />
    </div>
    <div>
      <div className="text-[10px] text-slate-500 font-medium">{label}</div>
      <div className="text-sm font-bold text-slate-800 leading-tight">{value}</div>
      {sub && <div className="text-[9px] text-slate-400 leading-tight mt-0.5">{sub}</div>}
    </div>
  </div>
);

export const DataUpload = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'preprocess' | 'classify'>('upload');
  const [folderPath, setFolderPath] = useState('');
  const [scanStatus, setScanStatus] = useState<'IDLE' | 'SCANNING' | 'SUCCESS' | 'ERROR'>('IDLE');
  const [extractedMetadataList, setExtractedMetadataList] = useState<any[]>([]);
  const [processingError, setProcessingError] = useState('');
  const [visualizationData, setVisualizationData] = useState<any>(null);

  // Preprocessing State
  const [sorMeanK, setSorMeanK] = useState(50);
  const [sorStdDev, setSorStdDev] = useState(1.0);
  const [preprocessStatus, setPreprocessStatus] = useState<'IDLE' | 'RUNNING' | 'SUCCESS' | 'ERROR'>('IDLE');
  const [preprocessResult, setPreprocessResult] = useState<any>(null);

  // Classification State
  const [clothRes, setClothRes] = useState(0.5);
  const [classThresh, setClassThresh] = useState(0.5);
  const [classifyStatus, setClassifyStatus] = useState<'IDLE' | 'RUNNING' | 'SUCCESS' | 'ERROR'>('IDLE');

  const handleScan = async () => {
    if (!folderPath) return;
    setScanStatus('SCANNING');
    setProcessingError('');
    setExtractedMetadataList([]);
    setPreprocessResult(null);
    setPreprocessStatus('IDLE');
    setClassifyStatus('IDLE');
    setVisualizationData(null);
    try {
      const response = await fetch('/api/v1/lidar/register_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath, source: 'LOCAL_SCAN', project_name: '로컬 스캔 프로젝트' })
      });
      if (response.ok) {
        const data = await response.json();
        setScanStatus(data.errors?.length ? 'ERROR' : 'SUCCESS');
        if (data.errors?.length) setProcessingError(`일부 파일 등록 실패: ${data.errors.map((item: any) => item.error).join('; ')}`);
        setExtractedMetadataList(data.datasets || []);
        if (data.visualization && (data.visualization.pointcloud || data.visualization.ortho || data.visualization.dsm)) {
          setVisualizationData(data.visualization);
          window.parent.postMessage({ type: 'LOAD_3D_DATA', payload: data.visualization }, '*');
        }
      } else {
        setScanStatus('ERROR');
      }
    } catch (error) {
      setScanStatus('ERROR');
    }
  };

  const handlePreprocess = async () => {
    const datasetId = extractedMetadataList[0]?.dataset_id;
    if (!datasetId) { setProcessingError('먼저 실제 점군 데이터를 등록해 주세요.'); return; }
    setProcessingError('');

    setPreprocessStatus('RUNNING');
    try {
      const response = await fetch('/api/v1/lidar/preprocess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          sor_mean_k: sorMeanK,
          sor_std_dev_mul: sorStdDev
        })
      });
      if (response.ok) {
        const data = await response.json();
        setPreprocessResult(data.result);
        setPreprocessStatus('SUCCESS');
      } else {
        setProcessingError((await response.json()).detail || '전처리에 실패했습니다.');
        setPreprocessStatus('ERROR');
      }
    } catch {
      setPreprocessStatus('ERROR');
    }
  };

  const handleClassify = async () => {
    const datasetId = extractedMetadataList[0]?.dataset_id;
    if (!datasetId) { setProcessingError('먼저 실제 점군 데이터를 등록해 주세요.'); return; }
    setProcessingError('');

    setClassifyStatus('RUNNING');
    try {
      const response = await fetch('/api/v1/lidar/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          cloth_resolution: clothRes,
          class_threshold: classThresh
        })
      });
      const data = await response.json();
      if (response.ok && data.status === 'SUCCESS') setClassifyStatus('SUCCESS');
      else { setProcessingError(data.detail || '분류 작업이 완료되지 않았습니다.'); setClassifyStatus('ERROR'); }
    } catch {
      setClassifyStatus('ERROR');
    }
  };

  const isScanning = scanStatus === 'SCANNING';
  const hasSuccess = scanStatus === 'SUCCESS';

  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-800">
      {processingError && <div role="alert" className="p-3 text-red-700 bg-red-50">{processingError}</div>}
      {/* Top Tab Bar */}
      <div className="flex bg-white border-b border-slate-200 shrink-0 shadow-sm">
        <button onClick={() => setActiveTab('upload')} className={`flex items-center gap-2 px-6 py-3 font-bold text-sm border-b-2 transition-colors ${activeTab === 'upload' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
          <FolderSearch size={16} /> 1. 데이터 등록 & 메타데이터
        </button>
        <button onClick={() => setActiveTab('preprocess')} className={`flex items-center gap-2 px-6 py-3 font-bold text-sm border-b-2 transition-colors ${activeTab === 'preprocess' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
          <Settings size={16} /> 2. 점군 전처리 (노이즈 제거)
        </button>
        <button onClick={() => setActiveTab('classify')} className={`flex items-center gap-2 px-6 py-3 font-bold text-sm border-b-2 transition-colors ${activeTab === 'classify' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
          <MountainSnow size={16} /> 3. 지상/비지상 분류 & DEM
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden p-3 flex gap-3">

        {/* Left Side: Global KPI & Target Dataset Info */}
        <div className="w-48 flex flex-col gap-2 shrink-0 border-r border-slate-200 pr-3 overflow-y-auto">
          <KpiWidget icon={FolderSearch} label="스캔 상태" value={isScanning ? "탐색중..." : hasSuccess ? "완료됨" : "대기"} color={isScanning ? "bg-amber-100 text-amber-600" : hasSuccess ? "bg-blue-100 text-blue-600" : "bg-slate-100 text-slate-600"} />
          <KpiWidget icon={Database} label="DB 등록" value={extractedMetadataList.length + ' 건'} color="bg-indigo-100 text-indigo-600" />
          <KpiWidget icon={CheckCircle} label="3D 뷰어 상태" value={visualizationData ? "연동 됨" : "대기"} color={visualizationData ? "bg-emerald-100 text-emerald-600" : "bg-slate-100 text-slate-500"} />

          {extractedMetadataList.length > 0 && (
            <div className="mt-2 bg-blue-50 border border-blue-200 rounded p-2 text-xs">
              <div className="font-bold text-blue-800 mb-1">현재 타겟 데이터셋</div>
              <div className="font-mono text-[10px] text-blue-600 break-all">{extractedMetadataList[0].dataset_id}</div>
              <div className="text-[10px] text-slate-500 truncate mt-1" title={extractedMetadataList[0].file_name}>{extractedMetadataList[0].file_name}</div>
            </div>
          )}
        </div>

        {/* Right Side: Tab Content */}
        <div className="flex-1 overflow-y-auto bg-white rounded-lg border border-slate-200 shadow-sm p-4 relative">

          {/* TAB 1: UPLOAD */}
          {activeTab === 'upload' && (
            <div className="flex flex-col h-full">
              <div className="flex gap-2 items-center mb-4">
                <input
                  type="text" value={folderPath} onChange={e => setFolderPath(e.target.value)}
                  placeholder="D:\로컬\데이터\경로\입력..."
                  className="flex-1 border border-slate-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
                />
                <button onClick={handleScan} disabled={!folderPath || isScanning} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-1.5 px-4 rounded flex items-center gap-2 text-sm disabled:bg-slate-300">
                  {isScanning ? <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> : <Search size={16} />}
                  스캔 & 등록
                </button>
              </div>

              {scanStatus === 'ERROR' && <div className="text-xs text-red-500 font-bold mb-3">스캔 실패. 경로를 다시 확인해주세요.</div>}

              <div className="flex-1 overflow-y-auto">
                {extractedMetadataList.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-400 text-sm border border-slate-200 rounded">
                    데이터가 없습니다.
                  </div>
                ) : (
                  extractedMetadataList.map(meta => (
                    <div key={meta.dataset_id} className="border border-blue-200 rounded-xl bg-white p-6 shadow-sm flex flex-col md:flex-row gap-8 items-center mb-4 relative overflow-hidden">
                      {/* Left Side: Icon & Title */}
                      <div className="flex flex-col items-center justify-center shrink-0 w-48 border-r border-slate-100 pr-8">
                        <div className="bg-blue-50 text-blue-600 rounded-2xl p-4 mb-4 shadow-inner">
                          <Database size={48} strokeWidth={1.5} />
                        </div>
                        <div className="text-center">
                          <p className="text-xs font-bold text-slate-700">파일에서 정보를</p>
                          <p className="text-xs font-bold text-slate-700">자동으로 추출했습니다.</p>
                        </div>
                      </div>

                      {/* Right Side: Metadata List */}
                      <div className="flex-1 w-full">
                        <div className="grid grid-cols-1 divide-y divide-slate-100 border border-slate-100 rounded-lg">
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">Dataset ID</div>
                            <div className="w-2/3 text-sm font-bold text-slate-800">{meta.dataset_id}</div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">촬영일</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800">{meta.creation_date ?? "미확인"}</div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">Drone/Sensor</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800">{meta.system_id?.trim() || "미확인"}</div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">CRS</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800">{meta.crs ?? "미확인"}</div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">Bounding Box</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800 flex items-center gap-2">
                              {meta.min_x != null && meta.min_y != null ? `${meta.min_x.toFixed(2)} / ${meta.min_y.toFixed(2)}` : '미확인'}
                              <MapPin size={14} className="text-blue-600"/>
                            </div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">Point Count</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800">{meta.point_count != null ? meta.point_count.toLocaleString() : '미확인'}</div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">평균 점밀도</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800">{meta.average_density != null ? `${meta.average_density.toFixed(0)} pts/m²` : '미측정'}</div>
                          </div>
                          <div className="flex py-2 px-4 hover:bg-slate-50 transition-colors">
                            <div className="w-1/3 text-xs font-medium text-slate-500 flex items-center">RGB / Intensity</div>
                            <div className="w-2/3 text-sm font-medium text-slate-800">{`RGB: ${meta.has_rgb ? '있음' : '없음'} / Intensity: ${meta.has_intensity ? '있음' : '없음'}`}</div>
                          </div>
                        </div>
                      </div>

                      <div className="absolute top-4 right-4 text-[10px] font-bold text-white bg-blue-600 px-2 py-1 rounded shadow-sm">
                        2 메타데이터 자동 추출
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 2: PREPROCESS */}
          {activeTab === 'preprocess' && (
            <div className="flex flex-col h-full">
              <h2 className="text-lg font-bold text-slate-800 mb-1">점군 전처리 (Statistical Outlier Removal)</h2>
              <p className="text-xs text-slate-500 mb-4">입력된 점군 데이터에서 노이즈(이상치)를 제거하고 정합을 준비합니다.</p>

              <div className="grid grid-cols-2 gap-4 max-w-lg mb-4">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-700">이웃 점의 개수 (Mean K)</label>
                  <input type="number" value={sorMeanK} onChange={e=>setSorMeanK(Number(e.target.value))} className="border border-slate-300 rounded px-3 py-1.5 text-sm" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-700">표준편차 배수 (Std Dev)</label>
                  <input type="number" step="0.1" value={sorStdDev} onChange={e=>setSorStdDev(Number(e.target.value))} className="border border-slate-300 rounded px-3 py-1.5 text-sm" />
                </div>
              </div>

              <div className="flex gap-3 items-center mb-6">
                <button onClick={handlePreprocess} disabled={preprocessStatus === 'RUNNING' || !extractedMetadataList.length} className="bg-slate-800 hover:bg-slate-900 text-white font-bold py-2 px-6 rounded flex items-center gap-2 text-sm disabled:bg-slate-400">
                  {preprocessStatus === 'RUNNING' ? <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> : <Settings size={16} />}
                  노이즈 제거 실행
                </button>
                {preprocessStatus === 'SUCCESS' && <span className="text-green-600 text-xs font-bold flex items-center gap-1"><CheckCircle size={14}/> {preprocessResult?.engine} 실행 완료 ({preprocessResult?.processing_time}s)</span>}
                {preprocessStatus === 'ERROR' && <span className="text-red-500 text-xs font-bold">오류가 발생했습니다.</span>}
              </div>

              {/* Results Panel */}
              <div className="flex flex-col lg:flex-row gap-4 border-t border-slate-200 pt-6">
                {/* Left: Stats */}
                <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-4">
                  <h3 className="font-bold text-sm text-slate-800 mb-3 flex items-center gap-2">
                    <Database size={16} className="text-blue-600"/> 전처리 결과 요약
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white p-3 rounded border border-slate-200 shadow-sm">
                      <div className="text-[10px] text-slate-500 font-bold mb-1">처리 전 Point Cloud</div>
                      <div className="text-lg font-black text-slate-800">
                        {preprocessStatus === 'SUCCESS' ? preprocessResult.before_points.toLocaleString() : '-'}
                      </div>
                    </div>
                    <div className="bg-white p-3 rounded border border-blue-200 shadow-sm">
                      <div className="text-[10px] text-blue-600 font-bold mb-1">노이즈 제거 후 Point Cloud</div>
                      <div className="text-lg font-black text-blue-800">
                        {preprocessStatus === 'SUCCESS' ? preprocessResult.after_points.toLocaleString() : '-'}
                      </div>
                    </div>
                    <div className="bg-white p-3 rounded border border-slate-200 shadow-sm">
                      <div className="text-[10px] text-red-500 font-bold mb-1">제거된 노이즈 포인트</div>
                      <div className="text-sm font-bold text-red-600">
                        {preprocessStatus === 'SUCCESS' ? `-${preprocessResult.removed_points.toLocaleString()} pts` : '-'}
                      </div>
                    </div>
                    <div className="bg-white p-3 rounded border border-slate-200 shadow-sm">
                      <div className="text-[10px] text-slate-500 font-bold mb-1">정합 오차율 (RMSE)</div>
                      <div className="text-sm font-bold text-slate-800">
                        {preprocessResult?.rmse != null ? `${preprocessResult.rmse} ${preprocessResult.unit}` : '미측정'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Steps */}
                <div className="w-64 bg-slate-800 rounded-lg p-4 text-slate-300 flex flex-col h-full shadow-inner">
                  <h3 className="font-bold text-sm text-white mb-3">Processing Steps</h3>
                  <div className="flex-1 overflow-y-auto pr-2 space-y-3">
                    {preprocessStatus === 'SUCCESS' && preprocessResult ? (
                      preprocessResult.steps_completed.map((step: any, idx: number) => (
                        <div key={idx} className="flex flex-col gap-1">
                          <div className="flex items-center gap-2 text-xs font-bold text-white">
                            <CheckCircle size={14} className="text-emerald-400 shrink-0"/>
                            <span>{step.name}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 pl-6 break-words">
                            {step.detail}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-slate-500 text-center mt-4">실행을 대기 중입니다...</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: CLASSIFY */}
          {activeTab === 'classify' && (
            <div className="flex flex-col h-full">
              <h2 className="text-lg font-bold text-slate-800 mb-1">지상/비지상 분류 (CSF Algorithm) & DEM 생성</h2>
              <p className="text-xs text-slate-500 mb-4">분류 및 DEM 실행 엔진은 아직 연결되지 않았습니다. 현재 이 기능은 사용할 수 없습니다.</p>

              <div className="grid grid-cols-2 gap-4 max-w-lg mb-4">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-700">시뮬레이션 해상도 (Cloth Res)</label>
                  <input type="number" step="0.1" value={clothRes} onChange={e=>setClothRes(Number(e.target.value))} className="border border-slate-300 rounded px-3 py-1.5 text-sm" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-700">분류 임계값 (Threshold)</label>
                  <input type="number" step="0.1" value={classThresh} onChange={e=>setClassThresh(Number(e.target.value))} className="border border-slate-300 rounded px-3 py-1.5 text-sm" />
                </div>
              </div>

              <div className="flex gap-3 items-center">
                <button onClick={handleClassify} disabled={true} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded flex items-center gap-2 text-sm disabled:bg-slate-400">
                  {classifyStatus === 'RUNNING' ? <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> : <MountainSnow size={16} />}
                  자동 분류 및 DEM 생성
                </button>
                {classifyStatus === 'SUCCESS' && <span className="text-green-600 text-xs font-bold flex items-center gap-1"><CheckCircle size={14}/> 3D 지형(DEM) 생성이 완료되었습니다.</span>}
                {classifyStatus === 'ERROR' && <span className="text-red-500 text-xs font-bold">오류가 발생했습니다.</span>}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};
