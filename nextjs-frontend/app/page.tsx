'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { extractErrorMessage } from '@/lib/errors';

type Mode = 'select' | 'patient_intake' | 'staff_login';
type UserRole = 'doctor' | 'clinician' | 'admin' | 'security_officer' | 'researcher';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

const rolePaths: Record<UserRole, string> = {
  doctor: '/dashboard/doctor',
  clinician: '/dashboard/clinician',
  admin: '/dashboard/admin',
  security_officer: '/dashboard/security',
  researcher: '/dashboard/research',
};

// SA ID validation
function validateSAID(id: string): { valid: boolean; age?: number; gender?: string; error?: string } {
  if (!/^\d{13}$/.test(id)) {
    return { valid: false, error: 'ID must be 13 digits' };
  }
  
  const year = parseInt(id.substring(0, 2));
  const month = parseInt(id.substring(2, 4));
  const day = parseInt(id.substring(4, 6));
  const genderCode = parseInt(id.substring(6, 10));
  
  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return { valid: false, error: 'Invalid date in ID' };
  }
  
  const fullYear = year >= 0 && year <= 30 ? 2000 + year : 1900 + year;
  const birthDate = new Date(fullYear, month - 1, day);
  const age = Math.floor((Date.now() - birthDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000));
  const gender = genderCode >= 5000 ? 'Male' : 'Female';
  
  return { valid: true, age, gender };
}

export default function EntryPage() {
  const router = useRouter();
  const [isMobile, setIsMobile] = useState(false);
  const [mode, setMode] = useState<Mode>('select');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Patient intake state
  const [capturedImage, setCapturedImage] = useState<Blob | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  // Staff login state
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [staffId, setStaffId] = useState('');
  const [password, setPassword] = useState('');
  
  const canUseCamera = () => {
    if (typeof window === 'undefined') return false;
    if (!window.isSecureContext) return false;
    return Boolean(navigator.mediaDevices?.getUserMedia);
  };

  const resolveCameraError = (err: unknown) => {
    const e = err as { name?: string; message?: string };
    if (e?.name === 'NotAllowedError') {
      return 'Camera access denied. Allow permission in browser site settings.';
    }
    if (e?.name === 'NotReadableError' || e?.name === 'TrackStartError') {
      return 'Camera is already in use by another app. Close Zoom/Teams/Camera app and retry.';
    }
    if (e?.name === 'NotFoundError' || e?.name === 'DevicesNotFoundError') {
      return 'No camera device was found. Connect a webcam or use Upload Photo.';
    }
    if (e?.name === 'OverconstrainedError') {
      return 'Camera exists but does not support preferred settings. Retrying with fallback settings.';
    }
    return `Camera failed to start. ${e?.message || 'Use Upload Photo while retrying.'}`;
  };

  const attachStreamToVideo = async () => {
    if (!videoRef.current || !streamRef.current) return;
    videoRef.current.srcObject = streamRef.current;
    videoRef.current.muted = true;
    await videoRef.current.play().catch(() => null);
  };

  // Start camera
  const startCamera = async () => {
    if (!canUseCamera()) {
      setError('Camera requires secure context and browser support. Use http://127.0.0.1:3100.');
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
    try {
      for (const constraints of attempts) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          streamRef.current = stream;
          setCameraActive(true);
          setError(null);
          await attachStreamToVideo();
          return;
        } catch (attemptError) {
          lastError = attemptError;
        }
      }
      setError(resolveCameraError(lastError));
      setCameraActive(false);
    } catch (err: unknown) {
      setError(resolveCameraError(err));
      setCameraActive(false);
    }
  };
  
  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    if (!cameraActive) return;
    void attachStreamToVideo();
  }, [cameraActive]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const onResize = () => setIsMobile(window.innerWidth <= 768);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  
  // Capture photo
  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video.videoWidth || !video.videoHeight) {
        setError('Camera stream is not ready. Please wait a moment and retry.');
        return;
      }
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
          if (blob) {
            setCapturedImage(blob);
            setImagePreview(URL.createObjectURL(blob));
            stopCamera();
          }
        }, 'image/jpeg', 0.8);
      }
    }
  };
  
  // File upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please upload an image file');
        return;
      }
      setCapturedImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };
  
  // Patient intake submission
  const handlePatientIntake = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const name = formData.get('name') as string;
    const identifier = formData.get('identifier') as string;
    const gender = formData.get('gender') as string;
    const visitReason = formData.get('visit_reason') as string;
    
    // Validate SA ID
    if (identifier) {
      const validation = validateSAID(identifier);
      if (!validation.valid) {
        setError(validation.error || 'Invalid SA ID');
        setLoading(false);
        return;
      }
    }
    
    // Build request
    const requestData = new FormData();
    if (capturedImage) {
      requestData.append('face_image', capturedImage, 'face.jpg');
    }
    requestData.append('name', name || '');
    requestData.append('identifier', identifier || '');
    requestData.append('gender', gender || '');
    requestData.append('visit_reason', visitReason);
    
    try {
      const res = await fetch(`${API_URL}/api/v1/patients/checkin`, {
        method: 'POST',
        body: requestData,
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(extractErrorMessage(data));
      }
      
      // Success - show session token
      setSuccess(`Session created: ${data.session_token || data.session_id}`);
      
      // Reset form after 3 seconds
      setTimeout(() => {
        setMode('select');
        setSuccess(null);
        setCapturedImage(null);
        setImagePreview(null);
      }, 3000);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };
  
  // Staff login submission
  const handleStaffLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRole || !staffId || !password) return;
    
    setLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', staffId);
      formData.append('password', password);
      formData.append('scope', selectedRole);

      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        credentials: 'include',
        body: formData.toString(),
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 403 && data.error === 'role_mismatch') {
          setError('This account is not authorised for the selected role.');
        } else if (res.status === 401) {
          setError('Invalid credentials. Please check your staff ID and password.');
        } else {
          setError(extractErrorMessage(data));
        }
        setLoading(false);
        return;
      }

      // Store tokens
      document.cookie = `access_token=${data.access_token}; path=/; max-age=3600; SameSite=Lax`;
      document.cookie = `refresh_token=${data.refresh_token}; path=/; max-age=86400; SameSite=Lax`;
      
      // Redirect
      router.push(rolePaths[selectedRole]);
    } catch (err) {
      setError('Cannot reach the server. Please check your connection.');
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0f1e',
      color: '#e5e7eb',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: isMobile ? '1rem' : '2rem',
    }}>
      <div style={{ width: '100%', maxWidth: isMobile ? '100%' : (mode === 'select' ? 700 : 500) }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: isMobile ? '1.25rem' : '2rem' }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: 'linear-gradient(135deg, #00b4a0, #0077b6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            fontWeight: 700,
            color: '#0a0f1e',
            margin: '0 auto 1rem',
          }}>
            Y
          </div>
          <h1 style={{ fontSize: isMobile ? '1.3rem' : '1.75rem', marginBottom: '0.5rem', color: '#fff' }}>South African DigiHealth</h1>
          <p style={{ color: '#9ca3af' }}>Biometric Health System</p>
        </div>

        {/* Mode Selection */}
        {mode === 'select' && (
          <div>
            <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', fontWeight: 400, color: '#d1d5db' }}>
              Welcome. How would you like to proceed?
            </h2>
            
            <div style={{ display: 'grid', gap: isMobile ? '0.75rem' : '1rem' }}>
              <button
                onClick={() => setMode('patient_intake')}
                style={{
                  background: '#1a2332',
                  border: '2px solid #00b4a0',
                  borderRadius: 12,
                  padding: isMobile ? '1rem' : '2rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  color: '#fff',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(0, 180, 160, 0.1)'}
                onMouseOut={(e) => e.currentTarget.style.background = '#1a2332'}
              >
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}></div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Patient Check-In</h3>
                <p style={{ color: '#9ca3af', margin: 0 }}>
                  New or returning patient? Register and create a session for consultation.
                </p>
              </button>
              
              <button
                onClick={() => setMode('staff_login')}
                style={{
                  background: '#1a2332',
                  border: '2px solid #6366f1',
                  borderRadius: 12,
                  padding: isMobile ? '1rem' : '2rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  color: '#fff',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'}
                onMouseOut={(e) => e.currentTarget.style.background = '#1a2332'}
              >
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}></div>
                <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>Staff Login</h3>
                <p style={{ color: '#9ca3af', margin: 0 }}>
                  Doctor, clinician, admin, security, or researcher access.
                </p>
              </button>
            </div>
          </div>
        )}

        {/* Patient Intake Form */}
        {mode === 'patient_intake' && (
          <div>
            <button
              onClick={() => setMode('select')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#00b4a0',
                cursor: 'pointer',
                marginBottom: '1rem',
                fontSize: '0.9rem',
              }}
            >
              ← Back to options
            </button>
            
            <h2 style={{ marginBottom: '0.5rem', color: '#fff' }}>Security Gate</h2>
            <p style={{ color: '#9ca3af', marginBottom: '1.5rem' }}>
              Fast and secure first-contact intake. Capture details to create a patient session.
            </p>
            
            {error && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid #ef4444',
                borderRadius: 8,
                padding: '1rem',
                marginBottom: '1rem',
                color: '#fca5a5',
              }}>
                Alert: {error}
              </div>
            )}
            
            {success && (
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid #10b981',
                borderRadius: 8,
                padding: '1rem',
                marginBottom: '1rem',
                color: '#6ee7b7',
              }}>
                Success: {success}
              </div>
            )}
            
            <form onSubmit={handlePatientIntake}>
              {/* Face Capture Section */}
              <div style={{
                background: '#1a2332',
                border: '1px solid #374151',
                borderRadius: 8,
                padding: '1.5rem',
                marginBottom: '1.5rem',
              }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#d1d5db' }}>
                  Biometric Face Capture (Optional)
                </h3>
                
                {!imagePreview && !cameraActive && (
                  <div>
                    <button
                      type="button"
                      onClick={startCamera}
                      style={{
                        background: '#00b4a0',
                        color: '#0a0f1e',
                        border: 'none',
                        borderRadius: 6,
                        padding: '0.75rem 1.5rem',
                        cursor: 'pointer',
                        fontWeight: 600,
                        marginBottom: '1rem',
                        width: '100%',
                      }}
                    >
                      Start / Retry Camera
                    </button>
                    
                    <div style={{ textAlign: 'center', margin: '1rem 0', color: '#6b7280' }}>
                      — OR —
                    </div>
                    
                    <label style={{
                      display: 'block',
                      background: '#374151',
                      color: '#d1d5db',
                      borderRadius: 6,
                      padding: '0.75rem',
                      cursor: 'pointer',
                      textAlign: 'center',
                    }}>
                      Upload Photo
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        style={{ display: 'none' }}
                      />
                    </label>
                  </div>
                )}
                
                {cameraActive && (
                  <div>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      style={{
                        width: '100%',
                        borderRadius: 8,
                        marginBottom: '1rem',
                        background: '#000',
                      }}
                    />
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        type="button"
                        onClick={capturePhoto}
                        style={{
                          flex: 1,
                          background: '#00b4a0',
                          color: '#0a0f1e',
                          border: 'none',
                          borderRadius: 6,
                          padding: '0.75rem',
                          cursor: 'pointer',
                          fontWeight: 600,
                        }}
                      >
                        Capture
                      </button>
                      <button
                        type="button"
                        onClick={stopCamera}
                        style={{
                          flex: 1,
                          background: '#ef4444',
                          color: '#fff',
                          border: 'none',
                          borderRadius: 6,
                          padding: '0.75rem',
                          cursor: 'pointer',
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
                
                {imagePreview && (
                  <div>
                    <img
                      src={imagePreview}
                      alt="Captured"
                      style={{
                        width: '100%',
                        borderRadius: 8,
                        marginBottom: '1rem',
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        setCapturedImage(null);
                        setImagePreview(null);
                      }}
                      style={{
                        background: '#6b7280',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 6,
                        padding: '0.5rem 1rem',
                        cursor: 'pointer',
                        width: '100%',
                      }}
                    >
                      Retake Photo
                    </button>
                  </div>
                )}
                
                <canvas ref={canvasRef} style={{ display: 'none' }} />
              </div>
              
              {/* Patient Details */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#d1d5db' }}>
                  Name (Optional)
                </label>
                <input
                  type="text"
                  name="name"
                  placeholder="Patient full name"
                  style={{
                    width: '100%',
                    background: '#1a2332',
                    border: '1px solid #374151',
                    borderRadius: 6,
                    padding: '0.75rem',
                    color: '#fff',
                    fontSize: '1rem',
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#d1d5db' }}>
                  South African ID (Optional)
                </label>
                <input
                  type="text"
                  name="identifier"
                  placeholder="13 digits"
                  maxLength={13}
                  style={{
                    width: '100%',
                    background: '#1a2332',
                    border: '1px solid #374151',
                    borderRadius: 6,
                    padding: '0.75rem',
                    color: '#fff',
                    fontSize: '1rem',
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#d1d5db' }}>
                  Gender (Optional)
                </label>
                <select
                  name="gender"
                  style={{
                    width: '100%',
                    background: '#1a2332',
                    border: '1px solid #374151',
                    borderRadius: 6,
                    padding: '0.75rem',
                    color: '#fff',
                    fontSize: '1rem',
                  }}
                >
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#d1d5db' }}>
                  Visit Reason <span style={{ color: '#ef4444' }}>*</span>
                </label>
                <input
                  type="text"
                  name="visit_reason"
                  placeholder="e.g. consultation, follow-up"
                  required
                  style={{
                    width: '100%',
                    background: '#1a2332',
                    border: '1px solid #374151',
                    borderRadius: 6,
                    padding: '0.75rem',
                    color: '#fff',
                    fontSize: '1rem',
                  }}
                />
              </div>
              
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%',
                  background: loading ? '#6b7280' : '#00b4a0',
                  color: '#0a0f1e',
                  border: 'none',
                  borderRadius: 6,
                  padding: '1rem',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                }}
              >
                {loading ? 'Creating Session...' : 'Create Patient Session'}
              </button>
            </form>
          </div>
        )}

        {/* Staff Login */}
        {mode === 'staff_login' && (
          <div>
            <button
              onClick={() => {
                setMode('select');
                setSelectedRole(null);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#6366f1',
                cursor: 'pointer',
                marginBottom: '1rem',
                fontSize: '0.9rem',
              }}
            >
              ← Back to options
            </button>
            
            {!selectedRole ? (
              <>
                <h2 style={{ marginBottom: '1.5rem', textAlign: 'center', color: '#fff' }}>
                  Select Your Role
                </h2>
                <div style={{ display: 'grid', gap: '0.75rem' }}>
                  {(['doctor', 'clinician', 'admin', 'security_officer', 'researcher'] as UserRole[]).map(role => (
                    <button
                      key={role}
                      onClick={() => setSelectedRole(role)}
                      style={{
                        background: '#1a2332',
                        border: '1px solid #374151',
                        borderRadius: 8,
                        padding: '1rem',
                        cursor: 'pointer',
                        color: '#fff',
                        textAlign: 'left',
                        fontSize: '1rem',
                      }}
                    >
                      {role === 'doctor' && ' Doctor'}
                      {role === 'clinician' && ' Clinician'}
                      {role === 'admin' && ' Admin'}
                      {role === 'security_officer' && ' Security Officer'}
                      {role === 'researcher' && ' Researcher'}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <>
                <h2 style={{ marginBottom: '0.5rem', color: '#fff' }}>
                  {selectedRole === 'doctor' && ' Doctor Login'}
                  {selectedRole === 'clinician' && ' Clinician Login'}
                  {selectedRole === 'admin' && ' Admin Login'}
                  {selectedRole === 'security_officer' && ' Security Login'}
                  {selectedRole === 'researcher' && ' Researcher Login'}
                </h2>
                <p style={{ color: '#9ca3af', marginBottom: '1.5rem' }}>
                  Enter your credentials to access the system.
                </p>
                
                {error && (
                  <div style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid #ef4444',
                    borderRadius: 8,
                    padding: '1rem',
                    marginBottom: '1rem',
                    color: '#fca5a5',
                  }}>
                    Alert: {error}
                  </div>
                )}
                
                <form onSubmit={handleStaffLogin}>
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#d1d5db' }}>
                      Staff ID
                    </label>
                    <input
                      type="text"
                      value={staffId}
                      onChange={(e) => setStaffId(e.target.value)}
                      placeholder="e.g. DR-001"
                      required
                      style={{
                        width: '100%',
                        background: '#1a2332',
                        border: '1px solid #374151',
                        borderRadius: 6,
                        padding: '0.75rem',
                        color: '#fff',
                        fontSize: '1rem',
                      }}
                    />
                  </div>
                  
                  <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#d1d5db' }}>
                      Password
                    </label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        background: '#1a2332',
                        border: '1px solid #374151',
                        borderRadius: 6,
                        padding: '0.75rem',
                        color: '#fff',
                        fontSize: '1rem',
                      }}
                    />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    style={{
                      width: '100%',
                      background: loading ? '#6b7280' : '#6366f1',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 6,
                      padding: '1rem',
                      fontSize: '1rem',
                      fontWeight: 600,
                      cursor: loading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {loading ? 'Signing in...' : 'Sign In'}
                  </button>
                  
                  <button
                    type="button"
                    onClick={() => setSelectedRole(null)}
                    style={{
                      width: '100%',
                      background: 'transparent',
                      color: '#9ca3af',
                      border: '1px solid #374151',
                      borderRadius: 6,
                      padding: '0.75rem',
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      marginTop: '0.5rem',
                    }}
                  >
                    ← Change Role
                  </button>
                </form>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


