import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";
const API_FALLBACK = "http://127.0.0.1:8000/api/v1";

export function App() {
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [name, setName] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [gender, setGender] = useState("");
  const [reason, setReason] = useState("");
  const [session, setSession] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => {
      stopCamera();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const startCamera = async () => {
    setError("");
    setSuccess("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (e) {
      setError(`Could not access camera: ${e.message}`);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const capturePhoto = () => {
    setError("");
    setSuccess("");
    if (!videoRef.current || !canvasRef.current) {
      setError("Camera is not ready.");
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setError("Could not get canvas context.");
      return;
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) {
        setError("Could not capture image.");
        return;
      }

      const file = new File([blob], "captured-face.jpg", { type: "image/jpeg" });
      setImage(file);

      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(file));
    }, "image/jpeg", 0.95);
  };

  const onFileSelect = (file) => {
    setSuccess("");
    setImage(file);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(file ? URL.createObjectURL(file) : "");
  };

  const createSession = async () => {
    if (!name.trim()) {
      setError("Name is required.");
      setSession(null);
      return;
    }

    if (!/^\d{13}$/.test(identifier.trim())) {
      setError("South African ID must be exactly 13 digits.");
      setSession(null);
      return;
    }

    if (!gender) {
      setError("Gender is required.");
      setSession(null);
      return;
    }

    if (!reason.trim()) {
      setError("Visit reason is required.");
      setSession(null);
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const form = new FormData();
      form.append("name", name.trim());
      form.append("identifier", identifier.trim());
      form.append("gender", gender);
      form.append("visit_reason", reason.trim());
      if (image) {
        form.append("face_image", image);
      }

      const endpoint = "/sessions/create";
      const doRequest = async (baseUrl) =>
        fetch(`${baseUrl}${endpoint}`, {
          method: "POST",
          body: form,
        });

      let response;
      try {
        response = await doRequest(API_BASE);
      } catch {
        response = await doRequest(API_FALLBACK);
      }

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Could not create patient session (HTTP ${response.status})`);
      }

      const payload = await response.json();
      setSession(payload);
      setSuccess(payload.warning ? "Session created with warning." : "Patient session created successfully.");
    } catch (e) {
      const networkLikeError = String(e?.message || "").toLowerCase().includes("fetch");
      if (networkLikeError) {
        setError("Cannot reach backend API. Ensure FastAPI is running on localhost:8000.");
      } else {
        setError(e.message);
      }
      setSession(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <h1>Security Gate</h1>
        <p>
          Fast and secure first-contact intake. Capture a face photo, collect key visit details,
          and create a clean patient session for clinical follow-up.
        </p>
      </header>

      <section className="card">
        <h2>Session Intake</h2>
        <p className="hint">Enter required details. Face image is optional.</p>
      </section>

      <section className="card">
        <h2>Face Capture</h2>
        <label>Camera controls</label>
        <div className="camera-row">
          {!cameraActive ? (
            <button type="button" onClick={startCamera}>Start Camera</button>
          ) : (
            <>
              <button type="button" onClick={capturePhoto}>Capture Photo</button>
              <button type="button" className="secondary" onClick={stopCamera}>Stop Camera</button>
            </>
          )}
        </div>

        <video ref={videoRef} className="camera-preview" autoPlay playsInline muted />
        <canvas ref={canvasRef} style={{ display: "none" }} />

        <label htmlFor="image-upload">Face image upload (optional)</label>
        <input id="image-upload" type="file" accept="image/*" onChange={(e) => onFileSelect(e.target.files?.[0] ?? null)} />

        {previewUrl ? <img src={previewUrl} alt="Captured face preview" className="photo-preview" /> : null}
      </section>

      <section className="card">
        <h2>Patient Intake Details</h2>
        <p className="hint">These fields are required for session creation.</p>

        <div className="field-grid">
          <div>
            <label htmlFor="patient-name">Name</label>
            <input id="patient-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Patient full name" />
          </div>

          <div>
            <label htmlFor="sa-id">South African ID</label>
            <input
              id="sa-id"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="South African ID (13 digits)"
              maxLength={13}
              inputMode="numeric"
            />
          </div>

          <div>
            <label htmlFor="patient-gender">Gender</label>
            <select id="patient-gender" value={gender} onChange={(e) => setGender(e.target.value)}>
              <option value="">Select</option>
              <option value="F">F</option>
              <option value="M">M</option>
              <option value="Other">Other</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>

          <div>
            <label htmlFor="reason">Visit reason</label>
            <input id="reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. consultation" />
          </div>
        </div>

        <button onClick={createSession} disabled={loading}>{loading ? "Creating..." : "Create Patient Session"}</button>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {success ? <p className="success-text">{success}</p> : null}

      {session ? (
        <section className="card success">
          <h2>Session Created</h2>
          {session.warning ? <p className="warning-text">{session.warning}</p> : null}
          <div className="stats-grid">
            <p><strong>Patient UUID:</strong><br />{session.patient_uuid}</p>
            <p><strong>Visit Session ID:</strong><br />{session.visit_session_id}</p>
            <p><strong>Result:</strong><br />{session.result}</p>
            <p><strong>Face Image:</strong><br />{session.image_received ? "Captured" : "Not provided"}</p>
          </div>
        </section>
      ) : null}
    </div>
  );
}
