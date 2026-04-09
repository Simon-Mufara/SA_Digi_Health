import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";
const API_FALLBACK = "http://127.0.0.1:8000/api/v1";

export function App() {
  const [token, setToken] = useState("");
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [profile, setProfile] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const highRisk = useMemo(() => (profile?.alerts?.length ?? 0) > 0, [profile]);
  const timelineCount = timeline.length;

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  const onFileSelect = (file) => {
    setImage(file);
    setSuccess("");
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(file ? URL.createObjectURL(file) : "");
  };

  const onScan = async () => {
    if (!image) {
      setError("Select a face image first.");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const form = new FormData();
      form.append("image", image);

      const endpoint = "/face-recognition/doctor-profile-from-image";
      const doRequest = async (baseUrl) =>
        fetch(`${baseUrl}${endpoint}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: form,
        });

      let scanResp;
      try {
        scanResp = await doRequest(API_BASE);
      } catch {
        scanResp = await doRequest(API_FALLBACK);
      }

      if (!scanResp.ok) {
        const payload = await scanResp.json().catch(() => ({}));
        if (scanResp.status === 401) {
          throw new Error("Unauthorized. Please paste a valid Doctor JWT token.");
        }
        throw new Error(payload.detail || `Face scan failed (HTTP ${scanResp.status})`);
      }

      const resolvedProfile = await scanResp.json();
      setProfile(resolvedProfile);

      let timelineResp;
      try {
        timelineResp = await fetch(`${API_BASE}/patients/${resolvedProfile.patient_uuid}/timeline`, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        timelineResp = await fetch(`${API_FALLBACK}/patients/${resolvedProfile.patient_uuid}/timeline`, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }

      if (!timelineResp.ok) {
        const payload = await timelineResp.json().catch(() => ({}));
        throw new Error(payload.detail || `Could not load visit timeline (HTTP ${timelineResp.status})`);
      }

      setTimeline(await timelineResp.json());
      setSuccess("Patient context loaded successfully.");
    } catch (e) {
      const networkLikeError = String(e?.message || "").toLowerCase().includes("fetch");
      if (networkLikeError) {
        setError("Cannot reach backend API. Ensure FastAPI is running on localhost:8000.");
      } else {
        setError(e.message);
      }
      setProfile(null);
      setTimeline([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <h1>Doctor Dashboard</h1>
        <p>Face-based patient context viewer with AI clinical summary and visit timeline.</p>
      </header>

      <section className="card">
        <h2>Scan Controls</h2>
        <label htmlFor="token">Doctor JWT</label>
        <input id="token" value={token} onChange={(e) => setToken(e.target.value)} placeholder="Paste doctor JWT token" />

        <label htmlFor="face-image">Face scan image</label>
        <input id="face-image" type="file" accept="image/*" onChange={(e) => onFileSelect(e.target.files?.[0] ?? null)} />
        {previewUrl ? <img src={previewUrl} alt="Face preview" className="photo-preview" /> : null}
        <button onClick={onScan} disabled={loading}>{loading ? "Scanning..." : "Scan & Load Patient"}</button>
      </section>

      {error ? <p className="error">{error}</p> : null}
      {success ? <p className="success-text">{success}</p> : null}

      {profile ? (
        <>
          <section className="card">
            <h2>Patient Context</h2>
            <div className="stats-grid">
              <p><strong>Patient UUID</strong><br />{profile.patient_uuid}</p>
              <p><strong>Name</strong><br />{profile.display_name ?? "Unknown"}</p>
              <p><strong>Identifier</strong><br />{profile.masked_identifier ?? "N/A"}</p>
              <p><strong>Gender</strong><br />{profile.gender ?? "N/A"}</p>
              <p><strong>Total Visits</strong><br />{profile.visit_count ?? 0}</p>
              <p><strong>Last Visit</strong><br />{profile.last_visit_at ? new Date(profile.last_visit_at).toLocaleString() : "N/A"}</p>
            </div>
            <p><strong>AI Summary:</strong> {profile.ai_summary}</p>
            <p><strong>Risk Factors:</strong> {(profile.risk_factors ?? []).join(", ") || "None"}</p>
          </section>

          <section className={`card ${highRisk ? "high-risk" : ""}`}>
            <h2>Risk Alerts {highRisk ? "(High Risk)" : ""}</h2>
            {(profile.alerts ?? []).length === 0 ? <p>No active alerts.</p> : (
              <ul>{profile.alerts.map((alert) => <li key={alert}>{alert}</li>)}</ul>
            )}
          </section>

          <section className="card">
            <h2>Visit Timeline</h2>
            <p className="hint">{timelineCount} visit{timelineCount === 1 ? "" : "s"} found</p>
            {timeline.length === 0 ? <p>No visits found.</p> : (
              <ul className="timeline-list">
                {timeline.map((visit) => (
                  <li key={visit.visit_session_id}>
                    <strong>{visit.status}</strong> - {new Date(visit.entry_time).toLocaleString()}
                    <br />
                    {visit.reason ?? "No reason provided"}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
