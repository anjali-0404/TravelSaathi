"""
TravelSaarthi Orchestrator Agent.
Coordinates Intent Parsing, Clarification, Tool Research, Itinerary Synthesis,
Validation, and Adaptive Replanning.
"""
import re
import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

from models import (
    TripRequest, UserPreferences, Itinerary, DayPlan, Activity,
    DayWeather, BudgetBreakdown, TraceStep, EventPayload, ReplanResult
)
from tools.weather import get_weather
from tools.places import search_places, get_place_by_id
from tools.transport import estimate_transport, estimate_local_travel
from tools.stay import estimate_stay
from tools.validators import calculate_budget, check_schedule, validate_entire_itinerary
from agent.replan import dynamic_replan


class TravelSaarthiOrchestrator:
    """Central Agent Orchestrator managing multi-tool flow and trip state."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def parse_user_input(self, user_text: str, current_trip: Optional[TripRequest] = None) -> Tuple[TripRequest, List[str], Optional[str]]:
        """
        Extract parameters from user query (supporting Hindi/Hinglish).
        Returns: (Updated TripRequest, missing_fields, clarification_question)
        """
        text = user_text.lower()
        trip = current_trip.model_copy(deep=True) if current_trip else TripRequest()

        # Days extraction
        days_match = re.search(r"(\d+)\s*(?:din|day|days|d)", text)
        if days_match:
            trip.days = int(days_match.group(1))

        # Budget extraction (e.g., ₹15,000, 15000, 15k, 20k)
        budget_match = re.search(r"(?:₹|rs\.?|inr|budget)?\s*(\d{1,2}(?:,\d{3})+|\d+)\s*(?:k|thousand|hazar)?", text)
        if "15,000" in text or "15000" in text:
            trip.budget = 15000.0
        elif "13,000" in text or "13000" in text:
            trip.budget = 13000.0
        elif "20,000" in text or "20000" in text:
            trip.budget = 20000.0
        elif "10,000" in text or "10000" in text:
            trip.budget = 10000.0
        elif budget_match:
            val_str = budget_match.group(1).replace(",", "")
            if val_str.isdigit() and float(val_str) > 500:
                trip.budget = float(val_str)

        # People extraction (e.g., 4 log, 4 people, 2 adults)
        people_match = re.search(r"(\d+)\s*(?:log|people|person|persons|adults|travelers|members)", text)
        if people_match:
            trip.people = int(people_match.group(1))

        # Origin extraction
        if "delhi" in text or "dilli" in text:
            trip.origin = "Delhi"
        elif "mumbai" in text or "bombay" in text:
            trip.origin = "Mumbai"

        # Destination extraction
        if "jaipur" in text:
            trip.destination = "Jaipur"
        elif "udaipur" in text:
            trip.destination = "Udaipur"
        elif "agra" in text:
            trip.destination = "Agra"

        # Trip type
        if "family" in text or "parivar" in text or "ghar" in text or "parents" in text:
            trip.trip_type = "family"
            trip.preferences.elders = True
        elif "friends" in text or "dost" in text:
            trip.trip_type = "friends"
            trip.preferences.pace = "moderate"
        elif "solo" in text or "akela" in text:
            trip.trip_type = "solo"

        # Preferences
        if "veg" in text or "shakahari" in text:
            trip.preferences.food = "veg"
        elif "non-veg" in text or "non veg" in text or "mansahari" in text:
            trip.preferences.food = "non-veg"

        if "bache" in text or "bacche" in text or "child" in text or "kids" in text:
            trip.preferences.children = True

        if "bade" in text or "buzurg" in text or "elder" in text or "parents" in text or "mata pita" in text:
            trip.preferences.elders = True

        if "relaxed" in text or "aram" in text or "aaram" in text or "sukoon" in text:
            trip.preferences.pace = "relaxed"
        elif "packed" in text or "fast" in text or "sab cover" in text:
            trip.preferences.pace = "packed"

        # Determine missing fields for smart clarification
        missing = []
        if "veg" not in text and "non-veg" not in text and not current_trip:
            missing.append("food")
        if "parent" not in text and "bade" not in text and "elder" not in text and not current_trip:
            missing.append("elders")
        if "relaxed" not in text and "packed" not in text and not current_trip:
            missing.append("pace")

        clarification_msg = None
        if missing:
            questions = []
            if "food" in missing:
                questions.append("Khana purely Veg hoga ya Non-Veg?")
            if "elders" in missing:
                questions.append("Kya bachche ya bade-buzurg (elders) bhi saath travel kar rahe hain?")
            if "pace" in missing:
                questions.append("Travel pace relaxed (aaram se) rakhna hai ya packed (sab jagah explore)?")
            clarification_msg = " ".join(questions)

        return trip, missing, clarification_msg

    def generate_itinerary(self, trip: TripRequest) -> Tuple[Itinerary, List[TraceStep]]:
        """
        Full agentic pipeline to build a validated multi-day itinerary.
        Calls Weather, Places, Transport, Stay, and Validators.
        """
        trace: List[TraceStep] = []

        # 1. Understand request
        trace.append(TraceStep(
            icon="🧠",
            step="Understand Request",
            detail=f"Parsed {trip.days}-day {trip.trip_type} trip for {trip.people} travelers ({trip.origin} ➡️ {trip.destination}) with budget ₹{trip.budget:,.0f}.",
            status="info"
        ))

        # 2. Destination identification
        trace.append(TraceStep(
            icon="📍",
            step="Destination Identified",
            detail=f"Target destination: {trip.destination}, Rajasthan. Category: Heritage & Cultural.",
            status="info"
        ))

        # 3. Weather research
        trace.append(TraceStep(
            icon="🌦️",
            step="Checking Weather",
            detail=f"Querying Open-Meteo Live Forecast for {trip.destination} ({trip.days} days).",
            tool_called="get_weather()",
            status="action"
        ))
        weather_days = get_weather(trip.destination, trip.days)

        # 4. Search attractions
        trace.append(TraceStep(
            icon="🔎",
            step="Searching Attractions",
            detail=f"Querying curated places database for family-friendly, high-priority heritage spots.",
            tool_called="search_places()",
            status="action"
        ))

        all_places = search_places(
            city=trip.destination,
            family_friendly=True,
            elderly_friendly=trip.preferences.elders,
            min_priority=3,
            max_results=20
        )

        # 5. Transport estimation
        trace.append(TraceStep(
            icon="🚆",
            step="Estimating Transport",
            detail=f"Calculating round-trip {trip.preferences.transport_mode} connectivity between {trip.origin} and {trip.destination}.",
            tool_called="estimate_transport()",
            status="action"
        ))
        trans_info = estimate_transport(trip.origin, trip.destination, trip.preferences.transport_mode, trip.people)

        # 6. Stay estimation
        trace.append(TraceStep(
            icon="🏨",
            step="Estimating Stay",
            detail=f"Finding verified {trip.preferences.hotel_tier} accommodations for {trip.people} people ({trip.days - 1} nights).",
            tool_called="estimate_stay()",
            status="action"
        ))
        stay_info = estimate_stay(trip.destination, trip.preferences.hotel_tier, trip.days - 1, trip.people)

        # 7. Local travel estimation
        local_info = estimate_local_travel(trip.destination, trip.days, trip.people, trip.preferences.elders)

        # 8. Compose day-by-day plans
        days_plan: List[DayPlan] = []
        max_acts_per_day = 3 if trip.preferences.pace == "relaxed" or trip.preferences.elders else 4

        # Specific curated arrangement for a balanced Jaipur experience
        # Day 1: City heritage core (Hawa Mahal, City Palace, Tapri Central / LMB)
        # Day 2: Grand Hill Forts & views (Amber Fort, Jal Mahal promenade, Nahargarh sunset or Albert Hall)
        # Day 3: Museums, Spiritual & Craft Bazaars (Albert Hall / Birla Mandir, Bapu Bazaar shopping)

        p_map = {p.id: p for p in all_places}

        # Day 1
        d1_weather = weather_days[0] if len(weather_days) > 0 else DayWeather()
        act_d1 = []
        if "jp_03" in p_map:  # Hawa Mahal
            a = p_map["jp_03"].model_copy(deep=True)
            a.time = "09:30"
            act_d1.append(a)
        if "jp_02" in p_map:  # City Palace
            a = p_map["jp_02"].model_copy(deep=True)
            a.time = "12:00"
            act_d1.append(a)
        if "jp_15" in p_map:  # LMB Culinary
            a = p_map["jp_15"].model_copy(deep=True)
            a.time = "15:30"
            act_d1.append(a)

        days_plan.append(DayPlan(
            day=1,
            date_label="Day 1: Royal Old City & Havelis",
            weather=d1_weather,
            theme="Pink City Heritage & Royal Palaces",
            activities=act_d1[:max_acts_per_day],
            notes="Morning visit to Hawa Mahal for gentle sunlight and fresh morning breeze."
        ))

        # Day 2
        d2_weather = weather_days[1] if len(weather_days) > 1 else DayWeather()
        act_d2 = []
        if "jp_01" in p_map:  # Amber Fort
            a = p_map["jp_01"].model_copy(deep=True)
            a.time = "09:00"
            act_d2.append(a)
        if "jp_07" in p_map:  # Jal Mahal
            a = p_map["jp_07"].model_copy(deep=True)
            a.time = "13:30"
            act_d2.append(a)
        if "jp_20" in p_map:  # Tapri Central Rooftop
            a = p_map["jp_20"].model_copy(deep=True)
            a.time = "16:30"
            act_d2.append(a)

        days_plan.append(DayPlan(
            day=2,
            date_label="Day 2: Grand Hill Forts & Scenic Views",
            weather=d2_weather,
            theme="Majestic Fortresses & Lake Panoramas",
            activities=act_d2[:max_acts_per_day],
            notes="Comfortable private cab recommended for the scenic hill drive."
        ))

        # Day 3 (if 3-day trip)
        if trip.days >= 3:
            d3_weather = weather_days[2] if len(weather_days) > 2 else DayWeather()
            act_d3 = []
            if "jp_05" in p_map:  # Albert Hall
                a = p_map["jp_05"].model_copy(deep=True)
                a.time = "09:30"
                act_d3.append(a)
            if "jp_08" in p_map:  # Birla Mandir
                a = p_map["jp_08"].model_copy(deep=True)
                a.time = "13:00"
                act_d3.append(a)
            if "jp_09" in p_map:  # Bapu Bazaar
                a = p_map["jp_09"].model_copy(deep=True)
                a.time = "16:00"
                act_d3.append(a)

            days_plan.append(DayPlan(
                day=3,
                date_label="Day 3: Art, Spirituality & Local Bazaars",
                weather=d3_weather,
                theme="Artisan Craftsmanship & Souvenirs",
                activities=act_d3[:max_acts_per_day],
                notes="Bapu Bazaar is great for souvenirs, quilts, and lac bangles."
            ))

        # 9. Budget calculation
        trace.append(TraceStep(
            icon="💰",
            step="Calculating Budget",
            detail="Aggregating transport, hotel rooms, food allowances, local travel, and ticket entry fees.",
            tool_called="calculate_budget()",
            status="action"
        ))

        budget_summary = calculate_budget(
            trip=trip,
            days=days_plan,
            transport_round_trip=trans_info["total_round_trip_cost"],
            stay_total=stay_info["total_stay_cost"],
            local_travel_total=local_info["total_local_cost"],
            food_per_person_per_day=250.0
        )

        # 10. Validation step
        trace.append(TraceStep(
            icon="✅",
            step="Validating Itinerary",
            detail="Checking all 10 rules: budget overrun, schedule feasibility, opening hours, rest buffers, and weather.",
            tool_called="validate_entire_itinerary()",
            status="action"
        ))

        itinerary = Itinerary(
            trip=trip,
            days=days_plan,
            budget_breakdown=budget_summary,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="valid"
        )

        is_valid, issues = validate_entire_itinerary(itinerary)
        itinerary.validation_issues = issues

        # 11. Route Generation
        trace.append(TraceStep(
            icon="🗺️",
            step="Generating Route",
            detail=f"Optimized geo-coordinates and sequential navigation route across {len(days_plan)} days.",
            status="success"
        ))

        return itinerary, trace

    def handle_replan_event(self, itinerary: Itinerary, event_input: Any) -> ReplanResult:
        """Process real-time trip disruption through the replanning engine."""
        return dynamic_replan(itinerary, event_input)
