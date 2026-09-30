"""
TravelSaarthi — Adaptive Travel Planning Agent
Bharat Agentic 2026 Hackathon (Mobility / Agentic AI Track)
"TravelSaarthi doesn't just plan a trip — it fixes the trip when things go wrong."
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
from datetime import datetime

from models import TripRequest, UserPreferences, Itinerary, EventPayload, ReplanResult
from agent.orchestrator import TravelSaarthiOrchestrator
from utils.formatting import format_inr, get_category_icon, get_weather_icon
from utils.helpers import build_interactive_itinerary_map

# Page configuration
st.set_page_config(
    page_title="TravelSaarthi • Adaptive Travel Agent",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern SaaS Aesthetics (Linear / Vercel style)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main background & container */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(12px);
    }

    .hero-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 12px;
    }

    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .badge-primary { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .badge-success { background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
    .badge-warning { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
    .badge-danger { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.3); }

    /* Day Cards */
    .day-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .day-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }

    .day-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 10px;
        margin-bottom: 14px;
    }

    .day-title {
        font-size: 17px;
        font-weight: 700;
        color: #e2e8f0;
    }

    /* Activity items */
    .activity-row {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .act-time {
        font-size: 13px;
        font-weight: 700;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        padding: 4px 8px;
        border-radius: 6px;
        min-width: 60px;
        text-align: center;
        margin-right: 12px;
    }

    .act-info {
        flex-grow: 1;
    }

    .act-name {
        font-size: 14px;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 2px;
    }

    .act-meta {
        font-size: 12px;
        color: #94a3b8;
    }

    .act-cost {
        font-size: 13px;
        font-weight: 700;
        color: #34d399;
        text-align: right;
        min-width: 90px;
    }

    /* Metric Box */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-label {
        font-size: 11px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 800;
        color: #f8fafc;
    }

    /* Why Changed Alert Box */
    .why-changed-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
        border: 1px solid rgba(129, 140, 248, 0.4);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 20px;
        animation: fadeIn 0.4s ease-in-out;
    }

    .why-title {
        font-size: 16px;
        font-weight: 700;
        color: #a5b4fc;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .why-text {
        font-size: 13.5px;
        color: #e2e8f0;
        line-height: 1.5;
    }

    /* Trace Timeline item */
    .trace-item {
        background: rgba(15, 23, 42, 0.7);
        border-left: 3px solid #6366f1;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 12.5px;
    }
    .trace-item-success { border-left-color: #10b981; }
    .trace-item-warning { border-left-color: #f59e0b; }
    .trace-item-action { border-left-color: #38bdf8; }

    /* Custom Streamlit sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = TravelSaarthiOrchestrator()

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None

if "trace" not in st.session_state:
    st.session_state.trace = []

if "latest_replan_result" not in st.session_state:
    st.session_state.latest_replan_result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_clarification" not in st.session_state:
    st.session_state.pending_clarification = None

if "current_trip_draft" not in st.session_state:
    st.session_state.current_trip_draft = None


# Helper to run initial plan generation
def trigger_generation(trip_req: TripRequest):
    with st.spinner("🤖 TravelSaarthi Agent synthesizing optimal itinerary..."):
        itin, trace_steps = st.session_state.orchestrator.generate_itinerary(trip_req)
        st.session_state.itinerary = itin
        st.session_state.trace = trace_steps
        st.session_state.latest_replan_result = None
        st.session_state.pending_clarification = None
        st.session_state.current_trip_draft = trip_req


# Helper to run replan simulation
def trigger_replan(event_payload_or_text):
    if not st.session_state.itinerary:
        st.warning("Please generate a trip first before simulating disruptions!")
        return

    with st.spinner("⚡ TravelSaarthi Adaptive Engine re-evaluating schedule & budget..."):
        replan_res = st.session_state.orchestrator.handle_replan_event(
            st.session_state.itinerary,
            event_payload_or_text
        )
        st.session_state.latest_replan_result = replan_res
        if replan_res.trace:
            st.session_state.trace.extend(replan_res.trace)


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
        <span style="font-size: 30px;">🧭</span>
        <div>
            <div style="font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">TravelSaarthi</div>
            <div style="font-size: 11px; color: #38bdf8; font-weight: 600;">Adaptive Travel Agent • Bharat 2026</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ New Trip Plan", use_container_width=True):
        st.session_state.itinerary = None
        st.session_state.trace = []
        st.session_state.latest_replan_result = None
        st.session_state.pending_clarification = None
        st.session_state.current_trip_draft = None
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Live Demo Scenarios")
    st.caption("One-click triggers for hackathon judging:")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✨ Demo Trip", use_container_width=True, help="3 days, ₹15,000, Delhi to Jaipur, 4 people family trip"):
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
            trigger_generation(demo_trip)
            st.rerun()

    with col_btn2:
        if st.button("🌧️ Bad Weather", use_container_width=True, help="Simulate heavy rain forecast on Day 2"):
            trigger_replan("Day 2 ka weather kharab hai aur baarish expected hai.")
            st.rerun()

    col_btn3, col_btn4 = st.columns(2)
    with col_btn3:
        if st.button("🚆 Train Delay", use_container_width=True, help="Simulate 2-hour train delay on arrival"):
            trigger_replan("Inbound train 2 ghante late ho gayi.")
            st.rerun()

    with col_btn4:
        if st.button("💰 Budget Cut", use_container_width=True, help="Simulate ₹2,000 budget reduction"):
            trigger_replan("Budget ₹2,000 kam ho gaya hai.")
            st.rerun()

    if st.button("😴 Traveler Fatigue (Rest Mode)", use_container_width=True, help="Relax schedule for tired elders/kids"):
        trigger_replan("Family aur parents thak gaye hain, schedule aaramdayak karo.")
        st.rerun()

    st.markdown("---")

    # Current Trip Parameters Panel
    if st.session_state.itinerary:
        trip = st.session_state.itinerary.trip
        st.markdown("### 📋 Active Trip Context")
        st.markdown(f"**Route:** `{trip.origin}` ➡️ `{trip.destination}`")
        st.markdown(f"**Duration:** `{trip.days} Days` | **Travelers:** `{trip.people} ({trip.trip_type})`")
        st.markdown(f"**Diet:** `{trip.preferences.food.capitalize()}` | **Pace:** `{trip.preferences.pace.capitalize()}`")
        st.markdown(f"**Elders Present:** `{'Yes (Senior Care)' if trip.preferences.elders else 'No'}`")
        st.markdown(f"**Stay Tier:** `{trip.preferences.hotel_tier.capitalize()}`")
    else:
        st.info("💡 Enter your trip details in Hinglish/English in the chat below or click **✨ Demo Trip** above to begin!")


# ==========================================
# MAIN CONTENT AREA
# ==========================================

# Top Hero Bar
st.markdown("""
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
            <div class="hero-title">TravelSaarthi (ट्रैवल सारथी)</div>
            <div class="hero-subtitle">
                The Adaptive Travel Agent for Indian Families • <i>"We don't just plan a trip — we fix it when things go wrong."</i>
            </div>
            <div>
                <span class="badge-pill badge-primary">⚡ Agentic Replanning</span>
                <span class="badge-pill badge-success">🌦️ Live Open-Meteo Weather</span>
                <span class="badge-pill badge-warning">💰 Dynamic Budget Guard</span>
                <span class="badge-pill badge-primary">🗣️ Hinglish Native</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# INPUT & CHAT SECTION
# ==========================================
chat_col, status_col = st.columns([3.2, 1.8])

with chat_col:
    user_query = st.chat_input("Enter in Hindi/Hinglish (e.g., '3 din, ₹15,000, Delhi se Jaipur, family trip, 4 log')...")

    # If user submitted query
    if user_query:
        st.session_state.chat_history.append({"role": "user", "text": user_query})

        # Check if this is an event/replan instruction on an existing itinerary
        lower_q = user_query.lower()
        is_event = any(k in lower_q for k in ["weather", "baarish", "rain", "delay", "late", "budget", "kam", "paisa", "fatigue", "thak", "rest"])

        if st.session_state.itinerary and is_event:
            trigger_replan(user_query)
            if st.session_state.latest_replan_result:
                st.session_state.chat_history.append({
                    "role": "agent",
                    "text": st.session_state.latest_replan_result.hinglish_explanation
                })
        else:
            # Parse trip intent
            parsed_trip, missing_fields, clarification = st.session_state.orchestrator.parse_user_input(
                user_query,
                current_trip=st.session_state.current_trip_draft
            )
            st.session_state.current_trip_draft = parsed_trip

            if missing_fields and not st.session_state.itinerary:
                st.session_state.pending_clarification = clarification
                st.session_state.chat_history.append({
                    "role": "agent",
                    "text": f"नमस्ते! Aapke trip ke liye kuch zaroori details bataiye:\n\n👉 {clarification}"
                })
            else:
                trigger_generation(parsed_trip)
                st.session_state.chat_history.append({
                    "role": "agent",
                    "text": f"✅ Shandar! Maine aapke liye {parsed_trip.days}-din ka budget-optimized Jaipur itinerary plan kar diya hai."
                })

    # Render Clarification Prompt Pill if waiting
    if st.session_state.pending_clarification and not st.session_state.itinerary:
        st.markdown(f"""
        <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="font-weight: 700; color: #fbbf24; font-size: 14px; margin-bottom: 4px;">🤔 Quick Clarification Needed:</div>
            <div style="font-size: 13px; color: #fef3c7;">{st.session_state.pending_clarification}</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🥦 Pure Veg + Relaxed", key="btn_clar_1"):
                draft = st.session_state.current_trip_draft or TripRequest()
                draft.preferences.food = "veg"
                draft.preferences.pace = "relaxed"
                draft.preferences.elders = True
                trigger_generation(draft)
                st.rerun()
        with c2:
            if st.button("🍗 Non-Veg + Moderate", key="btn_clar_2"):
                draft = st.session_state.current_trip_draft or TripRequest()
                draft.preferences.food = "non-veg"
                draft.preferences.pace = "moderate"
                draft.preferences.elders = False
                trigger_generation(draft)
                st.rerun()
        with c3:
            if st.button("⚡ Fast / Packed Pace", key="btn_clar_3"):
                draft = st.session_state.current_trip_draft or TripRequest()
                draft.preferences.pace = "packed"
                trigger_generation(draft)
                st.rerun()

with status_col:
    # Summary Card or Live Status
    if st.session_state.itinerary:
        b = st.session_state.itinerary.budget_breakdown
        st.markdown(f"""
        <div class="metric-card" style="border-color: {'rgba(239, 68, 68, 0.5)' if b.overrun else 'rgba(16, 185, 129, 0.4)'};">
            <div class="metric-label">Total Estimated Budget</div>
            <div class="metric-value" style="color: {'#f87171' if b.overrun else '#34d399'};">{format_inr(b.total)} <span style="font-size: 14px; color: #94a3b8;">/ {format_inr(b.budget)}</span></div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                Remaining: <b style="color: #38bdf8;">{format_inr(b.remaining)}</b> ({b.percentage_used}% used)
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">System Status</div>
            <div class="metric-value" style="color: #38bdf8; font-size: 18px;">Ready for Inputs</div>
            <div style="font-size: 11.5px; color: #94a3b8; margin-top: 4px;">Open-Meteo & Jaipur Database Armed</div>
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# REPLAN DIFF & EXPLANATION BANNER (CORE JUDGING DIFFERENTIATOR)
# ==========================================
if st.session_state.latest_replan_result:
    res = st.session_state.latest_replan_result
    st.markdown(f"""
    <div class="why-changed-box">
        <div class="why-title">
            <span>✨</span>
            <span>Why did TravelSaarthi adapt your plan? (क्यों बदला आपका प्लान?)</span>
            <span class="badge-pill badge-warning" style="margin-left: auto;">{res.event_classified}</span>
        </div>
        <div class="why-text">
            <b>Hinglish Explanation:</b> {res.hinglish_explanation}<br><br>
            <b>English Rationale:</b> {res.explanation}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show Changed Diff items
    if res.changes:
        st.markdown("#### 🔄 What Changed in Your Itinerary:")
        cols = st.columns(min(len(res.changes), 3))
        for idx, chg in enumerate(res.changes):
            with cols[idx % 3]:
                badge_type = "badge-success" if chg.change_type in ["added", "replaced"] else "badge-warning"
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span class="badge-pill {badge_type}">Day {chg.day} • {chg.change_type.upper()}</span>
                    </div>
                    <div style="font-size: 13.5px; font-weight: 700; color: #f8fafc;">{chg.activity_name}</div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">{chg.details}</div>
                </div>
                """, unsafe_allow_html=True)


# ==========================================
# ITINERARY & DASHBOARD MAIN TABS
# ==========================================
if st.session_state.itinerary:
    itin = st.session_state.itinerary
    tab_itin, tab_budget, tab_map, tab_trace = st.tabs([
        "📅 Day-Wise Itinerary",
        "💰 Budget Breakdown",
        "🗺️ Interactive Route Map",
        "🧠 Agent Execution Trace"
    ])

    # ------------------------------------------
    # TAB 1: ITINERARY CARDS
    # ------------------------------------------
    with tab_itin:
        st.markdown("### 🗓️ Curated Day-by-Day Schedule")

        for day in itin.days:
            w_icon = get_weather_icon(day.weather.condition)
            rain_badge = "badge-danger" if day.weather.is_rainy else "badge-success"

            st.markdown(f"""
            <div class="day-card">
                <div class="day-header">
                    <div>
                        <div class="day-title">{day.date_label}</div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Theme: {day.theme}</div>
                    </div>
                    <div style="text-align: right;">
                        <span class="badge-pill {rain_badge}">{w_icon} {day.weather.condition} • {day.weather.temp:g}°C (Rain: {day.weather.rain_prob}%)</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Activities in the day
            day_act_cost = 0.0
            for act in day.activities:
                c_icon = get_category_icon(act.category, act.type)
                type_tag = "🏢 Indoor" if act.type == "indoor" else "🌲 Outdoor"
                act_total = act.cost * itin.trip.people
                day_act_cost += act_total
                cost_text = f"₹{act.cost:,.0f} x {itin.trip.people} = {format_inr(act_total)}" if act.cost > 0 else "Free Entry"

                st.markdown(f"""
                <div class="activity-row">
                    <div style="display: flex; align-items: center;">
                        <div class="act-time">{act.time}</div>
                        <div class="act-info">
                            <div class="act-name">{c_icon} {act.name}</div>
                            <div class="act-meta">
                                <span>{type_tag}</span> • 
                                <span>⏱️ {act.duration_hr:g} hrs</span> • 
                                <span>⏰ Hours: {act.opening_time} - {act.closing_time}</span> • 
                                <span>⭐ Priority {act.priority}/5</span>
                            </div>
                        </div>
                    </div>
                    <div class="act-cost">{cost_text}</div>
                </div>
                """, unsafe_allow_html=True)

            if day.notes:
                st.markdown(f"<div style='font-size: 12px; color: #38bdf8; margin-top: 8px;'>💡 <i>{day.notes}</i></div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # TAB 2: BUDGET BREAKDOWN
    # ------------------------------------------
    with tab_budget:
        st.markdown("### 📊 Budget Allocation & Guardrails")
        b = itin.budget_breakdown

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Budget", format_inr(b.budget))
        with col_m2:
            st.metric("Estimated Usage", format_inr(b.total))
        with col_m3:
            st.metric("Remaining Buffer", format_inr(b.remaining))
        with col_m4:
            st.metric("Utilization", f"{b.percentage_used}%")

        # Budget Progress Bar
        bar_color = "red" if b.overrun else ("orange" if b.is_warning else "green")
        st.progress(min(1.0, b.percentage_used / 100.0))

        if b.is_warning:
            st.warning(f"⚠️ Budget Warning: Usage is at {b.percentage_used}% of allocated funds (>= 90% threshold).")

        st.markdown("---")
        st.markdown("#### 🧾 Itemized Expense Breakdown:")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown(f"""
            - 🚆 **Intercity Transport (Round-Trip):** `{format_inr(b.transport)}`
            - 🏨 **Accommodation ({itin.trip.days - 1} Nights):** `{format_inr(b.stay)}`
            - 🍛 **Food & Dining Allowance:** `{format_inr(b.food)}`
            """)
        with col_b2:
            st.markdown(f"""
            - 🎟️ **Sightseeing & Monument Entry Tickets:** `{format_inr(b.activities)}`
            - 🚕 **Local Sightseeing Transit:** `{format_inr(b.local_travel)}`
            - 💧 **Miscellaneous & Convenience Buffer:** `{format_inr(b.miscellaneous)}`
            """)

    # ------------------------------------------
    # TAB 3: INTERACTIVE MAP
    # ------------------------------------------
    with tab_map:
        st.markdown("### 🗺️ Day-Wise Geocoded Route Map")
        st.caption("Color coded by day: 🔵 Day 1 (Blue), 🟢 Day 2 (Green), 🟣 Day 3 (Purple). Click pins for details.")

        folium_map = build_interactive_itinerary_map(itin)
        st_folium(folium_map, width="100%", height=480)

    # ------------------------------------------
    # TAB 4: AGENT TRACE PANEL
    # ------------------------------------------
    with tab_trace:
        st.markdown("### 🧠 Agent Execution & Tool Invocation Trace")
        st.caption("Live trace of reasoning steps, tool calls, and rule validations:")

        for t in st.session_state.trace:
            status_class = f"trace-item-{t.status}"
            tool_pill = f"<span class='badge-pill badge-primary' style='font-size: 11px; margin-left: 8px;'>🔧 {t.tool_called}</span>" if t.tool_called else ""
            st.markdown(f"""
            <div class="trace-item {status_class}">
                <div style="font-weight: 700; color: #f1f5f9; display: flex; align-items: center;">
                    <span style="font-size: 16px; margin-right: 6px;">{t.icon}</span>
                    <span>{t.step}</span>
                    {tool_pill}
                </div>
                <div style="color: #cbd5e1; margin-top: 3px; font-size: 12.5px;">{t.detail}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    # Default Welcome Screen
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 16px; padding: 36px; text-align: center; margin-top: 20px;">
        <div style="font-size: 48px; margin-bottom: 12px;">🧭 🇮🇳</div>
        <div style="font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">Welcome to TravelSaarthi!</div>
        <div style="font-size: 14px; color: #94a3b8; max-width: 580px; margin: 0 auto 20px auto; line-height: 1.6;">
            Your resilient, Indian family-aware travel agent. Type your trip query in the chat box above or click <b>✨ Demo Trip</b> in the left sidebar to see the live agentic planning and replanning engine in action.
        </div>
    </div>
    """, unsafe_allow_html=True)
