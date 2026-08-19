from pydantic import BaseModel


class Shift(BaseModel): #represent each person 
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
    schedule_period: SchedulePeriod #evalutes from exisiting pydantic model 
    shifts: list[Shift]  #same stuff gets a list of shifts and evalutes using the shift pydantic model created above 
    warnings: list[str] = []


#therefore I used Pydantic for data validation because it validates the entire response structure
#including nested objects and lists
#with zero manual checking code. 
#If the Claude API returns malformed data, Pydantic catches it at the boundary
# before it ever reaches the frontend.