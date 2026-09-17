import React, { useEffect, useRef } from 'react';

interface WebrtcPlayerProps {
  url: string;
}

export const WebrtcPlayer: React.FC<WebrtcPlayerProps> = ({ url }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let pc: RTCPeerConnection;

    const initWebRTC = async () => {
      pc = new RTCPeerConnection();

      pc.addTransceiver('video', { direction: 'recvonly' });
      pc.addTransceiver('audio', { direction: 'recvonly' });

      pc.ontrack = (event) => {
        if (video.srcObject !== event.streams[0]) {
          video.srcObject = event.streams[0];
        }
      };

      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/sdp',
          },
          body: offer.sdp,
        });

        if (response.ok) {
          const answerSdp = await response.text();
          await pc.setRemoteDescription(
            new RTCSessionDescription({ type: 'answer', sdp: answerSdp })
          );
        } else {
          console.error('WHEP connection failed:', response.statusText);
        }
      } catch (error) {
        console.error('Error starting WebRTC:', error);
      }
    };

    initWebRTC();

    return () => {
      if (pc) {
        pc.close();
      }
      if (video.srcObject) {
        const stream = video.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [url]);

  return (
    <video
      ref={videoRef}
      className="w-full h-full object-contain bg-black"
      autoPlay
      muted
      playsInline
    />
  );
};
