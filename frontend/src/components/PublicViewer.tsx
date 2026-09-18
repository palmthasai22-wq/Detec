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
      <div className="absolute top-6 right-6 flex flex-col gap-4 z-10">
        {stats && (
          <div className="bg-black/60 backdrop-blur-md p-5 rounded-2xl border border-white/10 text-white shadow-2xl flex flex-col gap-4 min-w-[220px]">
            <h2 className="text-xs font-bold text-gray-400 uppercase tracking-widest border-b border-white/10 pb-2">Live Analysis</h2>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-gray-300">
                <BarChart2 size={16} className="text-blue-400" />
                <span className="text-sm font-medium">Density Index</span>
              </div>
              <span className="font-mono font-bold text-blue-400">{stats.density_index.toFixed(2)}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-gray-300">
                <Activity size={16} className="text-green-400" />
                <span className="text-sm font-medium">Traffic Level</span>
              </div>
              <span className="font-semibold text-green-400 capitalize text-sm">{stats.traffic_level}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-gray-300">
                <Users size={16} className="text-purple-400" />
                <span className="text-sm font-medium">Total Objects</span>
              </div>
              <span className="font-mono font-bold text-purple-400">{stats.total_objects}</span>
            </div>
          </div>
        )}
      </div>

      <div className="absolute bottom-6 left-6 z-10">
        <div className="bg-black/60 backdrop-blur-md px-5 py-3 rounded-xl border border-white/10 text-white shadow-xl">
          <h1 className="text-xl font-bold tracking-tight">{streamInfo.name}</h1>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
            <span className="text-xs text-gray-300 uppercase font-bold tracking-widest">Live Stream</span>
          </div>
        </div>
      </div>
    </div>
  );
};
