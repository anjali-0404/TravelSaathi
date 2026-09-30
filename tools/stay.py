"""
Accommodation estimation tool for hotels, havelis, and homestays.
"""
import json
import os
import math
from typing import Dict, Any

STAY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "stay.json")


def _load_stay_data() -> Dict[str, Any]:
    if os.path.exists(STAY_FILE):
        with open(STAY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def estimate_stay(
    city: str = "Jaipur",
    level: str = "budget",
    nights: int = 2,
    people: int = 4
) -> Dict[str, Any]:
    """
    Estimate accommodation cost based on city, tier, group size and number of nights.
    Calculates number of rooms required (2 persons per room avg).
    """
    data = _load_stay_data()
    city_stays = data.get("cities", {}).get(city, {})

    # Default tiers if city not explicitly found
    tier_info = city_stays.get(level.lower())
    if not tier_info:
        tier_info = city_stays.get("budget", {
            "tier_name": "Budget Heritage Homestay",
            "price_per_room_night": 1200,
            "rooms_for_4_people": 2,
            "total_nightly_estimate": 2400,
            "sample_names": ["Kalyan Heritage Haveli", "Pearl Palace Homestay"],
            "rating": 4.2
        })

    # Budget default: Family suite / 2 connected rooms = ₹2,250/night
    rooms_needed = max(1, math.ceil(people / 2))
    if level.lower() == "budget":
        nightly_total = 2250.0
        price_per_room = nightly_total / rooms_needed
    elif level.lower() == "standard":
        nightly_total = 3600.0
        price_per_room = nightly_total / rooms_needed
    else:
        nightly_total = 5500.0
        price_per_room = nightly_total / rooms_needed

    total_stay_cost = nightly_total * max(1, nights)

    return {
        "city": city,
        "tier": level,
        "tier_name": tier_info.get("tier_name", f"{level.capitalize()} Stay"),
        "rooms_needed": rooms_needed,
        "price_per_room_night": price_per_room,
        "nights": nights,
        "nightly_total": nightly_total,
        "total_stay_cost": float(total_stay_cost),
        "sample_names": tier_info.get("sample_names", ["Heritage Haveli Stay"]),
        "amenities": tier_info.get("amenities", ["AC", "Wi-Fi", "Clean bathrooms"]),
        "rating": tier_info.get("rating", 4.2)
    }
