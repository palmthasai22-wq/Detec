import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Cpu, MemoryStick, MonitorPlay, Server } from 'lucide-react';

interface GpuStat {
  id: number;
  name: string;
  utilization: number;
  memory_used: number;
  memory_total: number;
}

interface SystemStats {
  cpu_usage: number;
  ram_used: number;
  ram_total: number;
  gpu_stats?: GpuStat[];
}

export const ResourceMonitor: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/analytics_v2/system`);
        if (mounted) {
          setStats(response.data);
          setError('');
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to fetch system stats');
        }
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 2000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (!stats && !error) {
    return (
      <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 flex items-center justify-center min-h-[300px] text-gray-500">
        Connecting to system monitor...
      </div>
    );
  }

  const ProgressBar = ({ 
    label, 
    percentage, 
    colorClass, 
    textClass, 
    icon: Icon, 
    detail 
  }: { 
    label: string, 
    percentage: number, 
    colorClass: string, 
    textClass: string, 
    icon: any, 
    detail: string 
  }) => (
    <div className="mb-5 last:mb-0">
      <div className="flex justify-between items-end mb-2">
        <div className="flex items-center gap-2 text-gray-700 font-medium">
          <Icon size={18} className={textClass} />
          <span className="text-sm">{label}</span>
        </div>
        <span className="text-sm font-semibold text-gray-900">{detail}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
        <div 
          className={`${colorClass} h-2 rounded-full transition-all duration-1000 ease-in-out`} 
          style={{ width: `${Math.min(Math.max(percentage || 0, 0), 100)}%` }}
        ></div>
      </div>
    </div>
  );

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-50">
        <div className="p-2 bg-gray-50 rounded-lg text-gray-700">
          <Server size={20} />
        </div>
        <h2 className="text-lg font-bold text-gray-800">System Resources</h2>
      </div>

      {error ? (
        <div className="text-red-500 text-sm py-4 bg-red-50 px-4 rounded-lg">{error}</div>
      ) : stats ? (
        <div className="space-y-6">
          <ProgressBar 
            label="CPU Usage" 
            percentage={stats.cpu_usage} 
            colorClass="bg-blue-500"
            textClass="text-blue-600"
            icon={Cpu} 
            detail={`${(stats.cpu_usage || 0).toFixed(1)}%`} 
          />
          
          <ProgressBar 
            label="Memory (RAM)" 
            percentage={stats.ram_total ? (stats.ram_used / stats.ram_total) * 100 : 0} 
            colorClass="bg-emerald-500"
            textClass="text-emerald-600"
            icon={MemoryStick} 
            detail={`${(stats.ram_used || 0).toFixed(1)} GB / ${(stats.ram_total || 0).toFixed(1)} GB`} 
          />

          {stats.gpu_stats && stats.gpu_stats.length > 0 && (
            <div className="mt-8 pt-6 border-t border-gray-100">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4">GPU Infrastructure</h3>
              {stats.gpu_stats.map((gpu, index) => (
                <div key={index} className="space-y-5 bg-gray-50/50 border border-gray-100 p-5 rounded-xl mb-4 last:mb-0">
                  <div className="font-semibold text-gray-800 text-sm flex items-center gap-2">
                    <MonitorPlay size={16} className="text-purple-600" />
                    {gpu.name || `GPU ${gpu.id}`}
                  </div>
                  
                  <ProgressBar 
                    label="Compute Utilization" 
                    percentage={gpu.utilization} 
                    colorClass="bg-purple-500"
                    textClass="text-purple-600"
                    icon={Cpu} 
                    detail={`${(gpu.utilization || 0).toFixed(1)}%`} 
                  />
                  
                  <ProgressBar 
                    label="VRAM Usage" 
                    percentage={gpu.memory_total ? (gpu.memory_used / gpu.memory_total) * 100 : 0} 
                    colorClass="bg-pink-500"
                    textClass="text-pink-600"
                    icon={MemoryStick} 
                    detail={`${(gpu.memory_used || 0).toFixed(1)} GB / ${(gpu.memory_total || 0).toFixed(1)} GB`} 
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
