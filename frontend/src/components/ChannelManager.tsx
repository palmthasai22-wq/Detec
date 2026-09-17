import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Edit2, Trash2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Channel {
  id: number;
  name: string;
  source_type: string;
  source_url: string;
  ai_model: string;
  confidence_threshold: number;
}

export const ChannelManager: React.FC = () => {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [currentChannel, setCurrentChannel] = useState<Partial<Channel>>({});
  const [loading, setLoading] = useState(false);

  const fetchChannels = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/channels`);
      setChannels(res.data);
    } catch (err) {
      console.error('Failed to fetch channels:', err);
    }
  };

  useEffect(() => {
    fetchChannels();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (currentChannel.id) {
        await axios.put(`${API_URL}/api/channels/${currentChannel.id}`, currentChannel);
      } else {
        await axios.post(`${API_URL}/api/channels`, currentChannel);
      }
      setIsEditing(false);
      setCurrentChannel({});
      fetchChannels();
    } catch (err) {
      console.error('Failed to save channel:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await axios.delete(`${API_URL}/api/channels/${id}`);
      fetchChannels();
    } catch (err) {
      console.error('Failed to delete channel:', err);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Channels</h2>
        <button
          onClick={() => {
            setIsEditing(true);
            setCurrentChannel({ confidence_threshold: 0.5, source_type: 'mp4' });
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Plus size={20} /> Add Channel
        </button>
      </div>

      {isEditing && (
        <form onSubmit={handleSave} className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              required
              value={currentChannel.name || ''}
              onChange={(e) => setCurrentChannel({ ...currentChannel, name: e.target.value })}
              className="w-full border rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Source Type</label>
            <select
              value={currentChannel.source_type || 'mp4'}
              onChange={(e) => setCurrentChannel({ ...currentChannel, source_type: e.target.value })}
              className="w-full border rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              {['mp4', 'rtsp', 'rtmp', 'srt', 'hls', 'webrtc', 'youtube', 'youtube_live'].map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Source URL</label>
            <input
              type="text"
              required
              value={currentChannel.source_url || ''}
              onChange={(e) => setCurrentChannel({ ...currentChannel, source_url: e.target.value })}
              className="w-full border rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">AI Model</label>
            <input
              type="text"
              required
              value={currentChannel.ai_model || ''}
              onChange={(e) => setCurrentChannel({ ...currentChannel, ai_model: e.target.value })}
              className="w-full border rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Confidence Threshold ({currentChannel.confidence_threshold || 0})
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={currentChannel.confidence_threshold || 0}
              onChange={(e) => setCurrentChannel({ ...currentChannel, confidence_threshold: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>
          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg font-medium">
              {loading ? 'Saving...' : 'Save Channel'}
            </button>
            <button type="button" onClick={() => setIsEditing(false)} className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-5 py-2 rounded-lg font-medium">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Source</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Model</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {channels.map((ch) => (
              <tr key={ch.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{ch.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className="uppercase text-xs font-bold bg-gray-100 px-2 py-1 rounded">{ch.source_type}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{ch.ai_model}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 flex gap-3">
                  <button onClick={() => { setIsEditing(true); setCurrentChannel(ch); }} className="text-blue-600 hover:text-blue-800 transition-colors">
                    <Edit2 size={18} />
                  </button>
                  <button onClick={() => handleDelete(ch.id)} className="text-red-600 hover:text-red-800 transition-colors">
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
            {channels.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  No channels found. Create one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
