<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0B1220,100:1a2942&height=180&section=header&text=ShiftSync%20Extraction&fontSize=46&fontColor=FFD100&animation=fadeIn&fontAlignY=40&desc=The%20AI%20service%20that%20reads%20a%20schedule%20photo%20and%20turns%20it%20into%20structured%20shift%20data&descAlignY=62&descSize=14&descColor=E6E8EE" alt="ShiftSync Extraction banner"/>

<br>

[![Powers ShiftSync](https://img.shields.io/badge/Powers-ShiftSync-FFD100?style=for-the-badge&logo=vercel&logoColor=0B1220)](https://shiftsync.win)
[![Deployed on Railway](https://img.shields.io/badge/Deployed-Railway-0B1220?style=for-the-badge&logo=railway&logoColor=FFD100)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-0B1220?style=for-the-badge)](#license)

<br>

<img src="https://readme-typing-svg.demolab.com/?font=Inter&size=22&duration=2800&pause=1200&color=FFD100&center=true&vCenter=true&width=680&lines=A+photo+of+a+schedule+goes+in.;Claude+Vision+reads+every+shift.;Structured+JSON+comes+out." alt="Typing SVG" />

</div>

<br>

## What is this?

This is the AI extraction engine behind [**ShiftSync**](https://github.com/AbinKBinoy/shiftsync), a shift-scheduling app that turns a photo of a posted work schedule into a shared team calendar. This service is the piece that does the hard part: taking a raw photo of a whiteboard, a printout, or a screenshot of a scheduling system, and turning it into clean, structured shift data, employee names, dates, and start/end times, without anyone retyping a thing.

It's a standalone FastAPI service, deployed independently of the main app, and callable by any client over HTTP.

<br>

<div align="center">

## How it works

</div>

<table>
<tr>
<td width="33%" align="center">

**1. Receive**

A client POSTs an image of a posted schedule to <code>/extract-schedule</code>.

</td>
<td width="33%" align="center">

**2. Read**

Claude's Vision API reads the image, identifying every employee, date, and shift time on the page.

</td>
<td width="33%" align="center">

**3. Return**

The service returns clean, structured JSON, ready to be published straight to a calendar.

</td>
</tr>
</table>

<br>

## API

### `POST /extract-schedule`

Accepts an image file (schedule photo) as `multipart/form-data`.

**Request**

```bash
curl -X POST https://shiftsync-extraction-production.up.railway.app/extract-schedule \
  -F "file=@schedule.jpg"
```

**Response**

```json
{
  "shifts": [
    {
      "employee_name": "Jansen C.",
      "date": "2026-09-16",
      "start_time": "09:45",
      "end_time": "18:00"
    },
    {
      "employee_name": "Antonio L.",
      "date": "2026-09-16",
      "start_time": "10:00",
      "end_time": "18:00"
    }
  ],
  "warnings": []
}
```

Any ambiguity the model runs into (a smudged time, an unclear name) is surfaced in `warnings`, rather than silently guessed.

<br>

<div align="center">

## Built with

<img src="https://skillicons.dev/icons?i=python,fastapi,railway&theme=dark" />

</div>

<br>

## Why a separate service?

Reading an image with a vision model is slow and resource-heavy compared to the rest of a typical web request. Keeping this isolated from [ShiftSync's](https://github.com/AbinKBinoy/shiftsync) main Next.js app means the extraction workload never blocks or slows down the interactive parts of the product, the calendar, the swap flow, none of it waits on this. It also means this service could power a completely different frontend in the future without any changes here.

<br>

## Getting started locally

### Prerequisites
- Python 3.11+
- An Anthropic API key

### Setup

```bash
git clone https://github.com/AbinKBinoy/shiftsync-extraction.git
cd shiftsync-extraction
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

```
ANTHROPIC_API_KEY=
```

Run it:

```bash
uvicorn main:app --reload
```

The service will be live at `http://localhost:8000`, with interactive API docs at `http://localhost:8000/docs`.

<br>

## Tested against

Real, posted retail schedules, printed reports, whiteboard photos, and phone screenshots, not synthetic test data. See [ShiftSync](https://github.com/AbinKBinoy/shiftsync) for the full product this powers.

<br>

<div align="center">

## Author

**Abin Kuzhuvelikalam Binoy**

[![GitHub](https://img.shields.io/badge/GitHub-AbinKBinoy-0B1220?style=for-the-badge&logo=github)](https://github.com/AbinKBinoy)

<br>

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:1a2942,100:0B1220&height=100&section=footer" alt="footer"/>

</div>