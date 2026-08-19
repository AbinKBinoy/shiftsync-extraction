# shiftsync-extraction
Python FastAPI microservice for extracting employee schedules from photos using Claude Vision API


## current progress

1. Sarah opens ShiftSync in her browser (localhost:3000)
2. She uploads schedule.jpg
3. Browser sends the image to Next.js (localhost:3000/api/schedules/upload)
4. Next.js API route forwards the image to Python (localhost:8000/extract-schedule)
5. FastAPI receives it at the extract_schedule_endpoint function
6. Checks: is it an image? ✓  Under 10MB? ✓
7. Calls extract_schedule() from extraction.py
8. extraction.py base64 encodes it, sends to Claude
9. Claude looks at the photo, returns JSON
10. extraction.py parses and validates with Pydantic
11. Returns ExtractionResult back to main.py
12. FastAPI converts it to JSON and sends it back to Next.js
13. Next.js shows the extracted schedule in the verification table
14. Sarah fixes any mistakes and publishes

