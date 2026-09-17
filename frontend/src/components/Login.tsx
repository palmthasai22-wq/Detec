import React, { useState } from 'react';
import { Camera } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '';
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await axios.post(`${apiUrl}/api/auth/token`, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        navigate('/');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#0B0F19] text-slate-200 selection:bg-blue-500/30 font-sans p-4">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiLz48L3N2Zz4=')] opacity-50 pointer-events-none"></div>
      
      <div className="w-full max-w-md bg-[#0F1523] border border-slate-800/60 rounded-xl shadow-2xl overflow-hidden relative z-10">
        <div className="p-8 pb-6 text-center border-b border-slate-800/60">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <Camera className="w-12 h-12 text-blue-500" />
              <div className="absolute top-0 right-0 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-[#0F1523]"></div>
            </div>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent mb-1">Nexus<span className="text-blue-500">AI</span> Admin</h1>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500 font-semibold">Secure Authentication</p>
        </div>
        
        <div className="p-8">
          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-md text-red-400 text-sm font-medium text-center">
              {error}
            </div>
          )}
          
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-[#0B0F19] border border-slate-800 focus:border-blue-500/50 rounded-lg p-3 text-slate-200 outline-none transition-colors"
                required
                placeholder="Enter admin username"
              />
            </div>
            
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0B0F19] border border-slate-800 focus:border-blue-500/50 rounded-lg p-3 text-slate-200 outline-none transition-colors"
                required
                placeholder="Enter password"
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className={`w-full mt-2 bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-lg shadow-[0_0_15px_rgba(37,99,235,0.3)] transition-all ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
