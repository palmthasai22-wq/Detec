import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Upload as UploadIcon, Check, Map, RotateCcw } from 'lucide-react';
import { getApiUrl } from '../config/api';

const UploadAnalyzer: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [cameraId, setCameraId] = useState<number | null>(null);
  const [step, setStep] = useState<1 | 2>(1);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [lat, setLat] = useState<string>('');
  const [lng, setLng] = useState<string>('');
  const [monitorUrl, setMonitorUrl] = useState<string>('');

  useEffect(() => {
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [file]);
  
  // Canvas for drawing Wait Zone Polygon
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [polygon, setPolygon] = useState<[number, number][]>([]);
  const [previewPoint, setPreviewPoint] = useState<[number, number] | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post('/api/streams/upload', formData);
      setCameraId(res.data.camera_id);
      setMonitorUrl(getApiUrl(res.data.monitor_path || `/live/${res.data.public_id}`));
      setStep(2);
    } catch (err: any) {
      console.error(err);
      alert("อัปโหลดล้มเหลว: " + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };
  
  const handleCanvasClick = (e: React.MouseEvent) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setPolygon(prev => [...prev, [x, y]]);
  };

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    setPreviewPoint([x, y]);
  };

  const clearPolygon = () => {
    setPolygon([]);
    setPreviewPoint(null);
  };

  // Draw polygon on canvas
  useEffect(() => {
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        const w = canvasRef.current.width;
        const h = canvasRef.current.height;
        ctx.clearRect(0, 0, w, h);
        
        if (polygon.length > 0) {
          ctx.beginPath();
          ctx.moveTo(polygon[0][0] * w, polygon[0][1] * h);
          for (let i = 1; i < polygon.length; i++) {
            ctx.lineTo(polygon[i][0] * w, polygon[i][1] * h);
          }
          
          if (previewPoint && polygon.length > 0) {
            ctx.lineTo(previewPoint[0] * w, previewPoint[1] * h);
          }
          
          if (polygon.length >= 2 || (polygon.length === 2 && previewPoint)) {
            ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
            ctx.fill();
          }
          
          ctx.strokeStyle = '#3b82f6';
          ctx.lineWidth = 2;
          ctx.stroke();
          
          polygon.forEach(pt => {
            ctx.beginPath();
            ctx.arc(pt[0] * w, pt[1] * h, 5, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
            ctx.strokeStyle = '#3b82f6';
            ctx.stroke();
          });
        }
      }
    }
  }, [polygon, previewPoint, step]);

  const saveConfig = async () => {
    if (cameraId) {
      try {
        const payload: any = {};
        if (polygon.length >= 3) {
          payload.wait_zone = polygon;
        }
        if (lat && lng) {
          payload.lat = parseFloat(lat);
          payload.lng = parseFloat(lng);
        }
        await axios.put(`/api/cameras/${cameraId}`, payload);
      } catch(e) { console.error(e); }
    }
    alert("ตั้งค่าเสร็จสิ้น! คุณสามารถดูผลวิเคราะห์ได้ที่หน้าจอมอนิเตอร์");
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-white">อัปโหลดวิดีโอ (โดรน)</h1>
      
      {step === 1 ? (
        <div className="bg-[#0F1523] border border-slate-700 p-8 rounded-lg shadow-xl text-center">
          <UploadIcon className="w-16 h-16 mx-auto text-blue-500 mb-4" />
          <p className="text-slate-400 mb-6">ขั้นตอนที่ 1: อัปโหลดไฟล์วิดีโอจากโดรนเพื่อนำไปวิเคราะห์ด้วย AI</p>
          <input 
            type="file" 
            accept="video/mp4" 
            className="mb-6 block w-full max-w-xs mx-auto text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500"
            onChange={handleFileChange}
          />
          <button 
            disabled={!file || uploading}
            onClick={handleUpload}
            className="block w-full max-w-xs mx-auto bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-500 disabled:opacity-50 font-medium shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all"
          >
            {uploading ? 'กำลังอัปโหลด...' : 'อัปโหลดวิดีโอ'}
          </button>
        </div>
      ) : (
        <div className="bg-[#0F1523] border border-slate-700 p-6 rounded-lg shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-lg font-bold mb-2 text-white flex items-center gap-2">
                <Map className="w-5 h-5 text-blue-400" />
                ขั้นตอนที่ 2: วาดพื้นที่โซนรอสัญญาณไฟ (Wait Zone)
              </h2>
              <p className="text-sm text-slate-400 max-w-lg">
                คลิกบนกรอบด้านล่างเพื่อวาดสี่เหลี่ยมคลุมบริเวณ <b>"ทางแยก"</b> หรือ <b>"จุดกลับรถ"</b>
                <br/>หากรถจอดในบริเวณนี้ AI จะถือว่ากำลัง "รอสัญญาณไฟ (WAITING)" แทนที่จะมองว่าเป็น "รถติดสะสม (JAMMED)"
              </p>
            </div>
            {polygon.length > 0 && (
              <button onClick={clearPolygon} className="text-red-400 hover:text-red-300 text-sm flex items-center gap-1 bg-red-500/10 px-3 py-1.5 rounded border border-red-500/20">
                <RotateCcw className="w-4 h-4" /> ล้างเส้น
              </button>
            )}
          </div>
          
          <div className="flex justify-center mb-6">
            <div className="relative w-full max-w-2xl bg-black border border-slate-600 rounded overflow-hidden" style={{ aspectRatio: '640/480' }}>
              {videoUrl && (
                <video 
                  src={videoUrl} 
                  className="absolute inset-0 w-full h-full object-fill"
                  autoPlay
                  loop
                  muted
                />
              )}
              <canvas 
                ref={canvasRef}
                width={640} 
                height={480}
                className="absolute inset-0 w-full h-full cursor-crosshair z-10"
                onClick={handleCanvasClick}
                onMouseMove={handleCanvasMouseMove}
                onMouseLeave={() => setPreviewPoint(null)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-slate-800">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ละติจูด (Latitude) <span className="text-[10px] text-slate-500 normal-case">*สำหรับแผนที่ Impexspot</span></label>
              <input type="text" value={lat} onChange={e => setLat(e.target.value)} placeholder="เช่น 13.7563" className="w-full bg-black/50 border border-slate-700 rounded-lg p-2.5 text-white focus:border-blue-500 outline-none transition-colors" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ลองจิจูด (Longitude)</label>
              <input type="text" value={lng} onChange={e => setLng(e.target.value)} placeholder="เช่น 100.5018" className="w-full bg-black/50 border border-slate-700 rounded-lg p-2.5 text-white focus:border-blue-500 outline-none transition-colors" />
            </div>
          </div>

          {monitorUrl && (
            <div className="mt-5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 p-4">
              <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-cyan-300">URL จอมอนิเตอร์สำหรับ Impex Spot</label>
              <div className="flex gap-2">
                <input readOnly value={monitorUrl} className="min-w-0 flex-1 rounded-md border border-slate-700 bg-black/50 p-2.5 font-mono text-xs text-white" />
                <button type="button" onClick={() => navigator.clipboard.writeText(monitorUrl)} className="rounded-md bg-cyan-600 px-4 text-sm font-medium text-white hover:bg-cyan-500">คัดลอก URL</button>
                <a href={monitorUrl} target="_blank" rel="noreferrer" className="rounded-md border border-cyan-500/40 px-4 py-2 text-sm font-medium text-cyan-300 hover:bg-cyan-500/10">เปิดดู</a>
              </div>
              <p className="mt-2 text-[10px] text-slate-400">นำ URL นี้ไปใส่ช่อง “URL สตรีมภายนอก” ในหน้าจัดการกล้อง CCTV ของ Impex Spot</p>
            </div>
          )}
          
          <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-800">
             <button 
                onClick={saveConfig}
                className="text-slate-400 hover:text-white font-medium px-4 py-2"
              >
                ข้าม / เสร็จสิ้น
              </button>
            <button 
              onClick={saveConfig}
              className="bg-blue-600 text-white px-8 py-2 rounded-md hover:bg-blue-500 disabled:opacity-50 font-medium shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all flex items-center gap-2"
            >
              <Check className="w-5 h-5" /> บันทึกโซนและเสร็จสิ้น
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadAnalyzer;
