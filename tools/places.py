"""
Places and Attractions Search Tool using curated Jaipur dataset.
"""
import json
import os
from typing import List, Optional, Dict, Any
from models import Activity

PLACES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "places.json")


def _load_all_places() -> List[Dict[str, Any]]:
    """Load raw places list from JSON."""
    if os.path.exists(PLACES_FILE):
        with open(PLACES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def search_places(
    city: str = "Jaipur",
    category: Optional[str] = None,
    indoor_outdoor: Optional[str] = None,
    family_friendly: Optional[bool] = None,
    elderly_friendly: Optional[bool] = None,
    tags: Optional[List[str]] = None,
    min_priority: int = 1,
    max_results: int = 20
) -> List[Activity]:
    """
    Search and filter places in the selected city.
    Supports indoor/outdoor, family-friendly, elder-friendly, categories, and tags.
    """
    raw_places = _load_all_places()
    filtered = []

    for item in raw_places:
        # Category filter
        if category and category.lower() != "all" and item.get("category", "").lower() != category.lower():
            continue

        # Indoor / Outdoor filter
        if indoor_outdoor and indoor_outdoor.lower() in ["indoor", "outdoor"]:
            if item.get("indoor_outdoor", "").lower() != indoor_outdoor.lower():
                continue

        # Family / Elderly friendly
        if family_friendly is True and not item.get("family_friendly", True):
            continue
        if elderly_friendly is True and not item.get("elderly_friendly", True):
            continue

        # Priority
        if item.get("priority", 3) < min_priority:
            continue

        # Tags matching
        if tags:
            item_tags = [t.lower() for t in item.get("tags", [])]
            if not any(t.lower() in item_tags for t in tags):
                continue

        # Convert to Activity model
        act = Activity(
            id=item["id"],
            name=item["name"],
            type=item.get("indoor_outdoor", "outdoor"),
            cost=float(item.get("cost", 0.0)),
            duration_hr=float(item.get("duration_hr", 2.0)),
            lat=float(item.get("lat", 26.9124)),
            lon=float(item.get("lon", 75.7873)),
            priority=int(item.get("priority", 3)),
            opening_time=item.get("opening_time", "09:00"),
            closing_time=item.get("closing_time", "18:00"),
            category=item.get("category", "heritage"),
            family_friendly=item.get("family_friendly", True),
            elderly_friendly=item.get("elderly_friendly", True),
            description=item.get("description", "")
        )
        filtered.append(act)

    # Sort by priority descending
    filtered.sort(key=lambda x: x.priority, reverse=True)
    return filtered[:max_results]


def get_place_by_id(place_id: str) -> Optional[Activity]:
    """Retrieve single place Activity by its ID."""
    raw_places = _load_all_places()
    for item in raw_places:
        if item["id"] == place_id:
            return Activity(
                id=item["id"],
                name=item["name"],
                type=item.get("indoor_outdoor", "outdoor"),
                cost=float(item.get("cost", 0.0)),
                duration_hr=float(item.get("duration_hr", 2.0)),
                lat=float(item.get("lat", 26.9124)),
                lon=float(item.get("lon", 75.7873)),
                priority=int(item.get("priority", 3)),
                opening_time=item.get("opening_time", "09:00"),
                closing_time=item.get("closing_time", "18:00"),
                category=item.get("category", "heritage"),
                family_friendly=item.get("family_friendly", True),
                elderly_friendly=item.get("elderly_friendly", True),
                description=item.get("description", "")
            )
    return None
