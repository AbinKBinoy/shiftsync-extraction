import logging
import os
import traceback

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from extraction import ExtractionError, extract_schedule
from models import ExtractionResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shiftsync-extraction")

load_dotenv()

app = FastAPI(title="ShiftSync Extraction Service")

ACCEPTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "shiftsync-extraction"}


@app.post("/extract-schedule", response_model=ExtractionResult)
async def extract_schedule_endpoint(file: UploadFile):
    if file.content_type not in ACCEPTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Accepted formats: JPEG, PNG, WebP",
        )

    image_bytes = await file.read()

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    try:
        return extract_schedule(image_bytes, file.filename)
    except ExtractionError:
        traceback.print_exc()
        raise HTTPException(
            status_code=422,
            detail="Could not extract schedule data from this image. Please ensure the image shows a readable work schedule.",
        )
    except anthropic.APIError:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Schedule extraction service temporarily unavailable. Please try again.",
        )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
