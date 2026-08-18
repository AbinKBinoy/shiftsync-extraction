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
