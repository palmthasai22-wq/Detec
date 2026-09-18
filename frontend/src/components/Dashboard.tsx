import React, { useState, useEffect } from 'react';
import axios from 'axios';
import VideoPlayer from './VideoPlayer';
import { LayoutGrid, Maximize, Activity } from 'lucide-react';

interface Camera {
  id: number;
  name: string;
  type: string;
  url?: string | null;
  embed_url?: string | null;
  embed_mode?: 'image' | 'iframe' | null;
}

const Dashboard = () => {
  const [layout, setLayout] = useState(1);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCameras, setSelectedCameras] = useState<(number | null)[]>(Array(9).fill(null));

  useEffect(() => {
    axios.get('/api/cameras')
      .then(res => setCameras(Array.isArray(res.data) ? res.data : []))
      .catch(err => console.error("Error fetching cameras:", err));
  }, []);

  const handleCameraSelect = (index: number, cameraId: string) => {
    const newSelected = [...selectedCameras];
    newSelected[index] = cameraId ? parseInt(cameraId) : null;
    setSelectedCameras(newSelected);
  };

  const gridClass = layout === 1 ? 'grid-cols-1' : layout === 4 ? 'grid-cols-2' : 'grid-cols-3';

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-500">
      {/* Top Bar */}
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            ระบบเฝ้าระวังภาพรวม (Global Overwatch)
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
          </h1>
          <p className="text-slate-400 mt-1 text-sm">วิเคราะห์การจราจรและประเมินความหนาแน่นด้วย AI เรียลไทม์</p>
        </div>
        
        <div className="flex bg-[#0F1523] border border-slate-700/50 p-1 rounded-lg shadow-lg">
          {[1, 4, 9].map(num => (
            <button
              key={num}
              onClick={() => setLayout(num)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all flex items-center gap-2 ${
                layout === num 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              {num === 1 ? 'กล้องเดี่ยว' : num === 4 ? '4 กล้อง' : '9 กล้อง'}
            </button>
          ))}
        </div>
      </div>

      {/* Video Grid */}
      <div className={`grid ${gridClass} gap-6 flex-1 min-h-0`}>
        {Array.from({ length: layout }).map((_, index) => (
          <div key={index} className="bg-[#0F1523] rounded-xl border border-slate-800/80 overflow-hidden flex flex-col relative shadow-2xl group hover:border-slate-700 transition-colors">
            {/* Header overlay for camera selection */}
            <div className="absolute top-0 left-0 right-0 z-20 p-3 bg-gradient-to-b from-black/80 to-transparent flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
              <select
                className="bg-black/50 border border-slate-600 text-white rounded px-3 py-1.5 text-sm backdrop-blur focus:outline-none focus:border-blue-500 min-w-[200px]"
                value={selectedCameras[index] || ''}
                onChange={(e) => handleCameraSelect(index, e.target.value)}
              >
                <option value="">-- เลือกกล้องวิดีโอ --</option>
                {cameras.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              <div className="flex items-center gap-1.5">
                <button 
                  onClick={() => {
                    if(selectedCameras[index]) {
                      const url = `${window.location.origin}/api/streams/${selectedCameras[index]}`;
                      navigator.clipboard.writeText(url);
                      alert('Copied Direct Stream URL to clipboard:\n' + url);
                    }
                  }}
                  className="text-slate-300 hover:text-white bg-black/50 p-1.5 rounded border border-slate-600 backdrop-blur"
                  title="Copy Direct Stream URL for Maps"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                </button>
                <button className="text-slate-300 hover:text-white bg-black/50 p-1.5 rounded border border-slate-600 backdrop-blur">
                  <Maximize className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            {/* Video Content */}
            <div className="flex-1 w-full h-full bg-[#050810] relative flex items-center justify-center">
              {selectedCameras[index] ? (
                <VideoPlayer
                  cameraId={selectedCameras[index]!}
                  embedUrl={cameras.find(camera => camera.id === selectedCameras[index])?.url ? undefined : cameras.find(camera => camera.id === selectedCameras[index])?.embed_url || undefined}
                  embedMode={cameras.find(camera => camera.id === selectedCameras[index])?.embed_mode || undefined}
                />
              ) : (
                <div className="flex flex-col items-center text-slate-600">
                  <Activity className="w-12 h-12 mb-3 opacity-20" />
                  <span className="text-sm font-medium tracking-widest uppercase">ไม่มีสัญญาณ / ยังไม่เลือกกล้อง</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
