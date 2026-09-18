import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, Wifi, WifiOff, Loader2, Cpu, CloudLightning } from 'lucide-react';
import { getApiUrl } from '../config/api';

interface Camera {
  id: number;
  name: string;
  source_type: string;
  source_url: string;
  density_green_threshold: number;
  density_yellow_threshold: number;
  confidence_threshold: number;
  engine: string;
  roboflow_model_id?: string;
  roboflow_api_key?: string;
  lat?: number;
  lng?: number;
  embed_url?: string;
  embed_mode?: 'image' | 'iframe';
  public_id: string;
  is_shared?: boolean;
  public_url_slug?: string;
}

const parseEmbedInput = (input: string) => {
  const value = input.trim();
  if (!value) return null;
  const iframeMatch = value.match(/<iframe\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/i);
  const url = iframeMatch?.[1] || value;
  const parsed = new URL(url);
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('URL ภาพสด/iframe ต้องเป็น http หรือ https');
  return { url: parsed.toString(), mode: iframeMatch ? 'iframe' as const : 'image' as const };
};

const CameraManager = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{success: boolean, message: string} | null>(null);
  const [embedInput, setEmbedInput] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [formData, setFormData] = useState<any>({
    name: '', source_type: 'rtsp', source_url: '', 
    density_green_threshold: 10, density_yellow_threshold: 20,
    confidence_threshold: 0.15,
    engine: 'yolo', roboflow_model_id: '', roboflow_api_key: '',
    lat: '', lng: ''
  });

  const fetchCameras = () => {
    axios.get('/api/cameras')
      .then(res => setCameras(Array.isArray(res.data) ? res.data : []))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');
    try {
      const payload = { ...formData };
      const embed = parseEmbedInput(embedInput);
      payload.source_url = String(payload.source_url || '').trim();
      if (!payload.source_url) delete payload.source_url;
      
      if (embed) {
        payload.embed_url = embed.url;
        payload.embed_mode = embed.mode;
        if (!payload.source_url) payload.source_type = 'embed';
      }
      if (payload.lat !== '' && payload.lng !== '') {
        payload.lat = parseFloat(payload.lat);
        payload.lng = parseFloat(payload.lng);
      } else {
        delete payload.lat;
        delete payload.lng;
      }
      await axios.post('/api/cameras', payload);
      fetchCameras();
      setShowForm(false);
      setEmbedInput('');
      setFormData({ name: '', source_type: 'rtsp', source_url: '', density_green_threshold: 10, density_yellow_threshold: 20, confidence_threshold: 0.15, engine: 'yolo', roboflow_model_id: '', roboflow_api_key: '', lat: '', lng: '' });
      setTestResult(null);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail) ? detail.map(item => item.msg).join(', ') : detail;
      setSubmitError(message || err.message || 'บันทึกกล้องไม่สำเร็จ');
    }
  };

  const handleDelete = (id: number) => {
    if(confirm("ต้องการลบกล้องนี้หรือไม่?")) {
      axios.delete(`/api/cameras/${id}`)
        .then(() => fetchCameras());
    }
  };

  const handleTestConnection = async () => {
    if (!formData.source_url) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await axios.post('/api/streams/test-connection', { url: formData.source_url });
      setTestResult({
        success: res.data.status === 'success',
        message: res.data.message === 'Connection successful' ? 'เชื่อมต่อสำเร็จ' : (res.data.message || 'เชื่อมต่อสำเร็จ')
      });
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.response?.data?.detail || 'เชื่อมต่อล้มเหลว'
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="animate-in fade-in duration-500 max-w-5xl mx-auto">
      <div className="flex justify-between items-end mb-8 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            จัดการระบบกล้อง
          </h2>
          <p className="text-slate-400 mt-2">ตั้งค่าแหล่งวิดีโอ ระบบ AI และความไวของการแจ้งเตือน</p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)] font-medium"
        >
          <Plus className="w-5 h-5" /> เพิ่มกล้องใหม่
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-[#0F1523] border border-slate-700 p-8 rounded-xl mb-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>
          
          <h3 className="text-xl font-bold text-white mb-6">การตั้งค่ากล้อง</h3>
          
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ชื่อกล้อง</label>
                <input required className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors" 
                  value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="เช่น แยกราชประสงค์" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ละติจูด (Latitude)</label>
                  <input type="number" min="-90" max="90" step="any" required={Boolean(formData.lng)} className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                    value={formData.lat} onChange={e => setFormData({...formData, lat: e.target.value})} placeholder="13.7563" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ลองจิจูด (Longitude)</label>
                  <input type="number" min="-180" max="180" step="any" required={Boolean(formData.lat)} className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                    value={formData.lng} onChange={e => setFormData({...formData, lng: e.target.value})} placeholder="100.5018" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ประเภท</label>
                  <select className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                    value={formData.source_type} onChange={e => setFormData({...formData, source_type: e.target.value as any})}>
                    <option value="rtsp">RTSP (กล้องวงจรปิด)</option>
                    <option value="rtmp">RTMP (โดรน)</option>
                    <option value="mp4">ไฟล์วิดีโอ (MP4)</option>
                    <option value="youtube">YouTube</option>
                    <option value="youtube_live">YouTube Live</option>
                    <option value="hls">HLS Stream</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ค่าความแม่นยำ (Confidence)</label>
                  <input type="number" step="0.05" required className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white" 
                    value={formData.confidence_threshold} onChange={e => setFormData({...formData, confidence_threshold: parseFloat(e.target.value)})} />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">URL สตรีมสำหรับ AI</label>
                <div className="flex gap-2">
                  <input required={!embedInput.trim()} className="flex-1 bg-black/50 border border-slate-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors font-mono text-sm"
                    value={formData.source_url} onChange={e => setFormData({...formData, source_url: e.target.value})} 
                    placeholder={formData.source_type === 'rtsp' ? 'rtsp://admin:pass@192.168.1.100/stream' : 'rtmp://127.0.0.1/live/drone'} />
                  
                  {formData.source_type !== 'file' && (
                    <button type="button" onClick={handleTestConnection} disabled={testing || !formData.source_url}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 rounded-lg flex items-center justify-center transition-colors border border-slate-600 disabled:opacity-50 min-w-[120px]">
                      {testing ? <Loader2 className="w-5 h-5 animate-spin" /> : 'ทดสอบลิงก์'}
                    </button>
                )}
              </div>
              <div>
                <label className="block text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">URL ภาพสด หรือโค้ด iframe (ไม่บังคับ)</label>
                <textarea rows={3} className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors font-mono text-xs"
                  value={embedInput} onChange={e => setEmbedInput(e.target.value)}
                  placeholder={'https://camera.example/live.jpg\nหรือ <iframe src="https://example.com/embed/camera"></iframe>'} />
                <p className="mt-1 text-[10px] text-slate-500">ระบบจะเก็บเฉพาะ URL ที่ปลอดภัยจาก src และจะไม่รัน HTML ที่วางมาโดยตรง</p>
              </div>
              {testResult && (
                  <div className={`mt-3 p-3 rounded-md flex items-center gap-2 text-sm ${testResult.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                    {testResult.success ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                    {testResult.message}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4 border-l border-slate-800 pl-6">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">ระบบประมวลผล AI</label>
                <div className="flex bg-black/50 rounded-lg p-1 border border-slate-700">
                  <button type="button" 
                    onClick={() => setFormData({...formData, engine: 'yolo'})}
                    className={`flex-1 py-2 flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors ${formData.engine === 'yolo' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                    <Cpu className="w-4 h-4" /> YOLO26 (ในเครื่อง)
                  </button>
                  <button type="button" 
                    onClick={() => setFormData({...formData, engine: 'roboflow'})}
                    className={`flex-1 py-2 flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors ${formData.engine === 'roboflow' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                    <CloudLightning className="w-4 h-4" /> Roboflow (คลาวด์)
                  </button>
                </div>
              </div>

              {formData.engine === 'roboflow' ? (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div>
                    <label className="block text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">รหัสโมเดล Roboflow (Model ID)</label>
                    <input required={formData.engine === 'roboflow'} className="w-full bg-black/50 border border-purple-900/50 rounded-lg p-3 text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors font-mono text-sm" 
                      value={formData.roboflow_model_id} onChange={e => setFormData({...formData, roboflow_model_id: e.target.value})} placeholder="เช่น vehicle-detection-aerial/1" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">Roboflow API Key</label>
                    <input type="password" required={formData.engine === 'roboflow'} className="w-full bg-black/50 border border-purple-900/50 rounded-lg p-3 text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors font-mono text-sm" 
                      value={formData.roboflow_api_key} onChange={e => setFormData({...formData, roboflow_api_key: e.target.value})} placeholder="รหัส API ส่วนตัวของคุณ" />
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-yellow-500 uppercase tracking-wider mb-2">แจ้งเตือนสีเหลือง (คัน)</label>
                      <input type="number" required className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white" 
                        value={formData.density_yellow_threshold} onChange={e => setFormData({...formData, density_yellow_threshold: parseInt(e.target.value)})} />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-red-500 uppercase tracking-wider mb-2">แจ้งเตือนสีแดง (คัน)</label>
                      <input type="number" required className="w-full bg-black/50 border border-slate-700 rounded-lg p-3 text-white" 
                        value={formData.density_green_threshold} onChange={e => setFormData({...formData, density_green_threshold: parseInt(e.target.value)})} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="mt-8 flex justify-end gap-3">
            {submitError && <div role="alert" className="mr-auto rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">{submitError}</div>}
            <button type="button" onClick={() => setShowForm(false)} className="px-6 py-2.5 rounded-lg text-slate-400 hover:text-white font-medium">ยกเลิก</button>
            <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-2.5 rounded-lg font-medium shadow-[0_0_15px_rgba(37,99,235,0.4)]">บันทึกและติดตั้ง</button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cameras.map(camera => (
          <div key={camera.id} className="bg-[#0F1523] border border-slate-800 rounded-xl p-5 relative group hover:border-slate-600 transition-colors">
            <button 
              onClick={() => handleDelete(camera.id)}
              className="absolute top-4 right-4 text-slate-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Trash2 className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 rounded-lg ${camera.engine === 'roboflow' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                {camera.engine === 'roboflow' ? <CloudLightning className="w-6 h-6" /> : <Cpu className="w-6 h-6" />}
              </div>
              <div>
                <h3 className="font-bold text-white text-lg">{camera.name}</h3>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{camera.source_type.toUpperCase()} • {(camera.engine || 'yolo').toUpperCase()}</span>
              </div>
            </div>
            <div className="bg-black/50 rounded-lg p-3 mb-4 border border-slate-800">
              <p className="text-xs font-mono text-slate-400 truncate" title={camera.source_url}>{camera.source_url}</p>
            </div>
            {camera.source_type !== 'embed' && (
              <div className="mb-4 rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3 space-y-4">
                <div>
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-cyan-400">URL วิดีโอดิบสำหรับแผนที่ (MJPEG Direct)</p>
                  <div className="flex gap-2">
                    <div className="min-w-0 flex-1 truncate font-mono text-[10px] text-cyan-300 bg-black/50 px-2 py-1 rounded border border-cyan-500/20">
                      {getApiUrl(`/api/streams/${camera.id}`)}
                    </div>
                    <button type="button" onClick={() => navigator.clipboard.writeText(getApiUrl(`/api/streams/${camera.id}`))} className="rounded bg-cyan-600/20 px-2 py-1 text-[10px] font-semibold text-cyan-300 hover:bg-cyan-600/30 whitespace-nowrap">คัดลอกลิงก์</button>
                  </div>
                  <p className="mt-1 text-[10px] text-slate-500">ใช้ลิงก์นี้เมื่อแผนที่ต้องการไฟล์ภาพ/วิดีโอ (เช่น <code>&lt;img src="..."&gt;</code>)</p>
                </div>
                
                <div className="pt-3 border-t border-slate-700/50">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-blue-400">Public Viewer URL (หน้าเว็บ Dashboard)</p>
                    <button 
                      type="button" 
                      onClick={async () => {
                        try {
                          await axios.post(getApiUrl(`/api/channels/${camera.id}/share`));
                          fetchCameras(); // Refresh the list
                        } catch (e) {
                          alert('Failed to toggle share');
                        }
                      }}
                      className={`text-[10px] px-2 py-1 rounded font-semibold ${camera.is_shared ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'}`}
                    >
                      {camera.is_shared ? 'ปิดการแชร์' : 'เปิดการแชร์ (Enable Public Link)'}
                    </button>
                  </div>
                  
                  {camera.is_shared && camera.public_url_slug ? (
                    <div>
                      <div className="flex gap-2">
                        <div className="min-w-0 flex-1 truncate font-mono text-[10px] text-blue-300 bg-black/50 px-2 py-1 rounded border border-blue-500/20">
                          {window.location.origin}/view/{camera.public_url_slug}
                        </div>
                        <button type="button" onClick={() => navigator.clipboard.writeText(`${window.location.origin}/view/${camera.public_url_slug}`)} className="rounded bg-blue-600/20 px-2 py-1 text-[10px] font-semibold text-blue-300 hover:bg-blue-600/30 whitespace-nowrap">คัดลอกลิงก์</button>
                      </div>
                      <p className="mt-1 text-[10px] text-slate-500">ใช้ลิงก์นี้เมื่อแผนที่ต้องการหน้าเว็บ iframe</p>
                    </div>
                  ) : (
                    <p className="text-[10px] text-slate-500 italic">กด "เปิดการแชร์" เพื่อสร้างลิงก์สำหรับ iframe</p>
                  )}
                </div>
              </div>
            )}
            <div className="flex justify-between items-center text-sm border-t border-slate-800/60 pt-4">
              <span className="text-slate-400">ความไวแจ้งเตือนรถติด</span>
              <span className="font-medium text-white">{camera.density_yellow_threshold} คัน</span>
            </div>
          </div>
        ))}
        {cameras.length === 0 && !showForm && (
          <div className="col-span-full py-12 text-center border border-dashed border-slate-700 rounded-xl">
            <p className="text-slate-500 mb-2">ยังไม่ได้ตั้งค่ากล้องวิดีโอ</p>
            <button onClick={() => setShowForm(true)} className="text-blue-500 hover:text-blue-400 font-medium">เพิ่มกล้องตัวแรกของคุณ</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraManager;
