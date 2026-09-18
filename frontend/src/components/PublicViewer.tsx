import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { HlsPlayer } from './HlsPlayer';
import { Users, Activity, BarChart2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface StreamInfo {
  hls_url: string;
  mjpeg_url?: string;
  name: string;
}

interface StreamStats {
  density_index: number;
  traffic_level: string;
  total_objects: number;
}

export const PublicViewer: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);
  const [stats, setStats] = useState<StreamStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStream = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/public/${slug}/stream`);
        setStreamInfo(res.data);
      } catch (err) {
        console.error('Failed to fetch stream info:', err);
        setError('Stream not found or unavailable');
      }
    };
    if (slug) fetchStream();
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/public/${slug}/stats`);
        setStats(res.data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, [slug]);

  if (error) {
    return (
      <div className="w-screen h-screen flex items-center justify-center bg-gray-900 text-white font-sans">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Stream Unavailable</h1>
          <p className="text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!streamInfo) {
    return (
      <div className="w-screen h-screen flex items-center justify-center bg-gray-900 text-white font-sans">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-lg text-gray-300">Loading live feed...</p>
        </div>
      </div>
    );
  }

  const getTrafficStatus = (density: number) => {
    if (density < 40) return { label: 'FLOWING', color: 'text-green-400' };
    if (density < 75) return { label: 'SLOWING', color: 'text-yellow-400' };
    return { label: 'JAMMED', color: 'text-red-500' };
  };

  const trafficStatus = stats ? getTrafficStatus(stats.density_index) : null;

  return (
    <div className="w-screen h-screen bg-black overflow-hidden relative font-sans">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-full h-full">
          {streamInfo.mjpeg_url ? (
            <img src={`${API_URL}${streamInfo.mjpeg_url}`} className="w-full h-full object-contain" alt="Live Feed" />
          ) : (
            <HlsPlayer url={streamInfo.hls_url} />
          )}
        </div>
      </div>
      
      {/* Overlay Stats */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10 pointer-events-none">
        {stats && trafficStatus && (
          <div className="bg-black/50 backdrop-blur-sm p-3 rounded-lg border border-white/10 text-white shadow-lg flex flex-col gap-2 min-w-[150px]">
            <h2 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest border-b border-white/10 pb-1">Live Analysis</h2>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-gray-300">
                <BarChart2 size={12} className={trafficStatus.color} />
                <span className="text-xs font-medium">Density Index</span>
              </div>
              <span className={`font-mono text-xs font-bold ${trafficStatus.color}`}>{stats.density_index.toFixed(2)}%</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-gray-300">
                <Activity size={12} className={trafficStatus.color} />
                <span className="text-xs font-medium">Traffic Status</span>
              </div>
              <span className={`font-semibold capitalize text-xs ${trafficStatus.color}`}>{trafficStatus.label}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-gray-300">
                <Users size={12} className="text-gray-400" />
                <span className="text-xs font-medium">Vehicles</span>
              </div>
              <span className="font-mono text-xs font-bold text-gray-200">{stats.total_objects}</span>
            </div>
          </div>
        )}
      </div>

      <div className="absolute bottom-4 left-4 z-10 pointer-events-none">
        <div className="bg-black/50 backdrop-blur-sm px-3 py-2 rounded-lg border border-white/10 text-white shadow-lg">
          <h1 className="text-sm font-bold tracking-tight line-clamp-1 max-w-[200px]">{streamInfo.name}</h1>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_5px_rgba(239,68,68,0.8)]"></span>
            <span className="text-[9px] text-gray-300 uppercase font-bold tracking-widest">Live Stream</span>
          </div>
        </div>
      </div>
    </div>
  );
};
