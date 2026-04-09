'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { extractErrorMessage } from '@/lib/errors';

interface MatchResult {
  patient_id: string;
  confidence: number;
  name?: string;
  age?: number;
  gender?: string;
  identifier?: string;
}

type CaptureState = 'idle' | 'requesting' | 'streaming' | 'capturing' | 'processing' | 'success' | 'error';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

// SA ID validation and extraction
function validateSAID(id: string): { valid: boolean; age?: number; gender?: string; error?: string } {
  if (!/^\d{13}$/.test(id)) {
    return { valid: false, error: 'SA ID must be exactly 13 digits' };
  }
  
  const yy = parseInt(id.substring(0, 2), 10);
  const mm = parseInt(id.substring(2, 4), 10);
  const dd = parseInt(id.substring(4, 6), 10);
  const genderDigits = parseInt(id.substring(6, 10), 10);
  
  if (mm < 1 || mm > 12) return { valid: false, error: 'Invalid month in ID' };
  if (dd < 1 || dd > 31) return { valid: false, error: 'Invalid day in ID' };
  
  const currentYear = new Date().getFullYear() % 100;
  const century = yy > currentYear ? 1900 : 2000;
  const birthYear = century + yy;
  const age = new Date().getFullYear() - birthYear;
  
  const gender = genderDigits >= 5000 ? 'M' : 'F';
  
  return { valid: true, age, gender };
}

function FaceCaptureWidget({
  onCapture,
  matchResult,
}: {
  onCapture: (imageBlob: Blob) => Promise<void>;
  matchResult: MatchResult | null;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [state, setState] = useState<CaptureState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [cameraHint, setCameraHint] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const resolveCameraError = (err: unknown) => {
    const e = err as { name?: string; message?: string };
    if (e?.name === 'NotAllowedError') {
      return 'Camera access denied. Please grant permission or use file upload.';
    }
    if (e?.name === 'NotReadableError' || e?.name === 'TrackStartError') {
      return 'Camera is busy in another app. Close Zoom/Teams/Camera app and retry.';
    }
    if (e?.name === 'NotFoundError' || e?.name === 'DevicesNotFoundError') {
      return 'No camera device found. Connect a camera or use upload.';
    }
    if (e?.name === 'OverconstrainedError') {
      return 'Camera cannot satisfy preferred settings. Retrying with fallback constraints.';
    }
    return `Failed to access camera: ${e?.message || 'Unknown camera error'}`;
  };

  const startCamera = useCallback(async () => {
    setState('requesting');
    setError(null);
    setCameraHint(null);

    if (typeof window === 'undefined' || !window.isSecureContext) {
      setError('Camera needs a secure context. Use http://127.0.0.1:3100 or https.');
      setState('error');
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Camera API is unavailable in this browser.');
      setState('error');
      return;
    }
    
    stopCamera();

    const attempts: MediaStreamConstraints[] = [
      { video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: { facingMode: 'user' }, audio: false },
      { video: true, audio: false },
      { video: { facingMode: { ideal: 'environment' } }, audio: false },
    ];

    let lastError: unknown = null;
    for (const constraints of attempts) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
          videoRef.current.muted = true;
          await videoRef.current.play().catch(() => null);
          setCameraHint('Camera is live. Center one face, then capture.');
          setState('streaming');
        }
        return;
      } catch (attemptErr) {
        lastError = attemptErr;
      }
    }

    setError(resolveCameraError(lastError));
    setState('error');
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraHint(null);
    setState('idle');
  }, []);

  const captureFrame = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera is not ready yet.');
      setState('error');
      return;
    }
    
    setState('capturing');
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    if (!video.videoWidth || !video.videoHeight) {
      setError('Camera stream is not ready. Retry in a moment.');
      setState('error');
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    // Check for black frame
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const pixels = imageData.data;
    let nonBlackCount = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      if (pixels[i] > 10 || pixels[i + 1] > 10 || pixels[i + 2] > 10) {
        nonBlackCount++;
      }
    }
    
    if (nonBlackCount < (pixels.length / 4) * 0.1) {
      setError('Camera feed appears black. Check camera connection.');
      setState('error');
      return;
    }
    
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setError('Failed to capture image');
        setState('error');
        return;
      }
      
      setState('processing');
      await onCapture(blob);
      setState('success');
    }, 'image/jpeg', 0.92);
  }, [onCapture]);

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.type.match(/^image\/(jpeg|png)$/)) {
      setError('Please upload a JPEG or PNG image');
      setState('error');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      setError('Image must be less than 5MB');
      setState('error');
      return;
    }
    
    setState('processing');
    await onCapture(file);
  }, [onCapture]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return (
    <div className="card">
      <div className="card-header">
        <h3>📷 Face Capture</h3>
        {state === 'streaming' && (
          <button className="btn btn-ghost text-sm" onClick={stopCamera}>
            Stop Camera
          </button>
        )}
      </div>

      {/* Video/Preview area */}
      <div style={{
        position: 'relative',
        width: '100%',
        aspectRatio: '4/3',
        background: 'var(--bg-tertiary)',
        borderRadius: 8,
        overflow: 'hidden',
        marginBottom: '1rem',
        border: matchResult 
          ? '3px solid var(--success)' 
          : state === 'error' 
            ? '3px solid var(--danger)' 
            : '1px solid var(--border-color)',
        animation: state === 'error' ? 'shake 0.5s' : 'none',
      }}>
        {state === 'idle' && (
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
          }}>
            <span style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📷</span>
            <span>Camera inactive</span>
          </div>
        )}
        
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: state === 'streaming' || state === 'capturing' ? 'block' : 'none',
          }}
        />
        
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        
        {state === 'processing' && (
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <div style={{ textAlign: 'center' }}>
              <div className="skeleton" style={{ width: 48, height: 48, borderRadius: '50%', margin: '0 auto 1rem' }} />
              <div>Processing face...</div>
            </div>
          </div>
        )}
        
        {matchResult && (
          <div style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            padding: '1rem',
            background: 'linear-gradient(transparent, rgba(0,0,0,0.8))',
          }}>
            <div style={{ color: 'var(--success)', fontWeight: 600, marginBottom: '0.25rem' }}>
              ✓ Match Found
            </div>
            <div className="font-mono" style={{ fontSize: '0.8rem' }}>
              Confidence: {(matchResult.confidence * 100).toFixed(1)}%
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="banner banner-warning" style={{ marginBottom: '1rem' }}>
          ⚠️ {error}
        </div>
      )}
      {cameraHint && !error && (
        <div className="banner banner-info" style={{ marginBottom: '1rem' }}>
          ℹ️ {cameraHint}
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {state === 'idle' || state === 'error' ? (
          <button className="btn btn-primary" onClick={startCamera}>
            🎥 Start Camera
          </button>
        ) : state === 'streaming' ? (
          <button className="btn btn-primary" onClick={captureFrame}>
            📸 Capture Face
          </button>
        ) : null}
        
        <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
          📁 Upload Image
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
        </label>
      </div>
      
      <style jsx>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }
      `}</style>
    </div>
  );
}

function VitalsForm({
  vitals,
  onChange,
}: {
  vitals: { systolic: string; diastolic: string; temp: string; o2: string; weight: string };
  onChange: (v: typeof vitals) => void;
}) {
  return (
    <div className="card">
      <div className="card-header">
        <h3>💓 Vitals Entry</h3>
      </div>
      
      <div className="grid-2" style={{ gap: '1rem' }}>
        <div>
          <label className="label">Systolic BP (mmHg)</label>
          <input
            type="number"
            className="input"
            placeholder="120"
            value={vitals.systolic}
            onChange={(e) => onChange({ ...vitals, systolic: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Diastolic BP (mmHg)</label>
          <input
            type="number"
            className="input"
            placeholder="80"
            value={vitals.diastolic}
            onChange={(e) => onChange({ ...vitals, diastolic: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Temperature (°C)</label>
          <input
            type="number"
            className="input"
            placeholder="36.5"
            step="0.1"
            value={vitals.temp}
            onChange={(e) => onChange({ ...vitals, temp: e.target.value })}
          />
        </div>
        <div>
          <label className="label">O₂ Saturation (%)</label>
          <input
            type="number"
            className="input"
            placeholder="98"
            max="100"
            value={vitals.o2}
            onChange={(e) => onChange({ ...vitals, o2: e.target.value })}
          />
        </div>
        <div style={{ gridColumn: 'span 2' }}>
          <label className="label">Weight (kg)</label>
          <input
            type="number"
            className="input"
            placeholder="70"
            step="0.1"
            value={vitals.weight}
            onChange={(e) => onChange({ ...vitals, weight: e.target.value })}
          />
        </div>
      </div>
    </div>
  );
}

function IntakeForm({
  matchResult,
  onSubmit,
}: {
  matchResult: MatchResult | null;
  onSubmit: (data: any) => Promise<void>;
}) {
  const [name, setName] = useState(matchResult?.name || '');
  const [identifier, setIdentifier] = useState(matchResult?.identifier || '');
  const [gender, setGender] = useState(matchResult?.gender || '');
  const [visitReason, setVisitReason] = useState('');
  const [idError, setIdError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [vitals, setVitals] = useState({ systolic: '', diastolic: '', temp: '', o2: '', weight: '' });

  useEffect(() => {
    if (matchResult) {
      setName(matchResult.name || '');
      setGender(matchResult.gender || '');
      setIdentifier(matchResult.identifier || '');
    }
  }, [matchResult]);

  const handleIdChange = (value: string) => {
    setIdentifier(value);
    setIdError(null);
    
    if (value.length === 13) {
      const result = validateSAID(value);
      if (!result.valid) {
        setIdError(result.error || 'Invalid SA ID');
      } else {
        // Auto-fill from ID
        if (result.gender && !gender) setGender(result.gender);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (identifier && identifier.length === 13) {
      const result = validateSAID(identifier);
      if (!result.valid) {
        setIdError(result.error || 'Invalid SA ID');
        return;
      }
    }
    
    setSubmitting(true);
    try {
      await onSubmit({
        name,
        identifier,
        gender,
        visit_reason: visitReason,
        vitals,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {matchResult && (
        <div className="banner banner-success" style={{ marginBottom: '1rem' }}>
          🎉 Returning Patient — Form pre-filled from previous visit
        </div>
      )}
      
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="card-header">
          <h3>📋 Patient Details</h3>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label className="label">Name (optional)</label>
            <input
              type="text"
              className="input"
              placeholder="Patient name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          
          <div>
            <label className="label">South African ID (13 digits)</label>
            <input
              type="text"
              className="input"
              placeholder="e.g. 9001015800083"
              maxLength={13}
              value={identifier}
              onChange={(e) => handleIdChange(e.target.value.replace(/\D/g, ''))}
              style={idError ? { borderColor: 'var(--danger)' } : {}}
            />
            {idError && (
              <div style={{ color: 'var(--danger)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                {idError}
              </div>
            )}
            {identifier.length === 13 && !idError && (
              <div style={{ color: 'var(--success)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                ✓ Valid SA ID
              </div>
            )}
          </div>
          
          <div>
            <label className="label">Gender</label>
            <select
              className="select"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
            >
              <option value="">Select gender</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </div>
          
          <div>
            <label className="label">Visit Reason *</label>
            <select
              className="select"
              value={visitReason}
              onChange={(e) => setVisitReason(e.target.value)}
              required
            >
              <option value="">Select reason</option>
              <option value="consultation">General Consultation</option>
              <option value="follow-up">Follow-up Visit</option>
              <option value="emergency">Emergency</option>
              <option value="antenatal">Antenatal Care</option>
              <option value="immunization">Immunization</option>
              <option value="chronic">Chronic Disease Management</option>
              <option value="mental-health">Mental Health</option>
              <option value="tb-hiv">TB/HIV Services</option>
            </select>
          </div>
        </div>
      </div>

      <VitalsForm vitals={vitals} onChange={setVitals} />

      <div style={{ marginTop: '1.5rem' }}>
        <button 
          type="submit" 
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.875rem' }}
          disabled={!visitReason || submitting}
        >
          {submitting ? '⏳ Creating Session...' : '✓ Create Patient Session'}
        </button>
      </div>
    </form>
  );
}

function SessionSuccess({ sessionToken }: { sessionToken: string }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
      <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
      <h2 style={{ marginBottom: '0.5rem' }}>Session Created</h2>
      <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
        Patient is checked in and ready for clinical assessment
      </p>
      
      <div style={{
        background: 'var(--bg-tertiary)',
        padding: '1.5rem',
        borderRadius: 12,
        marginBottom: '1.5rem',
      }}>
        <div className="text-sm text-muted" style={{ marginBottom: '0.5rem' }}>Session Token</div>
        <div className="font-mono" style={{ fontSize: '1.25rem', wordBreak: 'break-all' }}>
          {sessionToken}
        </div>
      </div>
      
      {/* QR Code placeholder */}
      <div style={{
        width: 200,
        height: 200,
        margin: '0 auto',
        background: 'white',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'black',
      }}>
        <span style={{ fontSize: '0.8rem' }}>QR Code</span>
      </div>
      
      <button 
        className="btn btn-secondary" 
        style={{ marginTop: '1.5rem' }}
        onClick={() => window.location.reload()}
      >
        Start New Intake
      </button>
    </div>
  );
}

export default function ClinicianDashboard() {
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [capturedImage, setCapturedImage] = useState<Blob | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFaceCapture = async (imageBlob: Blob) => {
    setCapturedImage(imageBlob);
    setError(null);
    
    const formData = new FormData();
    formData.append('face_image', imageBlob, 'capture.jpg');
    
    try {
      const res = await fetch(`${API_URL}/api/v1/biometric/identify`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(extractErrorMessage(data));
      }
      
      if (data.patient_id) {
        setMatchResult({
          patient_id: data.patient_id,
          confidence: data.confidence,
          name: data.name,
          age: data.age,
          gender: data.gender,
          identifier: data.identifier,
        });
      } else {
        setMatchResult(null);
      }
    } catch (err: any) {
      console.error('Face capture error:', err);
      // Don't show error for no match - that's expected for new patients
      const errMsg = extractErrorMessage(err);
      if (!errMsg.includes('No face')) {
        setError(errMsg);
      }
    }
  };

  const handleSubmit = async (data: any) => {
    setError(null);
    
    const formData = new FormData();
    if (capturedImage) {
      formData.append('face_image', capturedImage, 'face.jpg');
    }
    formData.append('name', data.name || '');
    formData.append('identifier', data.identifier || '');
    formData.append('gender', data.gender || '');
    formData.append('visit_reason', data.visit_reason);
    
    if (data.vitals) {
      formData.append('systolic_bp', data.vitals.systolic || '');
      formData.append('diastolic_bp', data.vitals.diastolic || '');
      formData.append('temperature', data.vitals.temp || '');
      formData.append('o2_saturation', data.vitals.o2 || '');
      formData.append('weight', data.vitals.weight || '');
    }
    
    if (matchResult?.patient_id) {
      formData.append('existing_patient_id', matchResult.patient_id);
    }
    
    try {
      const res = await fetch(`${API_URL}/api/v1/patients/checkin`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      
      const result = await res.json();
      
      if (!res.ok) {
        throw new Error(extractErrorMessage(result));
      }
      
      setSessionToken(result.session_token || result.session_id || 'SESSION-' + Date.now());
    } catch (err: any) {
      setError(extractErrorMessage(err));
    }
  };

  if (sessionToken) {
    return (
      <div style={{ maxWidth: 600, margin: '0 auto' }}>
        <SessionSuccess sessionToken={sessionToken} />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1>Patient Intake</h1>
        <p className="text-muted">Register new patients or check in returning patients</p>
      </div>

      {error && (
        <div className="banner banner-warning" style={{ marginBottom: '1.5rem' }}>
          ⚠️ {error}
        </div>
      )}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <FaceCaptureWidget 
          onCapture={handleFaceCapture}
          matchResult={matchResult}
        />
        
        <IntakeForm 
          matchResult={matchResult}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
