# ShiftSync Extraction Service

## Project Overview

This is a Python FastAPI microservice — one half of a two-service architecture for ShiftSync, a collaborative shift management platform for frontline retail workers. This service does one job: receive a photo of a printed employee work schedule, send it to Claude's Vision API, parse the response, validate it with Pydantic, and return clean structured JSON.

The other half is a Next.js web app (separate repo: shiftsync) that handles the frontend, auth, database, and all user-facing features. That app calls this service when a user uploads a schedule photo.

## Architecture Context

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

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn (web framework + ASGI server)
- Pydantic (data validation and response models)
- Anthropic Python SDK (Claude Vision API calls)
- python-multipart (file upload handling)
- python-dotenv (environment variable loading)
- Deployed on Railway (free tier)

## File Structure

```
shiftsync-extraction/
├── CLAUDE.md               # This file — project context for Claude Code
├── main.py                 # FastAPI app, endpoints, CORS config
├── extraction.py           # Claude Vision API call + response parsing
├── models.py               # Pydantic models for request/response validation
├── requirements.txt        # Python dependencies
├── .env                    # ANTHROPIC_API_KEY (NEVER committed to git)
├── .env.example            # Template showing required env vars
├── .gitignore              # Ignores .env, __pycache__, .venv, etc.
└── README.md               # Project description, setup, API docs
```

## Dependencies (requirements.txt)

```
fastapi
uvicorn[standard]
anthropic
python-multipart
pydantic
python-dotenv
```

## Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...        # Required — Claude API key
ALLOWED_ORIGINS=http://localhost:3000 # Required — CORS origins (comma-separated)
```

- .env is for local development, NEVER committed to git
- .env.example is committed, shows what variables are needed without real values
- In production (Railway), these are set in the Railway dashboard under Variables

## API Endpoints

### GET /health
Health check endpoint for monitoring and deployment verification.

**Response (200):**
```json
{
  "status": "ok",
  "service": "shiftsync-extraction"
}
```

### POST /extract-schedule
Main endpoint. Receives a schedule photo, extracts shift data using Claude Vision API.

**Request:**
- Content-Type: multipart/form-data
- Body: file field containing image (JPEG, PNG)
- Max file size: 10MB
- Accepted formats: image/jpeg, image/png, image/webp

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

## Pydantic Models (models.py)

```python
from pydantic import BaseModel

class Shift(BaseModel):
    employee_name: str
    date: str                       # YYYY-MM-DD
    start_time: str                 # HH:MM (24-hour format)
    end_time: str                   # HH:MM (24-hour format)
    confidence: str = "high"        # "high" | "low"
    raw_date: str | None = None     # Original date text if date couldn't be parsed

class SchedulePeriod(BaseModel):
    start_date: str                 # YYYY-MM-DD
    end_date: str                   # YYYY-MM-DD

class ExtractionResult(BaseModel):
    department_name: str | None
    schedule_period: SchedulePeriod
    shifts: list[Shift]
    warnings: list[str] = []
```

## Claude Vision API — Prompt Strategy (extraction.py)

The system prompt sent to Claude's Vision API:

```
You are a work schedule extraction system. You will receive a photo of
a printed employee schedule. Extract ALL shifts into structured JSON.

The schedule may be in any format:
- Names in rows, dates in columns
- Names in columns, dates in rows
- A department name may appear as a header
- Times may be in 12h or 24h format
- Some cells may be empty (day off)
- Handwritten edits may appear over printed text

Return ONLY valid JSON in this exact format — no markdown, no backticks,
no explanation, just the JSON object:
{
  "department_name": "string or null",
  "schedule_period": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  },
  "shifts": [
    {
      "employee_name": "string",
      "date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "confidence": "high or low"
    }
  ]
}

Rules:
- Convert all times to 24-hour format (e.g., 2:00 PM → 14:00)
- If you cannot determine a specific date, include the raw column/row
  header in a "raw_date" field for that shift
- If a time is ambiguous or hard to read, set confidence to "low"
- Skip empty cells (days off) — do not create shift entries for them
- If you can identify the department name from a header, include it
- If you cannot determine the year, assume the current year
```

**Implementation notes for extraction.py:**
- Use the `anthropic` Python SDK, not raw HTTP requests
- Send the image as base64-encoded data in the message content
- Use the `claude-sonnet-4-6` model (good enough for vision, cheaper than Opus)
- Set max_tokens to 4096 (schedules can have many shifts)
- Parse the response text as JSON
- Validate against Pydantic ExtractionResult model
- If JSON parsing fails, try to extract JSON from markdown code blocks (Claude sometimes wraps in ```json```)
- If Pydantic validation fails, return a clear error — don't send malformed data to the frontend

## Error Handling Requirements

1. **Invalid file type:** Check MIME type before processing. Return 400 with clear message.
2. **File too large:** Reject files over 10MB. Return 400.
3. **Claude API failure:** Catch anthropic.APIError. Return 500 with generic message (don't expose API details).
4. **Claude returns non-JSON:** Try to extract JSON from response. If still fails, return 422.
5. **Pydantic validation fails:** Claude returned JSON but wrong structure. Return 422 with details about what's wrong.
6. **Empty extraction:** Claude returns valid JSON but 0 shifts. Return 200 with empty shifts array and a warning: "No shifts detected in this image."

## CORS Configuration

The FastAPI app must allow cross-origin requests from the Next.js frontend.

```python
from fastapi.middleware.cors import CORSMiddleware

# Origins loaded from ALLOWED_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # ["http://localhost:3000"] for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the server
uvicorn main:app --reload

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs (auto-generated by FastAPI)
```

## Testing with Postman

1. Open Postman
2. Create a POST request to http://localhost:8000/extract-schedule
3. In Body tab, select "form-data"
4. Add key "file", change type dropdown to "File", select a schedule photo
5. Hit Send
6. Check the JSON response

## Deployment (Railway)

1. Push code to GitHub
2. Create a new project on Railway, connect the GitHub repo
3. Railway auto-detects Python and deploys
4. Add environment variables in Railway dashboard:
   - ANTHROPIC_API_KEY = your key
   - ALLOWED_ORIGINS = https://your-nextjs-app.vercel.app
5. Note the public URL Railway gives you (e.g., https://shiftsync-extraction-production.up.railway.app)
6. This URL goes into the Next.js app's EXTRACTION_SERVICE_URL env var

## Build Progress

- [ ] Project setup (requirements.txt, .gitignore, .env.example)
- [ ] main.py with FastAPI app and GET /health endpoint
- [ ] models.py with Pydantic models (Shift, SchedulePeriod, ExtractionResult)
- [ ] extraction.py with Claude Vision API call and response parsing
- [ ] POST /extract-schedule endpoint in main.py
- [ ] Input validation (file type check, file size limit)
- [ ] Error handling (API failures, malformed responses, empty extractions)
- [ ] CORS middleware configuration
- [ ] Confidence scoring for ambiguous extractions
- [ ] Test with multiple schedule formats
- [ ] Deploy to Railway
- [ ] README.md with setup instructions and API documentation

## Commit Messages to Use

```
feat: FastAPI project setup with health check endpoint
feat: add Pydantic models for schedule extraction
feat: Claude Vision API integration for schedule extraction
feat: POST /extract-schedule endpoint with file upload
feat: input validation for file type and size
feat: error handling for API failures and malformed responses
feat: CORS middleware configuration
test: verify extraction with multiple schedule formats
deploy: Railway deployment with environment config
docs: add README with API documentation and setup guide
```
