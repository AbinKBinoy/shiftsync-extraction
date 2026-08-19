# ShiftSync Extraction Service

Python FastAPI microservice that extracts structured shift data from photos of printed employee work schedules using Claude's Vision API.

## Architecture

This service is one half of a two-service architecture for ShiftSync, a collaborative shift management platform for frontline retail workers. The other half is a Next.js web app (separate repo) that handles the frontend, auth, database, and all user-facing features. That app calls this service when a user uploads a schedule photo.

```
┌─────────────────────┐       ┌──────────────────────────────────┐
│   Next.js (Vercel)  │       │  THIS SERVICE — Python FastAPI   │
│                     │       │  (Railway)                       │
│  React Frontend     │       │                                  │
│  API Routes ────────┼──────→│  POST /extract-schedule          │
│                     │ HTTP  │    ├── Receives image            │
│                     │       │    ├── Calls Claude Vision API   │
│                     │       │    ├── Validates with Pydantic   │
│                     │       │    └── Returns structured JSON   │
└────────┬────────────┘       └──────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Supabase           │
│  (NOT used by this  │
│   service directly) │
└─────────────────────┘
```

**Request walkthrough** — Sarah, a shift manager, uploads a schedule photo:

1. Sarah opens ShiftSync in her browser (`localhost:3000`).
2. She uploads `schedule.jpg`.
3. The browser sends the image to Next.js (`localhost:3000/api/schedules/upload`).
4. The Next.js API route forwards the image to this service (`localhost:8000/extract-schedule`).
5. FastAPI receives it at `extract_schedule_endpoint`.
6. It checks: is it an accepted image type? Is it under 10MB?
7. It calls `extract_schedule()` from `extraction.py`.
8. `extraction.py` base64-encodes the image and sends it to Claude.
9. Claude looks at the photo and returns JSON.
10. `extraction.py` parses the response and validates it with Pydantic.
11. The validated `ExtractionResult` is returned to `main.py`.
12. FastAPI serializes it to JSON and sends it back to Next.js.
13. Next.js shows the extracted schedule in a verification table.
14. Sarah fixes any mistakes and publishes the schedule.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn — web framework and ASGI server
- Pydantic — data validation and response models
- Anthropic Python SDK — Claude Vision API calls
- python-multipart — file upload handling
- python-dotenv — environment variable loading
- Deployed on Railway (free tier)

## Running Locally

```bash
# Clone the repo
git clone <this-repo-url>
cd shiftsync-extraction

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the server
uvicorn main:app --reload

# Server runs at http://localhost:8000
# Interactive API docs at http://localhost:8000/docs
```

## API Endpoints

### GET /health

Health check endpoint for monitoring and deployment verification.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response (200):**
```json
{
  "status": "ok",
  "service": "shiftsync-extraction"
}
```

### POST /extract-schedule

Receives a schedule photo and extracts shift data using Claude's Vision API.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` field containing the image
- Max file size: 10MB
- Accepted formats: `image/jpeg`, `image/png`, `image/webp`

```bash
curl -X POST http://localhost:8000/extract-schedule \
  -F "file=@schedule.jpg"
```

**Response (200):**
```json
{
  "department_name": "Computing",
  "schedule_period": {
    "start_date": "2026-01-20",
    "end_date": "2026-01-26"
  },
  "shifts": [
    {
      "employee_name": "Abin",
      "date": "2026-01-20",
      "start_time": "14:00",
      "end_time": "22:00",
      "confidence": "high"
    },
    {
      "employee_name": "Sarah",
      "date": "2026-01-20",
      "start_time": "09:00",
      "end_time": "14:00",
      "confidence": "high"
    }
  ],
  "warnings": []
}
```

**Error Response (400) — Bad input:**
```json
{
  "detail": "Invalid file type. Accepted formats: JPEG, PNG, WebP"
}
```

**Error Response (422) — Extraction failed:**
```json
{
  "detail": "Could not extract schedule data from this image. Please ensure the image shows a readable work schedule."
}
```

**Error Response (500) — API failure:**
```json
{
  "detail": "Schedule extraction service temporarily unavailable. Please try again."
}
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key used for Vision API calls |
| `ALLOWED_ORIGINS` | Yes | Comma-separated list of origins allowed by CORS (e.g. `http://localhost:3000`) |

- `.env` is for local development and is never committed to git.
- `.env.example` is committed and shows what variables are needed without real values.
- In production (Railway), these are set in the Railway dashboard under Variables.

## Deployment

Deployed on [Railway](https://railway.app):

1. Push code to GitHub.
2. Create a new project on Railway and connect the GitHub repo.
3. Railway auto-detects Python and deploys.
4. Add environment variables in the Railway dashboard:
   - `ANTHROPIC_API_KEY` = your key
   - `ALLOWED_ORIGINS` = `https://your-nextjs-app.vercel.app`
5. Note the public URL Railway gives you (e.g. `https://shiftsync-extraction-production.up.railway.app`).
6. This URL goes into the Next.js app's `EXTRACTION_SERVICE_URL` environment variable.

## Related Repos

- [shiftsync](https://github.com/your-org/shiftsync) — Next.js frontend, auth, and database (the other half of the ShiftSync system)
