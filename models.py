"""
Pydantic Data Models for TravelSaarthi - Adaptive Travel Planning Agent
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    food: Literal["veg", "non-veg", "jain", "any"] = "veg"
    pace: Literal["relaxed", "moderate", "packed"] = "relaxed"
    elders: bool = False
    children: bool = False
    hotel_tier: Literal["budget", "standard", "comfort", "premium"] = "budget"
    transport_mode: Literal["train", "bus", "cab", "flight"] = "train"


class TripRequest(BaseModel):
    origin: str = Field(default="Delhi", alias="from")
    destination: str = Field(default="Jaipur", alias="to")
    days: int = Field(default=3, ge=1, le=14)
    budget: float = Field(default=15000.0, ge=1000.0)
    people: int = Field(default=4, ge=1)
    trip_type: Literal["family", "friends", "solo", "couple", "business"] = "family"
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    class Config:
        populate_by_name = True


class Activity(BaseModel):
    id: str
    name: str
    time: str = "09:00"  # "HH:MM" format
    type: Literal["outdoor", "indoor", "heritage", "food", "shopping", "nature", "leisure"] = "outdoor"
    cost: float = 0.0  # per person or total activity entry
    duration_hr: float = 2.0
    lat: float = 26.9124
    lon: float = 75.7873
    priority: int = Field(default=3, ge=1, le=5)  # 5 = Must visit, 1 = Optional filler
    opening_time: str = "08:00"
    closing_time: str = "18:00"
    category: str = "attraction"
    family_friendly: bool = True
    elderly_friendly: bool = True
    description: str = ""
    tips: Optional[str] = None


class DayWeather(BaseModel):
    condition: str = "Clear"
    temp: float = 28.0
    rain_prob: int = 10
    is_rainy: bool = False
    wind_speed: float = 12.0
    summary: str = "Pleasant sunny day"


class DayPlan(BaseModel):
    day: int
    date_label: str = "Day 1"
    weather: DayWeather = Field(default_factory=DayWeather)
    theme: str = "Heritage & Forts"
    activities: List[Activity] = Field(default_factory=list)
    day_cost: float = 0.0
    notes: Optional[str] = None


class BudgetBreakdown(BaseModel):
    transport: float = 0.0
    stay: float = 0.0
    food: float = 0.0
    activities: float = 0.0
    local_travel: float = 0.0
    miscellaneous: float = 0.0
    total: float = 0.0
    budget: float = 15000.0
    remaining: float = 0.0
    overrun: bool = False
    percentage_used: float = 0.0
    is_warning: bool = False  # True if percentage_used >= 90%


class TraceStep(BaseModel):
    icon: str = "🧠"
    step: str
    detail: str
    tool_called: Optional[str] = None
    output_summary: Optional[str] = None
    status: Literal["success", "warning", "info", "action"] = "info"


class EventPayload(BaseModel):
    type: Literal["weather", "delay", "budget", "fatigue", "closure", "custom"]
    day_affected: Optional[int] = 2
    description: str
    severity: Literal["low", "medium", "high"] = "medium"
    params: Dict[str, Any] = Field(default_factory=dict)


class PlanChange(BaseModel):
    change_type: Literal["moved", "replaced", "dropped", "downgraded", "adjusted_time", "added"]
    day: int
    activity_name: str
    details: str
    cost_impact: float = 0.0


class ReplanResult(BaseModel):
    success: bool
    event_classified: str
    affected_day: Optional[int] = None
    changes: List[PlanChange] = Field(default_factory=list)
    explanation: str
    hinglish_explanation: str
    old_itinerary_summary: Optional[str] = None
    new_budget: Optional[BudgetBreakdown] = None
    trace: List[TraceStep] = Field(default_factory=list)


class Itinerary(BaseModel):
    trip: TripRequest
    days: List[DayPlan] = Field(default_factory=list)
    budget_breakdown: BudgetBreakdown = Field(default_factory=BudgetBreakdown)
    created_at: str = ""
    status: Literal["draft", "valid", "replanned", "warning"] = "valid"
    validation_issues: List[str] = Field(default_factory=list)
    active_events: List[EventPayload] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
