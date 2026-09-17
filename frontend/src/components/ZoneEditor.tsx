import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Save, Trash2, Crosshair, X } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL;

interface Point {
  x: number;
  y: number;
}

export default function ZoneEditor({ channelId, onClose }: { channelId: number, onClose: () => void }) {
  const [zones, setZones] = useState<any[]>([]);
  const [activeZone, setActiveZone] = useState<any>(null);
  const [points, setPoints] = useState<Point[]>([]);
  const [loading, setLoading] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    fetchZones();
  }, [channelId]);

  const fetchZones = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/channels/${channelId}/zones`);
      setZones(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    const img = imgRef.current;
    
    if (!canvas || !ctx || !img) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw existing zones
    zones.forEach(z => {
      if (z.id === activeZone?.id) return; // Skip active zone as we draw it separately
      if (z.polygon && z.polygon.length > 2) {
        ctx.beginPath();
        ctx.moveTo(z.polygon[0][0] * canvas.width, z.polygon[0][1] * canvas.height);
        for (let i = 1; i < z.polygon.length; i++) {
          ctx.lineTo(z.polygon[i][0] * canvas.width, z.polygon[i][1] * canvas.height);
        }
        ctx.closePath();
        ctx.fillStyle = z.color ? z.color + '40' : 'rgba(59, 130, 246, 0.25)';
        ctx.fill();
        ctx.strokeStyle = z.color || '#3b82f6';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });

    // Draw active polygon points
    if (points.length > 0) {
      ctx.beginPath();
      ctx.moveTo(points[0].x * canvas.width, points[0].y * canvas.height);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x * canvas.width, points[i].y * canvas.height);
      }
      if (points.length > 2) ctx.closePath();
      
      ctx.fillStyle = 'rgba(255, 100, 0, 0.3)';
      ctx.fill();
      ctx.strokeStyle = '#ff6400';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      points.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x * canvas.width, p.y * canvas.height, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.stroke();
      });
    }
  };

  useEffect(() => {
    drawCanvas();
  }, [points, zones, activeZone]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    setPoints([...points, { x, y }]);
  };

  const handleSaveZone = async () => {
    if (points.length < 3) return alert('Please draw at least 3 points for a polygon zone.');
    
    const polygonData = points.map(p => [p.x, p.y]);
    
    try {
      if (activeZone?.id) {
        await axios.put(`${API_URL}/api/channels/${channelId}/zones/${activeZone.id}`, {
          polygon: polygonData
        });
      } else {
        await axios.post(`${API_URL}/api/channels/${channelId}/zones`, {
          name: `Zone ${zones.length + 1}`,
          polygon: polygonData,
          color: '#ff6400'
        });
      }
      setPoints([]);
      setActiveZone(null);
      fetchZones();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteZone = async (zoneId: number) => {
    if (!confirm('Delete this zone?')) return;
    try {
      await axios.delete(`${API_URL}/api/channels/${channelId}/zones/${zoneId}`);
      fetchZones();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0F1523] border border-slate-700 rounded-xl w-full max-w-5xl flex overflow-hidden shadow-2xl">
        
        {/* Editor area */}
        <div className="flex-1 p-6 flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Zone Editor</h2>
            <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-lg text-slate-400">
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="relative flex-1 bg-black rounded-lg border border-slate-700 overflow-hidden min-h-[400px]">
            {/* Show current stream frame as background */}
            <img 
              ref={imgRef}
              src={`${API_URL}/api/streams/${channelId}/stream.mjpg`}
              alt="Stream"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none opacity-50"
              crossOrigin="anonymous"
              onLoad={() => drawCanvas()}
            />
            <canvas
              ref={canvasRef}
              width={800}
              height={450}
              className="absolute inset-0 w-full h-full cursor-crosshair z-10"
              onClick={handleCanvasClick}
            />
          </div>
          
          <div className="flex items-center gap-4 mt-4 text-sm text-slate-400">
            <Crosshair className="w-4 h-4" /> Click on the video to draw a polygon.
            {points.length > 0 && (
              <button 
                onClick={() => setPoints([])} 
                className="ml-auto text-red-400 hover:text-red-300"
              >
                Clear Points
              </button>
            )}
          </div>
        </div>
        
        {/* Sidebar */}
        <div className="w-72 bg-[#0B0F19] border-l border-slate-800 p-6 flex flex-col">
          <h3 className="font-semibold text-slate-300 mb-4">Existing Zones</h3>
          
          <div className="space-y-3 flex-1 overflow-y-auto">
            {zones.map(z => (
              <div key={z.id} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 flex justify-between items-center">
                <span className="text-sm font-medium">{z.name}</span>
                <div className="flex gap-2">
                  <button onClick={() => handleDeleteZone(z.id)} className="text-red-400 hover:text-red-300">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
            {zones.length === 0 && !loading && (
              <p className="text-sm text-slate-500 text-center py-4">No zones created yet.</p>
            )}
          </div>
          
          <div className="pt-4 mt-4 border-t border-slate-800">
            <button
              onClick={handleSaveZone}
              disabled={points.length < 3}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2 rounded-lg font-medium transition-colors"
            >
              <Save className="w-4 h-4" /> Save Zone
            </button>
          </div>
        </div>
        
      </div>
    </div>
  );
}
