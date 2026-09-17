import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { Terminal, AlertCircle, CheckCircle2, Info, RefreshCw } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL;

export default function LogsView() {
  // We'll mock this for now since we didn't implement the exact /api/logs endpoint in Phase 5 backend
  // But the UI is ready to hook up to a real system_logs table
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = () => {
    setLoading(true);
    // Simulating API fetch
    setTimeout(() => {
      setLogs([
        { id: 1, timestamp: new Date().toISOString(), type: 'info', message: 'System started successfully' },
        { id: 2, timestamp: new Date(Date.now() - 60000).toISOString(), type: 'success', message: 'Camera 1 connected via RTSP' },
        { id: 3, timestamp: new Date(Date.now() - 120000).toISOString(), type: 'warning', message: 'High density detected in Zone A' },
        { id: 4, timestamp: new Date(Date.now() - 500000).toISOString(), type: 'error', message: 'Stream timeout for Channel 2' }
      ]);
      setLoading(false);
    }, 500);
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const getIcon = (type: string) => {
    switch(type) {
      case 'error': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case 'success': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      default: return <Info className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0F1523] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
      <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-[#151b2b]">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-slate-400" />
          <h2 className="font-semibold text-slate-200">System Event Logs</h2>
        </div>
        <button 
          onClick={fetchLogs}
          className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      <div className="flex-1 overflow-auto p-4 space-y-2 font-mono text-sm">
        {logs.map((log) => (
          <div key={log.id} className="flex gap-4 p-2 hover:bg-slate-800/50 rounded-lg transition-colors border-b border-slate-800/50 pb-3">
            <div className="text-slate-500 whitespace-nowrap">
              {format(new Date(log.timestamp), 'HH:mm:ss')}
            </div>
            <div className="mt-0.5">
              {getIcon(log.type)}
            </div>
            <div className="text-slate-300">
              {log.message}
            </div>
          </div>
        ))}
        {logs.length === 0 && !loading && (
          <div className="text-center text-slate-500 py-10">No logs found</div>
        )}
      </div>
    </div>
  );
}
