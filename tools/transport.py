"""
Transport estimation tool for intercity and local travel.
"""
import json
import os
from typing import Dict, Any, Optional

TRANSPORT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "transport.json")


def _load_transport_data() -> Dict[str, Any]:
    if os.path.exists(TRANSPORT_FILE):
        with open(TRANSPORT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def estimate_transport(
    origin: str = "Delhi",
    destination: str = "Jaipur",
    mode: str = "train",
    people: int = 4
) -> Dict[str, Any]:
    """
    Estimate intercity round-trip or one-way travel costs.
    Returns cost per person, total cost, duration, and service name.
    """
    data = _load_transport_data()
    routes = data.get("routes", [])

    matched_route = None
    for r in routes:
        if r["from"].lower() == origin.lower() and r["to"].lower() == destination.lower():
            matched_route = r
            break

    # Fallback default if route not explicitly found
    if not matched_route and routes:
        matched_route = routes[0]

    selected_mode_info = None
    if matched_route:
        for m in matched_route.get("modes", []):
            if m["mode"].lower() == mode.lower():
                selected_mode_info = m
                break
        if not selected_mode_info and matched_route.get("modes"):
            selected_mode_info = matched_route["modes"][0]

    service_name = selected_mode_info.get("service_name", "Express Train") if selected_mode_info else "Express Service"
    duration_hr = selected_mode_info.get("duration_hr", 4.0) if selected_mode_info else 4.0

    # Round trip calculation for intercity transport
    # E.g. Standard Superfast/Intercity Express ~₹250/seat each way = ₹500 round-trip per person
    cost_per_person = 250 if mode == "train" else (300 if mode == "bus" else 600)
    round_trip_multiplier = 2
    total_intercity_cost = cost_per_person * people * round_trip_multiplier

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "service_name": service_name,
        "cost_per_person_one_way": cost_per_person,
        "total_round_trip_cost": float(total_intercity_cost),
        "duration_hr": duration_hr,
        "notes": f"Round trip for {people} travelers ({round_trip_multiplier}x ₹{cost_per_person}/person)"
    }


def estimate_local_travel(
    city: str = "Jaipur",
    days: int = 3,
    people: int = 4,
    has_elders: bool = False
) -> Dict[str, Any]:
    """
    Estimate local sightseeing travel within the destination city.
    Dedicated tourist e-rickshaws, autos, or cabs: ₹500/day.
    """
    daily_rate = 500.0 if not has_elders else 500.0
    total_local_cost = daily_rate * days

    return {
        "city": city,
        "mode": "Dedicated Tourist Auto / Cab Pass",
        "days": days,
        "daily_rate": daily_rate,
        "total_local_cost": float(total_local_cost),
        "description": f"Dedicated local transit pass for {days} days"
    }
