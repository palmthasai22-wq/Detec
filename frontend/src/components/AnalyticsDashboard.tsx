import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, Users, TrendingUp } from 'lucide-react';

interface AnalyticsData {
  timestamp: string;
  density_index: number;
  traffic_index: number;
  total_detections: number;
}

const RANGES = [
  { label: '1h', value: '1h' },
  { label: '6h', value: '6h' },
  { label: '12h', value: '12h' },
  { label: '24h', value: '24h' },
  { label: '7d', value: '7d' },
];

export const AnalyticsDashboard: React.FC = () => {
  const [range, setRange] = useState('24h');
  const [data, setData] = useState<AnalyticsData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/analytics_v2/history?range=${range}`);
        setData(response.data);
      } catch (err) {
        setError('Failed to fetch analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [range]);

  const kpis = useMemo(() => {
    if (!data.length) return { avgDensity: 0, maxTraffic: 0, totalDetections: 0 };
    
    let sumDensity = 0;
    let maxTraffic = 0;
    let totalDetections = 0;

    data.forEach(d => {
      sumDensity += d.density_index;
      if (d.traffic_index > maxTraffic) maxTraffic = d.traffic_index;
      totalDetections += d.total_detections;
    });

    return {
      avgDensity: (sumDensity / data.length).toFixed(2),
      maxTraffic: maxTraffic.toFixed(2),
      totalDetections
    };
  }, [data]);

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800">Historical Analytics</h2>
        <div className="flex gap-2">
          {RANGES.map(r => (
            <button
              key={r.value}
              onClick={() => setRange(r.value)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                range === r.value 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="p-5 bg-blue-50/50 border border-blue-100 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
            <Users size={24} />
          </div>
          <div>
            <p className="text-sm text-blue-600/80 font-medium mb-1">Avg Density</p>
            <p className="text-2xl font-bold text-gray-900">{kpis.avgDensity}</p>
          </div>
        </div>
        
        <div className="p-5 bg-emerald-50/50 border border-emerald-100 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-emerald-100 text-emerald-600 rounded-lg">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm text-emerald-600/80 font-medium mb-1">Max Traffic</p>
            <p className="text-2xl font-bold text-gray-900">{kpis.maxTraffic}</p>
          </div>
        </div>

        <div className="p-5 bg-purple-50/50 border border-purple-100 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-purple-100 text-purple-600 rounded-lg">
            <TrendingUp size={24} />
          </div>
          <div>
            <p className="text-sm text-purple-600/80 font-medium mb-1">Total Detections</p>
            <p className="text-2xl font-bold text-gray-900">{kpis.totalDetections}</p>
          </div>
        </div>
      </div>

      <div className="h-[350px] w-full">
        {loading ? (
          <div className="h-full flex items-center justify-center text-gray-500">Loading data...</div>
        ) : error ? (
          <div className="h-full flex items-center justify-center text-red-500">{error}</div>
        ) : data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">No data available in this range</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis 
                dataKey="timestamp" 
                tick={{ fontSize: 12, fill: '#6B7280' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val: any) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#6B7280' }} 
                tickLine={false}
                axisLine={false}
              />
              <Tooltip 
                labelFormatter={(val: any) => new Date(val).toLocaleString()}
                contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)' }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Line 
                type="monotone" 
                dataKey="density_index" 
                name="Density Index" 
                stroke="#3B82F6" 
                strokeWidth={3} 
                dot={false} 
                activeDot={{ r: 6, fill: '#3B82F6', strokeWidth: 0 }} 
              />
              <Line 
                type="monotone" 
                dataKey="traffic_index" 
                name="Traffic Index" 
                stroke="#10B981" 
                strokeWidth={3} 
                dot={false} 
                activeDot={{ r: 6, fill: '#10B981', strokeWidth: 0 }} 
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
