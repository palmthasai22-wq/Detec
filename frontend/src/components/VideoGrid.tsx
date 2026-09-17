import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChannelTile } from './ChannelTile';
import type { Channel } from './ChannelTile';

type Layout = 1 | 2 | 3 | 4;

export const VideoGrid: React.FC = () => {
  const [layout, setLayout] = useState<Layout>(2);
  const [channels, setChannels] = useState<Channel[]>([]);

  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL || ''}/api/channels`);
        setChannels(response.data);
      } catch (error) {
        console.error('Failed to fetch channels:', error);
      }
    };
    fetchChannels();
  }, []);

  const totalCells = layout * layout;
  const gridCells = Array.from({ length: totalCells }, (_, i) => channels[i]);

  const getGridClass = () => {
    switch (layout) {
      case 1: return 'grid-cols-1';
      case 2: return 'grid-cols-2';
      case 3: return 'grid-cols-3';
      case 4: return 'grid-cols-4';
      default: return 'grid-cols-2';
    }
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex justify-end gap-2 p-2 bg-gray-900 border-b border-gray-800">
        {[1, 2, 3, 4].map((num) => (
          <button
            key={num}
            onClick={() => setLayout(num as Layout)}
            className={`px-3 py-1 text-sm font-medium rounded ${
              layout === num
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {num}x{num}
          </button>
        ))}
      </div>
      <div className={`flex-grow grid ${getGridClass()} gap-1 bg-gray-950 p-1`}>
        {gridCells.map((channel, index) => (
          <div key={channel?.id || `empty-${index}`} className="w-full h-full min-h-[200px]">
            {channel ? (
              <ChannelTile channel={channel} />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gray-900 text-gray-500 border border-gray-800">
                No Camera Assigned
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
