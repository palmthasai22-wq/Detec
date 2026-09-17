import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Camera, LayoutDashboard, Settings, List, Upload, Activity, ShieldCheck } from 'lucide-react';
import Dashboard from './components/Dashboard';
import CameraManager from './components/CameraManager';
import UploadAnalyzer from './components/UploadAnalyzer';
import LogsView from './components/LogsView';

const NavLink = ({ to, icon: Icon, children }: { to: string, icon: any, children: React.ReactNode }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link 
      to={to} 
      className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${
        isActive 
          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[0_0_15px_rgba(37,99,235,0.1)]' 
          : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
      }`}
    >
      <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
      <span className="font-medium tracking-wide text-sm">{children}</span>
      {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_#3b82f6]"></div>}
    </Link>
  );
};

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-[#0B0F19] text-slate-200 font-sans selection:bg-blue-500/30">
        {/* Sidebar - Enterprise Dark Theme */}
        <aside className="w-72 bg-[#0F1523] border-r border-slate-800/60 flex flex-col shadow-2xl relative z-20">
          <div className="p-6 flex items-center gap-3">
            <div className="relative">
              <Camera className="w-8 h-8 text-blue-500" />
              <div className="absolute top-0 right-0 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-[#0F1523]"></div>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Nexus<span className="text-blue-500">AI</span></h1>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-semibold mt-0.5">ระบบวิเคราะห์การจราจร</p>
            </div>
          </div>
          
          <div className="px-6 pb-4">
             <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-md text-green-400 text-xs font-medium">
               <ShieldCheck className="w-4 h-4" /> ระบบออนไลน์
             </div>
          </div>

          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3 px-3">ศูนย์ควบคุมหลัก</div>
            <NavLink to="/" icon={LayoutDashboard}>หน้าจอมอนิเตอร์</NavLink>
            <NavLink to="/logs" icon={List}>สถิติและรายงาน</NavLink>
            
            <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider mt-8 mb-3 px-3">ตั้งค่าระบบ</div>
            <NavLink to="/cameras" icon={Settings}>จัดการกล้อง</NavLink>
            <NavLink to="/upload" icon={Upload}>อัปโหลดวิดีโอ (โดรน)</NavLink>
          </nav>
          
          <div className="p-4 border-t border-slate-800/60">
            <div className="flex items-center gap-3 px-3 py-2 text-xs text-slate-500">
              <Activity className="w-4 h-4 text-blue-500/70" />
              <span>ระบบ AI YOLO26m ทำงานอยู่</span>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto bg-[#0B0F19] relative">
          {/* Subtle background grid pattern */}
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiLz48L3N2Zz4=')] opacity-50 pointer-events-none"></div>
          
          <div className="relative z-10 p-8 h-full">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/cameras" element={<CameraManager />} />
              <Route path="/upload" element={<UploadAnalyzer />} />
              <Route path="/logs" element={<LogsView />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
