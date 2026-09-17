import React from 'react';
import { HlsPlayer } from './HlsPlayer';

export interface Channel {
  id: string;
  name: string;
  status: string;
  hlsUrl?: string;
}

export interface Stats {
  densityIndex?: number;
  trafficLevel?: string;
}

interface ChannelTileProps {
  channel: Channel;
  stats?: Stats;
}

export const ChannelTile: React.FC<ChannelTileProps> = ({ channel, stats }) => {
  const fallbackUrl = `${import.meta.env.VITE_API_URL}/api/streams/${channel.id}/stream.mjpg`;

  return (
    <div className="relative w-full h-full bg-black border border-gray-700 overflow-hidden flex items-center justify-center">
      {channel.hlsUrl ? (
        <HlsPlayer url={channel.hlsUrl} />
      ) : (
        <img
          src={fallbackUrl}
          alt={channel.name}
          className="w-full h-full object-contain"
        />
      )}
      <div className="absolute top-0 left-0 p-2 bg-black/50 text-white w-full flex justify-between items-center text-sm z-10">
        <span className="font-semibold">{channel.name}</span>
        {stats && (
          <div className="flex gap-4">
            {stats.densityIndex !== undefined && (
              <span>Density: {stats.densityIndex}</span>
            )}
            {stats.trafficLevel && (
              <span>Traffic: {stats.trafficLevel}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
