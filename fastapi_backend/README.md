# FastAPI Privacy-First Clinical Intelligence Backend

## New capabilities
- LLM-based concise clinical summaries from structured patient data (visits, diagnoses, medications)
- Doctor dashboard React UI with face-scan flow, visit timeline, AI summary, and high-risk alerts
- Security gate React UI with webcam/file capture flow, optional demographics, and session creation only

## Backend AI clinical summary
Service:
- `app/services/llm_clinical_summary_service.py`

Current mode:
- `LLM_PROVIDER=mock` (deterministic local summarization path)

Structured inputs used:
- Diagnoses
- Medications
- Recent visit statuses
- Derived risk factors

Output:
- Concise clinical summary text in `smart_profile.ai_summary`

## Backend endpoints for face scan flows
- Doctor:
  - `POST /api/v1/face-recognition/doctor-profile-from-image`
- Security gate:
  - `POST /api/v1/face-recognition/gate-scan-image`

## Frontend apps
- Doctor Dashboard: `frontend/doctor-dashboard`
- Security Gate UI: `frontend/security-gate`

### Doctor dashboard features
- Upload face scan image (doctor role)
- Load patient profile from scan
- Display timeline
- Display AI summary and risk factors
- Alert panel for high-risk indicators

### Security gate features
- Capture/upload face image
- Optional demographics (`optional_name`, `optional_identifier`, `gender`)
- Create patient visit session
- Displays only session outcome (no patient history)

## Run backend
```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Run doctor dashboard
```bash
cd frontend/doctor-dashboard
npm install
npm run dev
```

## Run security gate UI
```bash
cd frontend/security-gate
npm install
npm run dev
```

## Security note
- Field-level AES-GCM encryption is active for sensitive patient identifiers
- Use secure secret manager-backed env injection for encryption keys