import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { List, RefreshCcw, Camera as CameraIcon } from 'lucide-react';

interface TrafficLog {
  id: number;
  camera_id: number;
  timestamp: string;
  person_count: number;
  car_count: number;
  motorcycle_count: number;
  truck_count: number;
  density_level: string;
}

interface Camera {
  id: number;
  name: string;
}

const LogsView = () => {
  const [logs, setLogs] = useState<TrafficLog[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [filterCamera, setFilterCamera] = useState<string>('');

  useEffect(() => {
    axios.get('/api/cameras').then(res => setCameras(res.data));
    fetchLogs();
  }, [filterCamera]);

  const fetchLogs = () => {
    const url = filterCamera 
      ? `/api/analytics/logs?camera_id=${filterCamera}`
      : `/api/analytics/logs`;
      
    axios.get(url).then(res => setLogs(res.data));
  };

  const getCameraName = (id: number) => cameras.find(c => c.id === id)?.name || `กล้อง ${id}`;

  const densityBadge = (level: string) => {
    const configs = {
      green: { color: 'text-green-400 bg-green-500/10 border border-green-500/20', text: 'คล่องตัว (LOW)' },
      yellow: { color: 'text-yellow-400 bg-yellow-500/10 border border-yellow-500/20', text: 'ปานกลาง (MODERATE)' },
      red: { color: 'text-red-400 bg-red-500/10 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.2)]', text: 'รถติดหนัก (HIGH)' }
    };
    const config = configs[level as keyof typeof configs] || { color: 'text-slate-400 bg-slate-800', text: level };
    
    return (
      <span className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-md ${config.color}`}>
        {config.text}
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto animate-in fade-in duration-500">
      <div className="flex justify-between items-end mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            สถิติและรายงานผล
          </h1>
          <p className="text-slate-400 mt-2">ประวัติข้อมูลการจราจรและการแจ้งเตือนจากระบบ AI</p>
        </div>
        
        <div className="flex gap-3 items-center">
          <button onClick={fetchLogs} className="px-4 py-2.5 bg-[#0F1523] border border-slate-700 rounded-lg hover:bg-slate-800 hover:text-white text-slate-400 text-sm flex items-center gap-2 transition-all">
            <RefreshCcw className="w-4 h-4" /> อัปเดตข้อมูล
          </button>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <CameraIcon className="w-4 h-4 text-slate-500" />
            </div>
            <select 
              className="bg-[#0F1523] border border-slate-700 text-white rounded-lg pl-9 pr-8 py-2.5 text-sm focus:outline-none focus:border-blue-500 appearance-none min-w-[200px]"
              value={filterCamera}
              onChange={(e) => setFilterCamera(e.target.value)}
            >
              <option value="">ดูกล้องทั้งหมด</option>
              {cameras.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="bg-[#0F1523] rounded-xl border border-slate-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800">
            <thead className="bg-black/40">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">วัน / เวลา</th>
                <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">ชื่อกล้อง</th>
                <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">รถยนต์</th>
                <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">มอเตอร์ไซค์</th>
                <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">รถบรรทุก</th>
                <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">บุคคล</th>
                <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">สถานะจราจร</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300 font-mono">
                    {new Date(log.timestamp).toLocaleString('th-TH')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                    {getCameraName(log.camera_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-mono text-blue-400">
                    {log.car_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-mono text-purple-400">
                    {log.motorcycle_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-mono text-orange-400">
                    {log.truck_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-mono text-green-400">
                    {log.person_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {densityBadge(log.density_level)}
                  </td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center">
                    <List className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-lg font-medium text-slate-300">ยังไม่มีข้อมูลบันทึก</p>
                    <p className="text-sm text-slate-500 mt-2">เปิดกล้องวิดีโอเพื่อเริ่มต้นการบันทึกสถิติแบบอัตโนมัติ</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LogsView;
