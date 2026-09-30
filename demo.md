# 🎯 TravelSaarthi — 3-Minute Hackathon Demo Script

### Event: Bharat Agentic 2026
### Track: Mobility / Agentic AI

---

## 🎬 Stage 1: The Hook (30 seconds)
> *"Namaste judges! Most AI travel apps generate a static PDF itinerary that becomes useless the moment real life happens in India — when monsoon rain starts, a train gets delayed by 2 hours, or someone in the family gets exhausted.*
>
> *Meet **TravelSaarthi** — an adaptive agentic travel companion. Our motto: **We don't just plan a trip, we fix it when things go wrong!**"*

---

## 🚀 Stage 2: Initial Plan Synthesis (45 seconds)

1. Click **`✨ Demo Trip`** in the left sidebar (or type in Hindi/Hinglish in the chat box):
   > *"3 din, ₹15,000, Delhi se Jaipur, family trip, 4 log."*

2. **Highlight the UI & Agent Trace:**
   - **Agent Trace Tab:** Show the live execution pipeline:
     - 🧠 Understands family dynamics & elderly travelers
     - 🌦️ Fetches live Open-Meteo weather
     - 🚆 Estimates Vande Bharat / Shatabdi round-trip fares (₹2,000)
     - 🏨 Selects top-rated Budget Heritage Homestay (₹4,500)
     - 🍛 Reserves authentic vegetarian food budget (₹3,000)
     - 🎟️ Calculates monument entry tickets (₹2,200)
     - 🚕 Dedicated local auto/cab pass (₹1,500)
   - **Budget Dashboard:** Total **₹13,200 / ₹15,000** (88% utilized, ₹1,800 buffer).
   - **Map:** Point out day-colored markers and connecting route lines.

---

## 🌧️ Stage 3: The First Disruption — Bad Weather (45 seconds)

1. Click **`🌧️ Bad Weather`** in the sidebar (or type *"Day 2 ko baarish hogi"*).
2. **Show the Diff Banner & Hinglish Explanation:**
   - **Why Changed Banner:**
     > *"🌧️ Day 2 ko tez baarish ka forecast hai! Aapki family aur parents ki suvidha ke liye humne Amber Fort ko Day 3 (saaf mausam) par shift kar diya hai aur Day 2 ko shandar indoor museums (City Palace & Albert Hall) add kar diye hain. Total budget bilkul safe hai! ✅"*
   - **Diff Breakdown:**
     - Day 2: Outdoor Amber Fort moved $\rightarrow$ Indoor City Palace & Albert Hall added.
     - Day 3: Clear weather $\rightarrow$ Amber Fort safely accommodated.
   - **Rule Compliance:** Zero rain conflicts, zero schedule overlaps.

---

## 💰 Stage 4: The Second Disruption — Budget Reduction (30 seconds)

1. Click **`💰 Budget Cut`** in the sidebar (or type *"Budget ₹2,000 kam ho gaya"*).
2. **Show Dynamic Financial Rebalancing:**
   - New Target Budget: **₹13,000** (reduced from ₹15,000).
   - **Agent Actions:**
     - Optimizes stay to economy saver tier (saves ₹1,000).
     - Adjusts dining allowance to local authentic thalis (saves ₹600).
     - New Total: **₹11,600**, remaining **₹1,400**.
     - Keeps Amber Fort and City Palace intact without breaking the budget!

---

## 🚆 Stage 5: Train Delays & Traveler Fatigue (30 seconds)

1. Click **`🚆 Train Delay`**:
   - Day 1 sightseeing smoothly shifts from 09:30 to 11:30 AM without family rushing.
2. Click **`😴 Traveler Fatigue`**:
   - Activates Senior Care mode $\rightarrow$ caps day to 2 leisurely spots with 3-hour afternoon rest gaps.

---

## 🏆 Key Takeaways for Judges
1. **Real Agentic Behavior:** Multi-step tool calls, constraint solvers, and autonomous replanning loops.
2. **Bharat-Centric Design:** Built from the ground up for Indian family nuances, train schedules, and pure-veg requirements.
3. **Resilient Architecture:** Real Open-Meteo API with deterministic cache fallback — zero crashes during live demos.
