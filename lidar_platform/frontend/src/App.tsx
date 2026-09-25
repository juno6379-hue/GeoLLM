import { DataUpload } from './pages/DataUpload';

export default function App() {
  return <div className="h-screen flex flex-col bg-slate-50">
    <header className="p-4 border-b bg-white">
      <h1 className="font-bold text-lg">LiDAR 데이터 등록 및 전처리</h1>
      <p className="text-sm text-slate-600">등록된 파일의 메타데이터와 실제 처리 결과를 표시합니다.</p>
    </header>
    <main className="flex-1 min-h-0"><DataUpload /></main>
  </div>;
}
