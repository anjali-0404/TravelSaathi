"""
Map generation and helper utilities for TravelSaarthi.
Builds interactive Folium maps with day-colored markers and route polylines.
"""
from typing import List, Dict, Any, Optional
import folium
from folium import plugins
from models import Itinerary, DayPlan

DAY_COLORS = {
    1: {"pin": "blue", "hex": "#2563eb"},
    2: {"pin": "green", "hex": "#059669"},
    3: {"pin": "purple", "hex": "#7c3aed"},
    4: {"pin": "orange", "hex": "#ea580c"},
    5: {"pin": "red", "hex": "#dc2626"}
}


def build_interactive_itinerary_map(itinerary: Itinerary) -> folium.Map:
    """
    Generate an interactive Leaflet/Folium map with numbered day-wise markers
    and route lines connecting consecutive attractions.
    """
    all_points = []
    for day in itinerary.days:
        for act in day.activities:
            all_points.append((act.lat, act.lon))

    # Center map on centroid or default Jaipur
    if all_points:
        avg_lat = sum(p[0] for p in all_points) / len(all_points)
        avg_lon = sum(p[1] for p in all_points) / len(all_points)
    else:
        avg_lat, avg_lon = 26.9124, 75.7873

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True
    )

    # Add markers and path per day
    for day in itinerary.days:
        day_color_info = DAY_COLORS.get(day.day, {"pin": "blue", "hex": "#2563eb"})
        day_points = []

        for idx, act in enumerate(day.activities, 1):
            day_points.append([act.lat, act.lon])

            # Popup HTML
            indoor_badge = "🏢 Indoor" if act.type == "indoor" else "🌲 Outdoor"
            cost_str = f"₹{act.cost:,.0f}/person" if act.cost > 0 else "Free Entry"

            popup_html = f"""
            <div style="font-family: 'Segoe UI', sans-serif; width: 220px; padding: 4px;">
                <div style="font-size: 11px; font-weight: 700; color: {day_color_info['hex']}; text-transform: uppercase;">
                    Day {day.day} • Stop #{idx} ({act.time})
                </div>
                <div style="font-size: 14px; font-weight: 700; margin: 3px 0; color: #1e293b;">
                    {act.name}
                </div>
                <div style="margin: 4px 0;">
                    <span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">{indoor_badge}</span>
                    <span style="background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;">{cost_str}</span>
                </div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                    ⏱️ Duration: {act.duration_hr:g} hrs | ⏰ Open: {act.opening_time} - {act.closing_time}
                </div>
            </div>
            """

            folium.Marker(
                location=[act.lat, act.lon],
                tooltip=f"Day {day.day} #{idx}: {act.name} ({act.time})",
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(
                    color=day_color_info["pin"],
                    icon="info-sign",
                    prefix="glyphicon"
                )
            ).add_to(m)

        # Draw connecting route line for the day
        if len(day_points) > 1:
            folium.PolyLine(
                locations=day_points,
                color=day_color_info["hex"],
                weight=3.5,
                opacity=0.85,
                dash_array="6, 8",
                tooltip=f"Day {day.day} Route"
            ).add_to(m)

    return m
