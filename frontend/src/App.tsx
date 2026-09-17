import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { Camera, LayoutDashboard, Settings, List, Upload, Activity, ShieldCheck, Share2 } from 'lucide-react';
import Dashboard from './components/Dashboard';
import CameraManager from './components/CameraManager';
import UploadAnalyzer from './components/UploadAnalyzer';
import LogsView from './components/LogsView';
import PublicViewer from './components/PublicViewer';
import Login from './components/Login';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

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

const AdminLayout = ({ children }: { children: React.ReactNode }) => {
  return (
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
            <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-semibold mt-0.5">Public Streaming Platform</p>
          </div>
        </div>
        
        <div className="px-6 pb-4">
            <div className="flex items-center gap-2 px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-md text-green-400 text-xs font-medium">
              <ShieldCheck className="w-4 h-4" /> System Online
            </div>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3 px-3">Command Center</div>
          <NavLink to="/" icon={LayoutDashboard}>NVR Dashboard</NavLink>
          <NavLink to="/logs" icon={List}>Historical Analytics</NavLink>
          
          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider mt-8 mb-3 px-3">Configuration</div>
          <NavLink to="/channels" icon={Settings}>Channel Manager</NavLink>
          <NavLink to="/upload" icon={Upload}>File Upload (Legacy)</NavLink>
        </nav>
        
        <div className="p-4 border-t border-slate-800/60">
          <div className="flex items-center gap-3 px-3 py-2 text-xs text-slate-500">
            <Activity className="w-4 h-4 text-blue-500/70" />
            <span>AI Engine Active</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto bg-[#0B0F19] relative">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiLz48L3N2Zz4=')] opacity-50 pointer-events-none"></div>
        
        <div className="relative z-10 p-8 h-full">
          {children}
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes (No Sidebar) */}
        <Route path="/view/:slug" element={<PublicViewer />} />
        <Route path="/login" element={<Login />} />

        {/* Admin Routes (With Sidebar) */}
        <Route path="/" element={<ProtectedRoute><AdminLayout><Dashboard /></AdminLayout></ProtectedRoute>} />
        <Route path="/channels" element={<ProtectedRoute><AdminLayout><CameraManager /></AdminLayout></ProtectedRoute>} />
        <Route path="/cameras" element={<ProtectedRoute><AdminLayout><CameraManager /></AdminLayout></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><AdminLayout><UploadAnalyzer /></AdminLayout></ProtectedRoute>} />
        <Route path="/logs" element={<ProtectedRoute><AdminLayout><LogsView /></AdminLayout></ProtectedRoute>} />
      </Routes>
    </Router>
  );
}

export default App;
