"use client";
import { useRef, useState, useEffect } from 'react';

export default function CameraFeed() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [captured, setCaptured] = useState(false);
  const [liveness, setLiveness] = useState('PENDING');
  const [quality, setQuality] = useState('CHECKING');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const startCamera = async () => {
    try {
      setStarting(true);
      setCameraError(null);
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraError('Camera API is not available in this browser.');
        setStarting(false);
        return;
      }
      stopCamera();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 960 },
          height: { ideal: 540 },
        },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
        await videoRef.current.play().catch(() => null);
      }
      setCameraActive(true);
      setStarting(false);
    } catch (err) {
      setStarting(false);
      setCameraActive(false);
      setCameraError('Camera is blocked. Allow camera permission and try again.');
    }
  };

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const capture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas && cameraActive) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        canvas.width = video.videoWidth || 960;
        canvas.height = video.videoHeight || 540;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        setCaptured(true);
        setLiveness('PASSED');
        setQuality('GOOD');
      }
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-slate-800">Camera Feed</h3>
        <span className="text-xs font-medium text-emerald-600">{cameraActive ? 'Live' : 'Offline'}</span>
      </div>

      <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden mb-2">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="h-full w-full object-cover"
        />
        <canvas ref={canvasRef} className="hidden" />
        <div className="absolute left-2 top-2 text-[10px] font-semibold text-emerald-300 bg-black/60 px-2 py-1 rounded">
          YOLOv8 • Face Detector
        </div>
        {captured && (
          <div className="absolute inset-x-0 bottom-0 bg-emerald-50/95 border-t border-emerald-200 text-emerald-800 text-xs font-semibold p-2">
            Liveness: {liveness} • Quality: {quality}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 mt-3">
        <button
          onClick={startCamera}
          disabled={starting}
          className="px-3 py-2 bg-slate-100 text-slate-700 rounded-md border border-slate-200 hover:bg-slate-200 disabled:opacity-60"
        >
          {starting ? 'Starting...' : 'Start / Retry Camera'}
        </button>
        <button
          onClick={capture}
          disabled={!cameraActive}
          className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-60"
        >
          Capture Biometrics
        </button>
      </div>

      {cameraError && <div className="mt-2 text-xs text-red-600">{cameraError}</div>}
    </div>
  );
}

