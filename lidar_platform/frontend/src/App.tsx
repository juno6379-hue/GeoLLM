import { useState } from 'react';
import { MountainSnow, Map, BoxSelect, AreaChart, Layers, CheckCircle, Search, Target, CheckSquare, UploadCloud, Cpu, Database, Eye } from 'lucide-react';
import { DataUpload } from './pages/DataUpload';

const SidebarItem = ({ icon: Icon, label, active = false, onClick }: { icon: any, label: string, active?: boolean, onClick?: () => void }) => (
  <div onClick={onClick} className={`flex items-center gap-3 px-4 py-3 cursor-pointer rounded-lg mb-1 transition-colors ${active ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-blue-50'}`}>
    <Icon size={20} />
    <span className="font-medium text-sm">{label}</span>
  </div>
);

const KpiWidget = ({ icon: Icon, label, value, sub, color }: any) => (
  <div className="bg-white border border-slate-200 rounded-lg p-3 flex items-center gap-4 w-48 shadow-sm">
    <div className={`p-2 rounded-full ${color}`}>
      <Icon size={24} />
    </div>
    <div>
      <div className="text-xs text-slate-500 font-medium">{label}</div>
      <div className="text-lg font-bold text-slate-800">{value}</div>
      {sub && <div className="text-[10px] text-slate-400">{sub}</div>}
    </div>
  </div>
);

const Card = ({ number, title, children }: any) => (
  <div className="bg-white border border-slate-200 rounded-xl flex flex-col shadow-sm overflow-hidden">
    <div className="border-b border-slate-100 bg-slate-50/50 px-4 py-2.5 flex items-center gap-2">
      <div className="bg-blue-600 text-white text-xs font-bold w-5 h-5 flex items-center justify-center rounded-sm">
        {number}
      </div>
      <h3 className="font-bold text-slate-700 text-sm">{title}</h3>
    </div>
    <div className="p-4 flex-1 flex flex-col">
      {children}
    </div>
  </div>
);

const AgentNode = ({ icon: Icon, title, desc, active = false }: any) => (
  <div className={`flex flex-col items-center justify-center p-3 rounded-lg border-2 ${active ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-white'} shadow-sm min-w-[160px]`}>
    <Icon size={24} className={active ? 'text-blue-600' : 'text-slate-500'} />
    <div className={`font-bold text-sm mt-2 ${active ? 'text-blue-700' : 'text-slate-700'}`}>{title}</div>
    <div className="text-[10px] text-slate-500 text-center mt-1">{desc}</div>
  </div>
);

function App() {
  const queryParams = new URLSearchParams(window.location.search);
  const initialPage = queryParams.get('page') || 'upload';
  const isEmbedded = queryParams.get('embedded') === 'true';
  const [currentPage, setCurrentPage] = useState(initialPage);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 font-sans">
      {/* Sidebar - Only show if not embedded */}
      {!isEmbedded && (
        <div className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm z-10">
          <div className="p-5 border-b border-slate-200 flex items-center gap-3 cursor-pointer" onClick={() => setCurrentPage('dashboard')}>
            <div className="bg-blue-600 text-white p-2 rounded-lg">
              <Map size={24} />
            </div>
            <div className="font-bold text-slate-800 leading-tight">
              해양공간<br/>지능분석 플랫폼
            </div>
          </div>
          <div className="p-4 flex-1 overflow-y-auto">
            <div onClick={() => setCurrentPage('upload')} className={`rounded-lg px-4 py-3 mb-4 flex items-center gap-3 cursor-pointer shadow-sm transition-colors ${currentPage === 'upload' ? 'bg-blue-600 text-white shadow-blue-200' : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'}`}>
              <UploadCloud size={20} />
              <span className="font-bold">1. 데이터 업로드</span>
            </div>
            <SidebarItem icon={Cpu} label="2. 전처리·정합" active={currentPage === 'dashboard'} onClick={() => setCurrentPage('dashboard')} />
            <SidebarItem icon={MountainSnow} label="3. 지상/비지상 분류" />
            <SidebarItem icon={Layers} label="4. DEM·DSM·DTM 생성" />
            <SidebarItem icon={Map} label="5. 정사영상 중첩" />
            <SidebarItem icon={BoxSelect} label="6. 객체 추출·분류" />
            <SidebarItem icon={AreaChart} label="7. 변화탐지" />
            <SidebarItem icon={Eye} label="8. 2D/3D 가시화" />
            <SidebarItem icon={CheckCircle} label="9. 품질검증·보고" />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {currentPage === 'upload' ? (
          <DataUpload />
        ) : (
          <>
            {/* Header */}
            <header className="bg-white border-b border-slate-200 p-4 flex justify-between items-center z-10 shadow-sm">
              <div>
                <h1 className="text-2xl font-black text-slate-800 tracking-tight">드론 LiDAR 분석 주요 기능별 UI</h1>
                <p className="text-sm text-slate-500 mt-1 font-medium">전처리 · 정합 · 객체추출 · 수치표고모델 · 변화탐지 · 2D/3D 가시화</p>
              </div>
              <div className="flex gap-4">
                <KpiWidget icon={Database} label="입력 점군" value="125.6 M" sub="points" color="bg-blue-100 text-blue-600" />
                <KpiWidget icon={Target} label="정합 RMSE" value="0.028 m" sub="RMSE" color="bg-emerald-100 text-emerald-600" />
                <KpiWidget icon={AreaChart} label="변화 후보" value="1,842" sub="개소" color="bg-rose-100 text-rose-600" />
                <KpiWidget icon={BoxSelect} label="생성 산출물" value="26" sub="개" color="bg-amber-100 text-amber-600" />
              </div>
            </header>

            {/* Dashboard Grid */}
            <main className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-4 grid-rows-2 gap-4 h-full min-h-[600px]">
                <Card number="1" title="점군 전처리·정합">
                  <div className="flex-1 bg-slate-800 rounded-lg flex items-center justify-center text-white mb-3 text-xs">
                     (Point Cloud Viz)
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>노이즈 제거</li>
                    <li>중복·이상 포인트 필터링</li>
                    <li>Boresight 보정</li>
                    <li>ICP 정합</li>
                  </ul>
                </Card>

                <Card number="2" title="지상/비지상 분류">
                  <div className="flex-1 bg-slate-800 rounded-lg flex items-center justify-center text-white mb-3 text-xs">
                     (Classification Viz)
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>Ground / Non-ground 분리</li>
                    <li>건물·수목·구조물 구분</li>
                    <li>DEM/DTM 생성 준비</li>
                  </ul>
                </Card>

                <Card number="3" title="수치표고모델 생성">
                  <div className="flex-1 flex gap-2 mb-3">
                    <div className="flex-1 bg-gradient-to-br from-green-400 to-yellow-600 rounded-lg flex items-center justify-center text-white text-[10px] font-bold">DEM</div>
                    <div className="flex-1 bg-gradient-to-br from-slate-400 to-slate-700 rounded-lg flex items-center justify-center text-white text-[10px] font-bold">DSM</div>
                    <div className="flex-1 bg-gradient-to-br from-blue-300 to-emerald-400 rounded-lg flex items-center justify-center text-white text-[10px] font-bold">DTM</div>
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>격자 보간</li>
                    <li>경사·음영기복도 생성</li>
                    <li>표고 기반 분석</li>
                  </ul>
                </Card>

                <Card number="4" title="정사영상·공간정보 중첩">
                  <div className="flex-1 bg-slate-800 rounded-lg flex items-center justify-center text-white mb-3 text-xs">
                     (Orthophoto Overlay Viz)
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>정사영상 변환</li>
                    <li>전자해도/시설물 중첩</li>
                    <li>전·후 시점 비교</li>
                  </ul>
                </Card>

                <Card number="5" title="객체 추출·분류">
                  <div className="flex-1 bg-slate-800 rounded-lg flex items-center justify-center text-white mb-3 text-xs">
                     (Object Extraction Viz)
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>방파제·호안·선석 탐지</li>
                    <li>도로·교량·건물 분류</li>
                  </ul>
                </Card>

                <Card number="6" title="변화탐지">
                  <div className="flex-1 flex gap-2 mb-3">
                     <div className="flex-1 bg-slate-700 rounded-lg flex flex-col items-center justify-center text-white text-[10px]"><span className="mb-1">시점 1</span></div>
                     <div className="flex-1 bg-slate-700 rounded-lg flex flex-col items-center justify-center text-white text-[10px]"><span className="mb-1">시점 2</span></div>
                     <div className="flex-1 bg-gradient-to-b from-red-500 via-yellow-400 to-blue-500 rounded-lg flex flex-col items-center justify-center text-white text-[10px] font-bold">ΔZ</div>
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>침하·변형·침식·퇴적 분석</li>
                    <li>변화 후보 자동 추출</li>
                  </ul>
                </Card>

                <Card number="7" title="2D/3D 가시화">
                  <div className="flex-1 flex gap-2 mb-3">
                     <div className="flex-1 bg-slate-300 rounded-lg flex items-center justify-center text-slate-600 text-xs font-bold border border-slate-400">2D Map</div>
                     <div className="flex-1 bg-slate-800 rounded-lg flex items-center justify-center text-white text-xs font-bold border border-slate-900">3D Viewer</div>
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>COG / GeoJSON 결과</li>
                    <li>3D Tiles / Point Cloud</li>
                  </ul>
                </Card>

                <Card number="8" title="품질검증·산출물">
                  <div className="flex-1 flex flex-col gap-2 mb-3">
                     <div className="flex justify-between items-center bg-green-50 p-1.5 rounded border border-green-200">
                        <span className="text-[10px] font-bold text-slate-600">좌표계 일치</span>
                        <span className="text-[10px] font-bold text-green-600 bg-green-200 px-2 py-0.5 rounded">PASS</span>
                     </div>
                     <div className="flex justify-between items-center bg-green-50 p-1.5 rounded border border-green-200">
                        <span className="text-[10px] font-bold text-slate-600">고도기준 검증</span>
                        <span className="text-[10px] font-bold text-green-600 bg-green-200 px-2 py-0.5 rounded">PASS</span>
                     </div>
                  </div>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                    <li>좌표계·고도기준 검증</li>
                    <li>보고서/레이어 출력</li>
                  </ul>
                </Card>
              </div>
            </main>

            {/* Agent Workflow Footer */}
            <footer className="bg-white border-t border-slate-200 p-4 flex items-center gap-6 z-10 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
              <div className="flex items-center gap-2 mr-4 border-r pr-6 border-slate-200">
                <Cpu className="text-slate-400" size={20} />
                <span className="font-bold text-slate-600 text-sm">오케스트레이터<br/>연계 흐름</span>
              </div>
              <div className="flex items-center gap-4 flex-1">
                <AgentNode icon={Search} title="Data Discovery Agent" desc="데이터 탐색 · 메타 관리" />
                <div className="text-slate-300 font-bold">➔</div>
                <AgentNode icon={Cpu} title="Drone LiDAR Analysis Agent" desc="전처리 · 정합 · 분석 · 객체추출" active />
                <div className="text-slate-300 font-bold">➔</div>
                <AgentNode icon={AreaChart} title="Spatial Analysis Agent" desc="공간분석 · 변화탐지 · 통계" />
                <div className="text-slate-300 font-bold">➔</div>
                <AgentNode icon={Map} title="Map · Report Agent" desc="지도 · 대시보드 · 보고서" />
                <div className="text-slate-300 font-bold">➔</div>
                <AgentNode icon={CheckSquare} title="Validation Agent" desc="품질검증 · 검수 · 배포" />
              </div>
            </footer>
          </>
        )}
      </div>
    </div>
  );
}

export default App;

