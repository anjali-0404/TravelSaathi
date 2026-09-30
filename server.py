"""
TravelSaarthi FastAPI Backend Server.
Provides REST APIs for Trip Planning, Hinglish Chat, Multi-Tool Research,
Live Open-Meteo Weather, and Dynamic Adaptive Replanning.
Serves the Full-Fledged Modern SaaS Frontend directly at http://localhost:8000.
"""
import os
import json
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models import TripRequest, UserPreferences, EventPayload, Itinerary, ReplanResult
from agent.orchestrator import TravelSaarthiOrchestrator
from tools.weather import get_weather
from tools.places import search_places, _load_all_places
from tools.transport import estimate_transport, estimate_local_travel
from tools.stay import estimate_stay
from tools.validators import validate_entire_itinerary, calculate_budget

app = FastAPI(
    title="TravelSaarthi API",
    description="Adaptive Travel Planning Agent for Bharat Agentic 2026",
    version="2.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = TravelSaarthiOrchestrator()

# In-memory session store
active_sessions: Dict[str, Dict[str, Any]] = {
    "default": {
        "itinerary": None,
        "trip_draft": None,
        "trace": [],
        "latest_replan": None,
        "chat_history": []
    }
}


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


class ReplanRequest(BaseModel):
    session_id: str = "default"
    event_type: str = "weather"
    description: str = "Day 2 ka weather kharab hai."
    day_affected: Optional[int] = 2
    reduction_amount: Optional[float] = 2000.0
    delay_hours: Optional[float] = 2.0


@app.get("/api/health")
def health():
    return {"status": "ok", "agent": "TravelSaarthi", "version": "2.0.0"}


@app.get("/api/places")
def get_places(category: Optional[str] = None, indoor_outdoor: Optional[str] = None):
    """Retrieve attractions dataset with optional filters."""
    places = search_places(category=category, indoor_outdoor=indoor_outdoor, max_results=30)
    return {"places": [p.model_dump() for p in places]}


@app.get("/api/weather/{city}")
def get_city_weather(city: str = "Jaipur", days: int = 3):
    """Fetch live or cached weather for city."""
    weather = get_weather(city, days=days)
    return {"city": city, "days": [w.model_dump() for w in weather]}


@app.post("/api/chat")
def handle_chat(payload: ChatRequest):
    """
    Process natural language or Hinglish user message.
    Handles trip generation, missing field clarifications, and replanning triggers.
    """
    session = active_sessions.setdefault(payload.session_id, {
        "itinerary": None,
        "trip_draft": None,
        "trace": [],
        "latest_replan": None,
        "chat_history": []
    })

    text = payload.message.strip()
    session["chat_history"].append({"role": "user", "text": text})

    lower_q = text.lower()
    is_disruption = any(k in lower_q for k in [
        "weather", "baarish", "rain", "delay", "late", "budget", "kam", "paisa", "fatigue", "thak", "rest"
    ])

    # If active itinerary exists and user mentions a disruption -> trigger replan
    if session["itinerary"] and is_disruption:
        result = orchestrator.handle_replan_event(session["itinerary"], text)
        session["latest_replan"] = result
        if result.trace:
            session["trace"].extend(result.trace)

        agent_reply = result.hinglish_explanation
        session["chat_history"].append({"role": "agent", "text": agent_reply})

        return {
            "type": "replan",
            "reply": agent_reply,
            "itinerary": session["itinerary"].model_dump(),
            "replan_result": result.model_dump(),
            "trace": [t.model_dump() for t in session["trace"]],
            "chat_history": session["chat_history"]
        }

    # Otherwise parse trip intent
    parsed_trip, missing, clarification = orchestrator.parse_user_input(
        text,
        current_trip=session["trip_draft"]
    )
    session["trip_draft"] = parsed_trip

    if missing and not session["itinerary"]:
        agent_reply = f"नमस्ते! Aapke trip plan ko customize karne ke liye kuch zaroori details bataiye:\n\n👉 {clarification}"
        session["chat_history"].append({"role": "agent", "text": agent_reply})
        return {
            "type": "clarification",
            "reply": agent_reply,
            "missing_fields": missing,
            "trip_draft": parsed_trip.model_dump(),
            "chat_history": session["chat_history"]
        }

    # Generate full trip
    itin, trace_steps = orchestrator.generate_itinerary(parsed_trip)
    session["itinerary"] = itin
    session["trace"] = trace_steps
    session["latest_replan"] = None

    agent_reply = f"✅ Shandar! Maine aapke liye {parsed_trip.days}-din ka budget-optimized Jaipur itinerary plan kar diya hai."
    session["chat_history"].append({"role": "agent", "text": agent_reply})

    return {
        "type": "plan_generated",
        "reply": agent_reply,
        "itinerary": itin.model_dump(),
        "trace": [t.model_dump() for t in trace_steps],
        "chat_history": session["chat_history"]
    }


@app.post("/api/generate")
def generate_trip(trip: TripRequest, session_id: str = "default"):
    """Direct programmatic trip generation from structured model."""
    session = active_sessions.setdefault(session_id, {
        "itinerary": None,
        "trip_draft": None,
        "trace": [],
        "latest_replan": None,
        "chat_history": []
    })

    itin, trace = orchestrator.generate_itinerary(trip)
    session["itinerary"] = itin
    session["trace"] = trace
    session["latest_replan"] = None
    session["trip_draft"] = trip

    return {
        "itinerary": itin.model_dump(),
        "trace": [t.model_dump() for t in trace]
    }


@app.post("/api/replan")
def trigger_replan_endpoint(payload: ReplanRequest):
    """Trigger one of the 4 core disruption scenarios."""
    session = active_sessions.setdefault(payload.session_id, {
        "itinerary": None,
        "trip_draft": None,
        "trace": [],
        "latest_replan": None,
        "chat_history": []
    })

    if not session["itinerary"]:
        # Auto-initialize demo trip if none exists
        demo_trip = TripRequest(
            origin="Delhi",
            destination="Jaipur",
            days=3,
            budget=15000.0,
            people=4,
            trip_type="family",
            preferences=UserPreferences(
                food="veg",
                pace="relaxed",
                elders=True,
                children=False,
                hotel_tier="budget",
                transport_mode="train"
            )
        )
        itin, trace = orchestrator.generate_itinerary(demo_trip)
        session["itinerary"] = itin
        session["trace"] = trace

    event = EventPayload(
        type=payload.event_type,
        day_affected=payload.day_affected,
        description=payload.description,
        params={
            "reduction": payload.reduction_amount or 2000.0,
            "delay_hours": payload.delay_hours or 2.0
        }
    )

    result = orchestrator.handle_replan_event(session["itinerary"], event)
    session["latest_replan"] = result
    if result.trace:
        session["trace"].extend(result.trace)

    return {
        "replan_result": result.model_dump(),
        "itinerary": session["itinerary"].model_dump(),
        "trace": [t.model_dump() for t in session["trace"]]
    }


# Mount Static Frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "TravelSaarthi API is online. Frontend loading..."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"[TravelSaarthi] Launching Web Server at http://localhost:{port} ...")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
