# TravelSaarthi (ट्रैवल सारथी) — Adaptive Travel Planning Agent

> **Bharat Agentic 2026 Hackathon**  
> **Track:** Mobility / Agentic AI  
> **Core Differentiator:** *"TravelSaarthi doesn't just plan a trip — it fixes the trip when things go wrong."*

---

## 🧭 Project Overview

**TravelSaarthi** is an intelligent, resilient, Indian-family-aware travel planning agent designed specifically for Indian domestic travel dynamics (railway schedules, pure-veg preferences, budget constraints, elder pacing, and sudden weather shifts).

Traditional travel generators produce static itineraries. If it rains, a train is delayed, the budget is cut, or family members tire, static plans collapse. **TravelSaarthi acts as an active agentic travel companion** that continuously validates and autonomously adapts itineraries in real-time.

```
                    STREAMLIT UI (Linear / Vercel Dark SaaS)
                                     |
                                     v
                           AGENT ORCHESTRATOR
                                     |
                             LLM + TOOL CALLING
                                     |
       -------------------------------------------------------------
       |              |              |              |              |
    Weather        Places        Transport         Stay        Validators
  (Open-Meteo)  (places.json) (transport.json)  (stay.json)    (10 Rules)
       |              |              |              |              |
       -------------------------------------------------------------
                                     |
                                     v
                        ADAPTIVE REPLANNING ENGINE
                      (Weather / Delays / Budget / Fatigue)
                                     |
                                     v
                                TRIP STATE
                     (Structured Pydantic + Diff Trace)
```

---

## 🌟 Key Features

1. **Native Hindi / Hinglish Natural Language Understanding:**
   - Understands colloquial inputs: *"3 din, ₹15,000, Delhi se Jaipur, family trip, 4 log"* or *"Day 2 ka weather kharab hai"*.
2. **Smart Minimal Clarification:**
   - Asks only critical missing questions (*"Khana veg hoga ya non-veg?", "Bachche ya elders saath hain?"*) and stops once sufficient context is known.
3. **Multi-Tool Research Pipeline:**
   - **Live Open-Meteo Weather API** with automatic offline fallback caching.
   - Curated dataset of 25+ heritage forts, museums, food stops, and cultural markets.
   - Ground-truth transport models (Vande Bharat, Shatabdi, Volvo, tourist autos/cabs).
   - Multi-tier stay estimation (Budget heritage havelis, standard boutique hotels).
4. **Resilient Adaptive Replanning Engine (The Differentiator):**
   - 🌧️ **Bad Weather:** Detects rain on Day 2, moves outdoor Amber Fort to sunny Day 3, inserts rich indoor cultural museums (City Palace / Albert Hall).
   - 🚆 **Train Delay:** Shifts Day 1 start times (+2 hours) and recalculates transit buffers.
   - 💰 **Budget Reductions:** Dynamically downgrades hotel/dining tiers and removes lowest-priority paid items to stay strictly under the new budget.
   - 😴 **Traveler Fatigue:** Implements Senior Care mode (caps activities to 2 leisurely spots with 3-hour afternoon rest breaks).
5. **Transparent "Agent Trace" Panel:**
   - Live visual audit log showing every reasoning step, tool call, and validation status.
6. **"Why did I change your plan?" Diff Visualizer:**
   - Explains before vs after changes in warm, accessible Hinglish and English.
7. **Interactive Leaflet/Folium Route Map:**
   - Day-wise color-coded route lines and markers with detailed popup cards.

---

## 📦 Project Structure

```
travelsaarthi/
│
├── app.py                      # Main Streamlit SaaS Application & Dashboard
├── models.py                   # Strongly typed Pydantic V2 Data Models
│
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py         # Intent parsing, clarification & multi-tool pipeline
│   ├── prompts.py              # System prompts & Hinglish guidance
│   └── replan.py               # Adaptive Replanning Engine for disruptions
│
├── tools/
│   ├── __init__.py
│   ├── weather.py              # Open-Meteo API + Cached fallback
│   ├── places.py               # Curated Jaipur places search & filtering
│   ├── transport.py            # Intercity & local transit calculator
│   ├── stay.py                 # Accommodation tier estimator
│   └── validators.py           # 10-point schedule & budget validator
│
├── data/
│   ├── places.json             # 25+ verified Jaipur destinations
│   ├── transport.json          # Train, bus, cab, and auto fares
│   └── stay.json               # Budget, standard & comfort stay options
│
├── cache/
│   └── weather.json            # Deterministic offline weather fallback
│
├── utils/
│   ├── __init__.py
│   ├── formatting.py           # INR currency, time, and UI badge helpers
│   └── helpers.py              # Folium map builder with day-wise polyline routes
│
├── test_travelsaarthi.py       # Comprehensive unit & end-to-end scenario test suite
├── requirements.txt            # Lightweight Python dependencies
├── .env.example                # Sample environment configuration
├── demo.md                     # Step-by-step 3-minute hackathon demo script
└── README.md                   # Full documentation
```

---

## 🛡️ 10 Validation Rules Enforced

1. **Total cost $\le$ allocated budget.**
2. **Early warning triggered when budget usage reaches $\ge 90\%$.**
3. **Relaxed / elderly travelers: maximum 3 activities per day.**
4. **Normal travelers: maximum 5 activities per day.**
5. **Transit time buffer (30–45 mins) strictly enforced between consecutive spots.**
6. **Activity opening and closing hours respected.**
7. **Outdoor venues forbidden on rain-flagged days.**
8. **Sufficient rest gaps and lunch windows for family comfort.**
9. **Zero overlapping activities permitted.**
10. **Every planned day must contain valid, non-empty schedules.**

---

## 🚀 Quickstart & Running Locally

### 1. Clone & Navigate
```bash
git clone https://github.com/your-repo/travelsaarthi.git
cd "travel saathi"
```

### 2. Create & Activate Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Run the Automated Test Suite
```bash
python test_travelsaarthi.py
```

### 5. Launch Options

#### Option A: Full-Fledged Modern Web Application (Recommended for Hackathon Demo)
```bash
python server.py
```
Open **`http://localhost:8080`** in your browser to access the full-fledged responsive SaaS dashboard with live Leaflet map routes, conversational Hinglish assistant, and instant scenario triggers.

#### Option B: Streamlit Application
```bash
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 Hackathon Demo Flow (3 Minutes)

1. **Generate Trip:** Click `✨ Demo Trip` in the sidebar or type:  
   `"3 din, ₹15,000, Delhi se Jaipur, family trip, 4 log"`
2. **Inspect Plan:** Review Day-Wise schedule, Budget breakdown (`₹13,200 / ₹15,000`), interactive Leaflet map, and live Agent Trace.
3. **Trigger Weather Disruption:** Click `🌧️ Bad Weather`.  
   *Observation:* Day 2 rain detected $\rightarrow$ Amber Fort moved to Day 3 $\rightarrow$ City Palace & Albert Hall Museums inserted for Day 2 $\rightarrow$ Hinglish explanation displayed.
4. **Trigger Budget Reduction:** Click `💰 Budget Cut`.  
   *Observation:* Budget cut from ₹15,000 to ₹13,000 $\rightarrow$ Accommodation and dining optimized $\rightarrow$ Total cost recalibrated safely below ₹13,000.
5. **Trigger Train Delay / Fatigue:** Click `🚆 Train Delay` or `😴 Traveler Fatigue` to demonstrate instant schedule re-alignment and senior care rest breaks.

---

## 📄 License
MIT License • Built for **Bharat Agentic 2026 Hackathon**.
