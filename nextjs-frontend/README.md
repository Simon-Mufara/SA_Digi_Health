# Face Biometric Pipeline - YARA Hospital System

## API Endpoints

### Backend (FastAPI)

Base URL: `http://localhost:8000/api/v1`

#### Check Service Status
```
GET /biometric/status
```
Response:
```json
{
  "status": "available",
  "model": "Facenet512",
  "detector": "opencv",
  "threshold": 0.75
}
```

#### Capture Face Biometric
```
POST /biometric/capture
Content-Type: multipart/form-data

Form fields:
- face_image: File (required, JPEG/PNG, <5MB)
- patient_id: string (optional)
- use_webcam: boolean (optional)
```

Success Response (200):
```json
{
  "success": true,
  "patient_id": "uuid-here",
  "embedding_id": "123",
  "image_hash": "sha256-hash",
  "model": "Facenet512",
  "captured_at": "2026-03-31T03:00:00",
  "message": "Face biometric captured successfully"
}
```

Error Responses (422):
```json
{
  "error": "no_face_detected",
  "message": "No face found in image. Please retake with better lighting."
}
```
```json
{
  "error": "multiple_faces",
  "message": "Multiple faces detected. Please ensure only one face is in frame."
}
```

#### Identify Patient by Face
```
POST /biometric/identify
Content-Type: multipart/form-data

Form fields:
- face_image: File (required, JPEG/PNG, <5MB)
```

Success Response (200):
```json
{
  "match": "patient-uuid",
  "patient_id": "patient-uuid",
  "confidence": 0.89,
  "name": "John Doe"
}
```

No Match Response (200):
```json
{
  "match": null,
  "patient_id": null,
  "confidence": 0.45,
  "name": null
}
```

## Frontend Usage (Next.js)

### Installation
```bash
cd nextjs-frontend
npm install
```

### Using the FaceCapture Component

```tsx
import FaceCapture from '@/components/FaceCapture';

// Capture mode - enroll a new face
<FaceCapture
  mode="capture"
  patientId="optional-patient-uuid"
  onCapture={(response) => {
    console.log('Captured:', response);
  }}
  onError={(error) => {
    console.error('Error:', error.error, error.message);
  }}
/>

// Identify mode - match against existing faces
<FaceCapture
  mode="identify"
  onIdentify={(response) => {
    if (response.match) {
      console.log('Matched patient:', response.name, response.confidence);
    } else {
      console.log('No match found');
    }
  }}
  onError={(error) => {
    console.error('Error:', error.error, error.message);
  }}
/>
```

### Component States
- `idle` - Ready to start
- `requesting-permission` - Asking for camera access
- `streaming` - Camera feed active
- `capturing` - Taking snapshot
- `processing` - Sending to API
- `success` - Operation completed
- `error` - Something went wrong

### Error Handling
The component handles these error types:
- `camera_permission_denied` - User denied camera access
- `black_frame` - Camera feed is black/unavailable
- `no_face_detected` - No face in image (triggers shake animation)
- `multiple_faces` - More than one face detected
- `invalid_file_type` - Not JPEG/PNG
- `file_too_large` - Exceeds 5MB
- `network_error` - Cannot reach backend

## Running the System

1. Start FastAPI backend:
```bash
cd fastapi_backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

2. Start Next.js frontend:
```bash
cd nextjs-frontend
npm run dev
```

3. Access:
- Backend API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
