import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { Settings, Users, Car, AlertTriangle, Truck } from 'lucide-react';
import { getApiUrl, getWebSocketUrl } from '../config/api';

interface VideoPlayerProps {
  cameraId: number;
  embedUrl?: string;
  embedMode?: 'image' | 'iframe';
}

interface StreamStats {
  camera_id: number;
  density: 'green' | 'yellow' | 'red' | 'blue';
  congestion_index: number;
  current_vehicles: number;
  person_count: number;
  car_count: number;
  motorcycle_count: number;
  truck_count: number;
  in_count: number;
  out_count: number;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ cameraId, embedUrl, embedMode }) => {
  const [stats, setStats] = useState<StreamStats | null>(null);
  const [confidence, setConfidence] = useState<number>(15);
  const [showSettings, setShowSettings] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Fetch initial confidence
    axios.get(`/api/cameras/`).then(res => {
      const cameras = Array.isArray(res.data) ? res.data : [];
      const cam = cameras.find((c: any) => c.id === cameraId);
      if (cam && cam.confidence_threshold) {
        setConfidence(Math.round(cam.confidence_threshold * 100));
      }
    }).catch(console.error);

    // WebSocket for stats
    const ws = new WebSocket(getWebSocketUrl('/api/analytics/ws'));
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data: StreamStats = JSON.parse(event.data);
        if (data.camera_id === cameraId) {
          setStats(data);
        }
      } catch (e) {
        console.error("Error parsing websocket message", e);
      }
    };

    return () => {
      ws.close();
    };
  }, [cameraId]);

  const handleConfidenceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value);
    setConfidence(val);
    axios.put(`/api/cameras/${cameraId}`, {
      confidence_threshold: val / 100.0
    }).catch(console.error);
  };

  const densityConfig = {
    green: { color: 'text-green-400', bg: 'bg-green-500', glow: 'shadow-[0_0_15px_#22c55e]', label: 'FLOWING' },
    yellow: { color: 'text-yellow-400', bg: 'bg-yellow-500', glow: 'shadow-[0_0_15px_#eab308]', label: 'SLOWING' },
    red: { color: 'text-red-400', bg: 'bg-red-500', glow: 'shadow-[0_0_15px_#ef4444]', label: 'JAMMED' },
    blue: { color: 'text-blue-400', bg: 'bg-blue-500', glow: 'shadow-[0_0_15px_#3b82f6]', label: 'WAITING SIGNAL' },
  };

  const currentDensity = stats ? densityConfig[stats.density] : densityConfig.green;

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center bg-black group overflow-hidden">
      {/* Video Feed */}
      {embedUrl && embedMode === 'iframe' ? (
        <iframe
          src={embedUrl}
          title={`Embedded camera ${cameraId}`}
          className="h-full w-full border-0 bg-black"
          allow="autoplay; fullscreen; picture-in-picture"
          sandbox="allow-scripts allow-same-origin allow-presentation"
          referrerPolicy="no-referrer"
        />
      ) : (
        <img
          src={embedUrl || getApiUrl(`/api/streams/${cameraId}`)}
          alt={`Stream ${cameraId}`}
          className="w-full h-full object-contain"
          referrerPolicy="no-referrer"
          onError={(e) => {
            (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%"><rect width="100%" height="100%" fill="%23050810"/><text x="50%" y="50%" fill="%23334155" font-family="monospace" font-size="20" text-anchor="middle" alignment-baseline="middle">ไม่มีสัญญาณ</text></svg>';
          }}
        />
      )}
      
      {/* Settings Gear - Top Right */}
      <div className="absolute top-4 right-4 z-30 opacity-0 group-hover:opacity-100 transition-opacity">
        <button 
          onClick={() => setShowSettings(!showSettings)}
          className="bg-black/60 p-2 rounded-full text-slate-300 hover:text-white border border-slate-600 backdrop-blur"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-14 right-4 z-30 bg-black/80 border border-slate-700 p-4 rounded-lg backdrop-blur-md w-64 shadow-2xl animate-in slide-in-from-top-2">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">ความแม่นยำ AI (Sensitivity)</span>
            <span className="text-blue-400 font-mono text-sm">{confidence}%</span>
          </div>
          <input 
            type="range" 
            min="1" 
            max="80" 
            value={confidence}
            onChange={handleConfidenceChange}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <p className="text-[10px] text-slate-500 mt-2 leading-tight">
            ค่าน้อย = ตรวจจับรถระยะไกลได้ดี | ค่ามาก = กรองเฉพาะรถที่ชัดเจน
          </p>
        </div>
      )}
      
      {/* HUD Overlay - Bottom Panel */}
      {stats && (
        <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end gap-4">
          
          {/* Main Stats Block */}
          <div className="bg-black/60 border border-slate-700/50 rounded-lg p-3 backdrop-blur-sm flex gap-6">
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-1">ปริมาณรถทั้งหมดในกล้อง</span>
              <span className="text-2xl font-mono font-bold text-white leading-none">{stats.current_vehicles} <span className="text-sm text-slate-500 font-sans">คัน</span></span>
            </div>
          </div>

          {/* Counts */}
          <div className="bg-black/60 border border-slate-700/50 px-4 py-3 rounded-lg backdrop-blur-sm flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">จำนวนรถบนจอ</span>
              <span className="text-xl font-bold text-white leading-none">{stats.current_vehicles} <span className="text-xs text-slate-500">คัน</span></span>
            </div>
            
            {(stats.in_count > 0 || stats.out_count > 0) && (
              <>
                <div className="w-px h-8 bg-slate-700/50"></div>
                <div className="flex flex-col justify-center">
                  <div className="text-xs font-mono text-slate-300">เข้า: <span className="text-green-400">{stats.in_count}</span></div>
                  <div className="text-xs font-mono text-slate-300">ออก: <span className="text-red-400">{stats.out_count}</span></div>
                </div>
              </>
            )}
          </div>
          
          {/* Congestion Index (Jam Level) */}
          <div className="bg-black/60 border border-slate-700/50 px-4 py-3 rounded-lg backdrop-blur-sm flex-1 max-w-md">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">ดัชนีรถติด (Jam Index)</span>
              <span className={`text-xs font-mono font-bold ${stats.congestion_index > 75 ? 'text-red-400' : stats.congestion_index > 40 ? 'text-yellow-400' : 'text-green-400'}`}>
                {stats.congestion_index}% 
                <span className="ml-1 text-[10px] font-sans">
                  {stats.congestion_index > 75 ? '(ติดขัด)' : stats.congestion_index > 40 ? '(ชะลอตัว)' : '(คล่องตัว)'}
                </span>
              </span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ease-out ${stats.congestion_index > 75 ? 'bg-red-500 shadow-[0_0_10px_#ef4444]' : stats.congestion_index > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${stats.congestion_index}%` }}
              ></div>
            </div>
          </div>
          
          {/* Density Indicator */}
          <div className="bg-black/60 border border-slate-700/50 px-4 py-3 rounded-lg backdrop-blur-sm flex items-center gap-3">
            <div className="flex flex-col text-right">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">สถานะจราจร</span>
              <span className={`text-sm font-bold tracking-widest ${currentDensity.color}`}>
                {currentDensity.label}
              </span>
            </div>
            <div className="relative flex items-center justify-center">
              <div className={`absolute w-full h-full rounded-full ${currentDensity.bg} opacity-20 animate-ping`}></div>
              <div className={`w-4 h-4 rounded-full ${currentDensity.bg} ${currentDensity.glow}`}></div>
            </div>
          </div>

        </div>
      )}
      
      {/* Scanline Effect Overlay (subtle) */}
      <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%)] bg-[length:100%_4px] opacity-20 mix-blend-overlay"></div>
    </div>
  );
};

export default VideoPlayer;
