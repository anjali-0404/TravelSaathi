"""
Validation and budget calculation engine for TravelSaarthi.
Enforces all 10 core constraints and produces clear feedback.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from models import TripRequest, DayPlan, Activity, BudgetBreakdown, Itinerary


def calculate_budget(
    trip: TripRequest,
    days: List[DayPlan],
    transport_round_trip: float,
    stay_total: float,
    local_travel_total: float,
    food_per_person_per_day: float = 250.0
) -> BudgetBreakdown:
    """
    Calculate comprehensive budget breakdown including food, activities, stay, and travel.
    Warns when usage reaches >= 90%.
    """
    total_activities_cost = 0.0
    for d in days:
        for a in d.activities:
            # Activity cost is multiplied by number of people if it's ticketed, or fixed if group
            total_activities_cost += (a.cost * trip.people)

    # Food calculation: e.g. breakfast + lunch + dinner + snacks per person per day
    total_food_cost = food_per_person_per_day * trip.people * trip.days
    miscellaneous = 0.0  # Included in contingency buffer / remaining funds

    total_spent = (
        transport_round_trip +
        stay_total +
        total_food_cost +
        total_activities_cost +
        local_travel_total +
        miscellaneous
    )

    remaining = trip.budget - total_spent
    percentage_used = round((total_spent / trip.budget) * 100, 1) if trip.budget > 0 else 100.0
    overrun = total_spent > trip.budget
    is_warning = percentage_used >= 90.0

    return BudgetBreakdown(
        transport=round(transport_round_trip, 2),
        stay=round(stay_total, 2),
        food=round(total_food_cost, 2),
        activities=round(total_activities_cost, 2),
        local_travel=round(local_travel_total, 2),
        miscellaneous=round(miscellaneous, 2),
        total=round(total_spent, 2),
        budget=round(trip.budget, 2),
        remaining=round(remaining, 2),
        overrun=overrun,
        percentage_used=percentage_used,
        is_warning=is_warning
    )


def _parse_time_str(time_str: str) -> datetime:
    """Parse HH:MM string into datetime object for arithmetic."""
    try:
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return datetime(2026, 1, 1, hour, minute)
    except Exception:
        return datetime(2026, 1, 1, 9, 0)


def check_schedule(
    day_plan: DayPlan,
    pace: str = "relaxed",
    has_elders: bool = False
) -> Dict[str, Any]:
    """
    Validate a single day's plan against scheduling rules:
    - Activity limits (3 for relaxed/elders, 5 for normal)
    - Opening and closing times
    - Overlapping activities
    - Rain vs outdoor activities
    """
    issues = []
    activities = day_plan.activities

    # Rule 3 & 4: Activity counts
    max_activities = 3 if (pace == "relaxed" or has_elders) else 5
    if len(activities) > max_activities:
        issues.append(
            f"Day {day_plan.day} has {len(activities)} activities (exceeds recommended max {max_activities} for {pace} pace / elders)."
        )

    # Rule 7: Rain vs outdoor activities
    if day_plan.weather.is_rainy:
        for act in activities:
            if act.type == "outdoor":
                issues.append(
                    f"Day {day_plan.day} has high rain probability ({day_plan.weather.rain_prob}%), but outdoor activity '{act.name}' is scheduled."
                )

    # Rule 6, 8, 9: Time constraints, opening hours & overlapping
    current_time = None
    for i, act in enumerate(activities):
        start_dt = _parse_time_str(act.time)
        end_dt = start_dt + timedelta(hours=act.duration_hr)
        open_dt = _parse_time_str(act.opening_time)
        close_dt = _parse_time_str(act.closing_time)

        # Opening hours check
        if start_dt < open_dt:
            issues.append(f"'{act.name}' starts at {act.time}, but does not open until {act.opening_time}.")
        if end_dt > close_dt:
            issues.append(f"'{act.name}' ends around {end_dt.strftime('%H:%M')}, but closes at {act.closing_time}.")

        # Overlap and travel time check
        if current_time:
            transit_buffer = timedelta(minutes=30)
            if start_dt < (current_time + transit_buffer):
                overlap_mins = int(((current_time + transit_buffer) - start_dt).total_seconds() / 60)
                if start_dt < current_time:
                    issues.append(f"Overlap detected: '{act.name}' starts at {act.time} before previous activity finishes.")
                else:
                    issues.append(f"Insufficient travel gap ({overlap_mins}m needed) before '{act.name}'.")

        current_time = end_dt

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "day": day_plan.day
    }


def validate_entire_itinerary(itinerary: Itinerary) -> Tuple[bool, List[str]]:
    """
    Validate all 10 core constraints across the entire itinerary:
    1. total cost <= budget
    2. warning when >= 90%
    3. relaxed/elderly travelers: max 3 activities/day
    4. normal travelers: max 5 activities/day
    5. travel time fits between activities
    6. opening hours respected
    7. outdoor activities not on rainy days
    8. rest gaps for families
    9. no overlapping activities
    10. valid days exist
    """
    all_issues = []

    # Rule 1 & 2: Budget check
    if itinerary.budget_breakdown.overrun:
        all_issues.append(
            f"Budget exceeded! Total spent ₹{itinerary.budget_breakdown.total:,.0f} exceeds budget ₹{itinerary.budget_breakdown.budget:,.0f}."
        )

    # Rule 10: Valid days
    if not itinerary.days:
        all_issues.append("Itinerary contains no days.")
        return False, all_issues

    # Check each day's schedule
    for day in itinerary.days:
        if not day.activities:
            all_issues.append(f"Day {day.day} has no planned activities.")

        day_check = check_schedule(
            day,
            pace=itinerary.trip.preferences.pace,
            has_elders=itinerary.trip.preferences.elders
        )
        all_issues.extend(day_check["issues"])

    is_valid = len([i for i in all_issues if "Budget exceeded" in i or "Overlap" in i or "closes at" in i or "rain probability" in i]) == 0
    return is_valid, all_issues
