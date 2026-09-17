import React, { useState } from 'react';
import axios from 'axios';
import { Copy, RefreshCw, Share2, EyeOff, Globe, MessageCircle, MessageSquare, X, Code } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ShareManagerProps {
  channel_id: number;
  is_shared: boolean;
  public_url_slug: string | null;
  onUpdate: () => void;
}

export const ShareManager: React.FC<ShareManagerProps> = ({
  channel_id,
  is_shared,
  public_url_slug,
  onUpdate
}) => {
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const toggleShare = async () => {
    setLoading(true);
    try {
      if (is_shared) {
        await axios.delete(`${API_URL}/api/channels/${channel_id}/share`);
      } else {
        await axios.post(`${API_URL}/api/channels/${channel_id}/share`);
      }
      onUpdate();
    } catch (err) {
      console.error('Failed to toggle share:', err);
    } finally {
      setLoading(false);
    }
  };

  const regenerateLink = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/channels/${channel_id}/share/regenerate`);
      onUpdate();
    } catch (err) {
      console.error('Failed to regenerate link:', err);
    } finally {
      setLoading(false);
    }
  };

  const publicLink = `${window.location.origin}/view/${public_url_slug}`;
  const embedCode = `<iframe src="${publicLink}?embed=true" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>`;

  const copyLink = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  return (
    <div className="bg-[#151B2B] p-5 rounded-xl shadow-sm border border-slate-800 text-slate-200">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Share2 size={20} className="text-blue-500" /> Public Streaming
        </h3>
        <div className="flex gap-2">
          {is_shared && (
            <button
              onClick={() => setShowModal(true)}
              className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white transition-colors"
            >
              Share View
            </button>
          )}
          <button
            onClick={toggleShare}
            disabled={loading}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              is_shared 
                ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30' 
                : 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30'
            }`}
          >
            {is_shared ? <><EyeOff size={16} /> Disable Sharing</> : <><Share2 size={16} /> Enable Sharing</>}
          </button>
        </div>
      </div>

      {showModal && is_shared && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
          <div className="bg-[#282828] text-white w-[500px] rounded-xl overflow-hidden shadow-2xl relative p-6">
            <button 
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white"
            >
              <X size={24} />
            </button>
            <h2 className="text-xl font-medium mb-6">Share public stream</h2>
            
            <div className="flex items-center justify-start gap-6 mb-8 overflow-x-auto pb-2">
              <div className="flex flex-col items-center gap-2 cursor-pointer group" onClick={() => copyLink(embedCode)}>
                <div className="w-14 h-14 rounded-full bg-[#3d3d3d] group-hover:bg-[#4d4d4d] flex items-center justify-center transition-colors">
                  <Code size={24} className="text-white" />
                </div>
                <span className="text-xs text-gray-300">Embed</span>
              </div>
              <div className="flex flex-col items-center gap-2 cursor-pointer group">
                <div className="w-14 h-14 rounded-full bg-[#3b5998] flex items-center justify-center transition-transform group-hover:scale-105">
                  <Globe size={24} className="text-white" />
                </div>
                <span className="text-xs text-gray-300">Facebook</span>
              </div>
              <div className="flex flex-col items-center gap-2 cursor-pointer group">
                <div className="w-14 h-14 rounded-full bg-[#007aff] flex items-center justify-center transition-transform group-hover:scale-105">
                  <MessageSquare size={24} className="text-white fill-white" />
                </div>
                <span className="text-xs text-gray-300">Messages</span>
              </div>
              <div className="flex flex-col items-center gap-2 cursor-pointer group">
                <div className="w-14 h-14 rounded-full bg-[#25D366] flex items-center justify-center transition-transform group-hover:scale-105">
                  <MessageCircle size={24} className="text-white" />
                </div>
                <span className="text-xs text-gray-300">WhatsApp</span>
              </div>
              <div className="flex flex-col items-center gap-2 cursor-pointer group">
                <div className="w-14 h-14 rounded-full bg-black border border-gray-600 flex items-center justify-center transition-transform group-hover:scale-105">
                  <span className="text-2xl font-bold text-white">𝕏</span>
                </div>
                <span className="text-xs text-gray-300">X</span>
              </div>
            </div>

            <div className="bg-[#121212] border border-gray-700 rounded-lg flex items-center justify-between p-1.5">
              <div className="px-3 overflow-hidden">
                <p className="text-sm text-gray-300 truncate w-64">{publicLink}</p>
              </div>
              <button 
                onClick={() => copyLink(publicLink)}
                className="bg-[#3EA6FF] hover:bg-[#5EBBFF] text-black font-medium text-sm px-4 py-2 rounded-full transition-colors"
              >
                Copy
              </button>
            </div>
            
            <div className="mt-4 flex justify-end">
               <button onClick={regenerateLink} className="text-xs text-gray-400 hover:text-white flex items-center gap-1">
                 <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Regenerate URL
               </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
