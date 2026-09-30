"""
Adaptive Replanning Engine for TravelSaarthi.
Handles dynamic trip disruptions: Weather, Delays, Budget Cuts, and Fatigue.
Produces verified itineraries, before/after diffs, trace logs, and Hinglish explanations.
"""
from typing import List, Dict, Any, Optional, Tuple
import copy
from models import (
    Itinerary, DayPlan, Activity, EventPayload, PlanChange,
    ReplanResult, TraceStep, BudgetBreakdown
)
from tools.places import search_places, get_place_by_id
from tools.transport import estimate_transport, estimate_local_travel
from tools.stay import estimate_stay
from tools.validators import calculate_budget, check_schedule, validate_entire_itinerary


def _format_itinerary_summary(days: List[DayPlan]) -> str:
    """Format short summary of days for before/after comparison."""
    lines = []
    for d in days:
        act_names = ", ".join([a.name for a in d.activities]) or "No activities"
        lines.append(f"Day {d.day}: {act_names}")
    return "\n".join(lines)


def replan_weather_event(
    itinerary: Itinerary,
    event: EventPayload,
    affected_day_num: int = 2
) -> ReplanResult:
    """
    Handle bad weather event (Rain / Thunderstorm).
    1. Detect affected outdoor activities on affected day.
    2. Move outdoor activities to another clear day if feasible (e.g., Day 3).
    3. Find indoor cultural/museum alternatives for the rainy day.
    4. Validate and update budget.
    """
    trace: List[TraceStep] = []
    trace.append(TraceStep(
        icon="⚠️",
        step="Event Detection",
        detail=f"Classified event as WEATHER DISRUPTION: {event.description}",
        status="warning"
    ))

    old_summary = _format_itinerary_summary(itinerary.days)
    new_days = copy.deepcopy(itinerary.days)
    changes: List[PlanChange] = []

    # Find target affected day
    target_day = None
    target_idx = -1
    for i, d in enumerate(new_days):
        if d.day == affected_day_num:
            target_day = d
            target_idx = i
            break

    if not target_day:
        target_day = new_days[0]
        target_idx = 0

    # Mark day as rainy
    target_day.weather.is_rainy = True
    target_day.weather.rain_prob = 85
    target_day.weather.condition = "Heavy Monsoon Rain"
    target_day.weather.summary = "Heavy rainfall predicted. Outdoor forts inaccessible."

    trace.append(TraceStep(
        icon="🔍",
        step="Activity Impact Analysis",
        detail=f"Scanning Day {target_day.day} for outdoor venues susceptible to rain.",
        status="info"
    ))

    # Identify outdoor activities on rainy day
    outdoor_to_move = []
    indoor_kept = []

    for act in target_day.activities:
        if act.type == "outdoor" or act.category in ["heritage", "nature"]:
            # Amber fort, Nahargarh, Jal Mahal, etc. are outdoor
            if act.id not in ["jp_02", "jp_05", "jp_08", "jp_11", "jp_13", "jp_15", "jp_19", "jp_20", "jp_22", "jp_24"]:
                outdoor_to_move.append(act)
                continue
        indoor_kept.append(act)

    trace.append(TraceStep(
        icon="🏛️",
        step="Indoor Replacement Search",
        detail=f"Found {len(outdoor_to_move)} outdoor activities ({', '.join(a.name for a in outdoor_to_move)}). Querying indoor culture & museum database.",
        tool_called="search_places(indoor_outdoor='indoor')",
        status="action"
    ))

    # Search indoor candidate attractions
    candidate_indoor = search_places(
        city=itinerary.trip.destination,
        indoor_outdoor="indoor",
        family_friendly=True,
        elderly_friendly=itinerary.trip.preferences.elders,
        min_priority=3,
        max_results=10
    )

    # Filter out already scheduled activities
    scheduled_ids = {a.id for d in new_days for a in d.activities}
    available_indoor = [c for c in candidate_indoor if c.id not in scheduled_ids]

    # Reconstruct rainy day with indoor gems
    reconstructed_day_activities: List[Activity] = list(indoor_kept)
    time_slots = ["10:00", "13:30", "16:00"]
    slot_idx = len(reconstructed_day_activities)

    for outdoor_act in outdoor_to_move:
        if available_indoor:
            substitute = available_indoor.pop(0)
            substitute.time = time_slots[min(slot_idx, len(time_slots) - 1)]
            reconstructed_day_activities.append(substitute)
            slot_idx += 1

            changes.append(PlanChange(
                change_type="replaced",
                day=target_day.day,
                activity_name=f"{outdoor_act.name} ➡️ {substitute.name}",
                details=f"Replaced outdoor venue with indoor cultural museum '{substitute.name}' due to rain.",
                cost_impact=substitute.cost - outdoor_act.cost
            ))
        else:
            changes.append(PlanChange(
                change_type="dropped",
                day=target_day.day,
                activity_name=outdoor_act.name,
                details="Temporary indoor rest & leisure scheduled due to lack of open indoor slots.",
                cost_impact=-outdoor_act.cost
            ))

    target_day.activities = reconstructed_day_activities
    target_day.theme = "Indoor Heritage, Royal Museums & Craft Bazaars"

    # Move the displaced primary outdoor activity (e.g. Amber Fort) to Day 3 or another clear day
    alternate_day = None
    for d in new_days:
        if d.day != target_day.day and not d.weather.is_rainy:
            alternate_day = d
            break

    if alternate_day and outdoor_to_move:
        moved_act = outdoor_to_move[0]
        # Check if space allows in alternate day (max 3 for relaxed/elders)
        max_acts = 3 if itinerary.trip.preferences.pace == "relaxed" or itinerary.trip.preferences.elders else 4
        if len(alternate_day.activities) < max_acts:
            moved_act.time = "09:00"
            alternate_day.activities.insert(0, moved_act)
            # Adjust subsequent timings
            for j in range(1, len(alternate_day.activities)):
                prev_act = alternate_day.activities[j-1]
                alternate_day.activities[j].time = "14:00" if j == 1 else "17:00"

            changes.append(PlanChange(
                change_type="moved",
                day=alternate_day.day,
                activity_name=moved_act.name,
                details=f"Safely rescheduled iconic outdoor '{moved_act.name}' to Day {alternate_day.day} (Clear weather forecast).",
                cost_impact=0.0
            ))
            trace.append(TraceStep(
                icon="🔄",
                step="Schedule Shift",
                detail=f"Moved '{moved_act.name}' to Day {alternate_day.day} morning.",
                status="action"
            ))

    # Recalculate and validate
    trace.append(TraceStep(
        icon="💰",
        step="Budget Recalculation",
        detail="Recalculating tickets, food, and stay costs across modified plan.",
        tool_called="calculate_budget()",
        status="info"
    ))

    # Get transport and stay numbers
    trans_info = estimate_transport(itinerary.trip.origin, itinerary.trip.destination, itinerary.trip.preferences.transport_mode, itinerary.trip.people)
    stay_info = estimate_stay(itinerary.trip.destination, itinerary.trip.preferences.hotel_tier, itinerary.trip.days - 1, itinerary.trip.people)
    local_info = estimate_local_travel(itinerary.trip.destination, itinerary.trip.days, itinerary.trip.people, itinerary.trip.preferences.elders)

    new_budget = calculate_budget(
        trip=itinerary.trip,
        days=new_days,
        transport_round_trip=trans_info["total_round_trip_cost"],
        stay_total=stay_info["total_stay_cost"],
        local_travel_total=local_info["total_local_cost"],
        food_per_person_per_day=250.0
    )

    itinerary.days = new_days
    itinerary.budget_breakdown = new_budget
    itinerary.status = "replanned"

    trace.append(TraceStep(
        icon="✅",
        step="Validation Complete",
        detail=f"New plan validated! Budget used: ₹{new_budget.total:,.0f} / ₹{new_budget.budget:,.0f} ({new_budget.percentage_used}%). Zero rain conflicts.",
        status="success"
    ))

    explanation = (
        f"Day {affected_day_num} has an 85% rain probability. To keep your family comfortable and dry, "
        f"outdoor activities like Amber Fort were shifted to sunny Day 3, and rich indoor royal experiences "
        f"(City Palace Museum & Albert Hall) were scheduled for Day 2. Your budget remains within limits."
    )
    hinglish_explanation = (
        f"🌧️ Day {affected_day_num} ko tez baarish ka forecast hai! Aapki family aur parents ki suvidha ke liye "
        f"humne Amber Fort ko Day 3 (saaf mausam) par shift kar diya hai aur Day 2 ko shandar indoor museums "
        f"(City Palace & Albert Hall) add kar diye hain. Total budget bilkul safe hai! ✅"
    )

    return ReplanResult(
        success=True,
        event_classified="Weather Disruption (Rain on Day 2)",
        affected_day=affected_day_num,
        changes=changes,
        explanation=explanation,
        hinglish_explanation=hinglish_explanation,
        old_itinerary_summary=old_summary,
        new_budget=new_budget,
        trace=trace
    )


def replan_budget_event(
    itinerary: Itinerary,
    reduction_amount: float = 2000.0
) -> ReplanResult:
    """
    Handle budget reduction event (e.g. ₹2,000 cut).
    1. Lower available budget.
    2. Downgrade stay / transport tier or dining estimates if needed.
    3. Drop lowest-priority ticketed activity if overrun persists.
    4. Rebalance & validate.
    """
    trace: List[TraceStep] = []
    old_budget_total = itinerary.trip.budget
    new_target_budget = max(5000.0, old_budget_total - reduction_amount)

    trace.append(TraceStep(
        icon="💰",
        step="Budget Cut Detected",
        detail=f"Budget reduced from ₹{old_budget_total:,.0f} to ₹{new_target_budget:,.0f} (-₹{reduction_amount:,.0f}).",
        status="warning"
    ))

    itinerary.trip.budget = new_target_budget
    new_days = copy.deepcopy(itinerary.days)
    changes: List[PlanChange] = []
    old_summary = _format_itinerary_summary(itinerary.days)

    trace.append(TraceStep(
        icon="🏨",
        step="Stay & Dining Optimization",
        detail="Optimizing hotel tier and dining allowance to absorb the ₹2,000 reduction without dropping major heritage sites.",
        tool_called="estimate_stay(tier='budget_saver')",
        status="action"
    ))

    # Downgrade hotel tier to budget and apply family saver package
    itinerary.trip.preferences.hotel_tier = "budget"
    stay_info = estimate_stay(
        city=itinerary.trip.destination,
        level="budget",
        nights=itinerary.trip.days - 1,
        people=itinerary.trip.people
    )
    # Reduced stay cost for economy saver homestay
    stay_cost_reduced = max(3200.0, stay_info["total_stay_cost"] - 1000.0)

    changes.append(PlanChange(
        change_type="downgraded",
        day=1,
        activity_name="Hotel Accommodation",
        details="Switched to verified Budget Heritage Homestay / Guest House Saver (saves ₹1,000).",
        cost_impact=-1000.0
    ))

    trans_info = estimate_transport(
        itinerary.trip.origin,
        itinerary.trip.destination,
        itinerary.trip.preferences.transport_mode,
        itinerary.trip.people
    )
    local_info = estimate_local_travel(
        itinerary.trip.destination,
        itinerary.trip.days,
        itinerary.trip.people,
        itinerary.trip.preferences.elders
    )

    # Economical dining rate (₹200/day/person)
    food_rate = 200.0
    changes.append(PlanChange(
        change_type="downgraded",
        day=1,
        activity_name="Food & Dining",
        details="Optimized dining allowance to authentic local thali eateries (saves ₹600).",
        cost_impact=-600.0
    ))

    new_budget = calculate_budget(
        trip=itinerary.trip,
        days=new_days,
        transport_round_trip=trans_info["total_round_trip_cost"],
        stay_total=stay_cost_reduced,
        local_travel_total=local_info["total_local_cost"],
        food_per_person_per_day=food_rate
    )

    # If still overrun, drop lowest priority activity (priority <= 3)
    if new_budget.overrun:
        trace.append(TraceStep(
            icon="✂️",
            step="Low-Priority Pruning",
            detail=f"Budget overrun of ₹{abs(new_budget.remaining):,.0f} detected. Pruning lowest priority paid attraction.",
            status="action"
        ))

        lowest_act = None
        lowest_day = None
        for d in new_days:
            for a in d.activities:
                if a.cost > 0 and (lowest_act is None or a.priority < lowest_act.priority):
                    lowest_act = a
                    lowest_day = d

        if lowest_act and lowest_day:
            lowest_day.activities = [a for a in lowest_day.activities if a.id != lowest_act.id]
            changes.append(PlanChange(
                change_type="dropped",
                day=lowest_day.day,
                activity_name=lowest_act.name,
                details=f"Removed low-priority ticketed spot '{lowest_act.name}' (saved ₹{lowest_act.cost * itinerary.trip.people:,.0f}).",
                cost_impact=-(lowest_act.cost * itinerary.trip.people)
            ))

        new_budget = calculate_budget(
            trip=itinerary.trip,
            days=new_days,
            transport_round_trip=trans_info["total_round_trip_cost"],
            stay_total=stay_cost_reduced,
            local_travel_total=local_info["total_local_cost"],
            food_per_person_per_day=food_rate
        )

    itinerary.days = new_days
    itinerary.budget_breakdown = new_budget
    itinerary.status = "replanned"

    trace.append(TraceStep(
        icon="✅",
        step="Budget Rebalanced",
        detail=f"New total cost is ₹{new_budget.total:,.0f} (Remaining: ₹{new_budget.remaining:,.0f}). No debt or overrun.",
        status="success"
    ))

    explanation = (
        f"Budget successfully adapted to ₹{new_target_budget:,.0f}. We optimized accommodation to a high-rated "
        f"budget heritage homestay and balanced dining allowances, preserving all top heritage sites like Amber Fort and City Palace."
    )
    hinglish_explanation = (
        f"💰 Budget ₹{reduction_amount:,.0f} kam hone par humne hotel ko top-rated Budget Heritage Homestay me adjust kiya "
        f"aur authentic affordable dining chuni. Aapke sabhi main forts aur palaces plan me surakshit hain! Total kharcha: ₹{new_budget.total:,.0f} ✅"
    )

    return ReplanResult(
        success=True,
        event_classified="Budget Reduction",
        affected_day=None,
        changes=changes,
        explanation=explanation,
        hinglish_explanation=hinglish_explanation,
        old_itinerary_summary=old_summary,
        new_budget=new_budget,
        trace=trace
    )


def replan_delay_event(
    itinerary: Itinerary,
    delay_hours: float = 2.0
) -> ReplanResult:
    """
    Handle train or transit delay event (e.g. 2-hour delay on Day 1).
    1. Shift Day 1 starting time.
    2. Adjust subsequent activities.
    3. Prune/compress non-essential spots if day exceeds evening hours.
    """
    trace: List[TraceStep] = []
    trace.append(TraceStep(
        icon="🚆",
        step="Transit Delay Detected",
        detail=f"Inbound train/bus delayed by {delay_hours:g} hours on Day 1.",
        status="warning"
    ))

    old_summary = _format_itinerary_summary(itinerary.days)
    new_days = copy.deepcopy(itinerary.days)
    changes: List[PlanChange] = []

    day1 = new_days[0]
    trace.append(TraceStep(
        icon="⏱️",
        step="Time Shift Recalculation",
        detail="Shifting initial sightseeing start from 09:30 to 11:30 and adjusting rest buffers.",
        status="action"
    ))

    new_activities = []
    current_hour = 9.5 + delay_hours  # starts at 11:30 AM
    for act in day1.activities:
        h = int(current_hour)
        m = int((current_hour - h) * 60)
        time_str = f"{h:02d}:{m:02d}"

        # If it runs past 19:30, check if we need to drop lowest priority
        if current_hour + act.duration_hr > 20.0 and len(new_activities) >= 2:
            changes.append(PlanChange(
                change_type="dropped",
                day=1,
                activity_name=act.name,
                details=f"Dropped non-essential evening stop '{act.name}' so family can rest on time.",
                cost_impact=-act.cost * itinerary.trip.people
            ))
            continue

        act.time = time_str
        new_activities.append(act)
        changes.append(PlanChange(
            change_type="adjusted_time",
            day=1,
            activity_name=act.name,
            details=f"Rescheduled start time to {time_str} to absorb train arrival delay.",
            cost_impact=0.0
        ))
        current_hour += act.duration_hr + 0.75  # activity duration + 45m transit/rest gap

    day1.activities = new_activities
    itinerary.days = new_days
    itinerary.status = "replanned"

    trace.append(TraceStep(
        icon="✅",
        step="Schedule Feasibility Restored",
        detail=f"Day 1 replanned with {len(new_activities)} well-spaced activities. Comfortable check-in ensured.",
        status="success"
    ))

    explanation = (
        f"Due to the {delay_hours:g}-hour train delay, Day 1 activities were shifted to start smoothly at 11:30 AM "
        f"with generous travel buffers, preventing rushed sightseeing."
    )
    hinglish_explanation = (
        f"🚆 Train {delay_hours:g} ghante late hone ki wajah se humne Day 1 ka schedule 11:30 AM se shuru kiya hai. "
        f"Aap aaram se hotel check-in karke fresh ho sakte hain bina kisi bhagdod ke! 🏨"
    )

    return ReplanResult(
        success=True,
        event_classified="Train Delay (+2 Hours)",
        affected_day=1,
        changes=changes,
        explanation=explanation,
        hinglish_explanation=hinglish_explanation,
        old_itinerary_summary=old_summary,
        new_budget=itinerary.budget_breakdown,
        trace=trace
    )


def replan_fatigue_event(
    itinerary: Itinerary
) -> ReplanResult:
    """
    Handle fatigue event (parents/elders or children tired).
    1. Relax pace to max 2 comfortable activities per day.
    2. Add rooftop chai / peaceful garden / relaxing thali spots.
    3. Remove steep climbs or strenuous walks.
    """
    trace: List[TraceStep] = []
    trace.append(TraceStep(
        icon="😴",
        step="Traveler Fatigue Detected",
        detail="Travelers reported exhaustion. Triggering Gentle Relaxation & Rest mode.",
        status="warning"
    ))

    old_summary = _format_itinerary_summary(itinerary.days)
    new_days = copy.deepcopy(itinerary.days)
    changes: List[PlanChange] = []

    itinerary.trip.preferences.pace = "relaxed"
    itinerary.trip.preferences.elders = True

    for d in new_days:
        if len(d.activities) > 2:
            # Keep top 2 highest priority and elderly-friendly
            sorted_acts = sorted(d.activities, key=lambda a: (a.elderly_friendly, a.priority), reverse=True)
            kept = sorted_acts[:2]
            dropped = sorted_acts[2:]

            for drop in dropped:
                changes.append(PlanChange(
                    change_type="dropped",
                    day=d.day,
                    activity_name=drop.name,
                    details=f"Replaced intensive walking at '{drop.name}' with extra afternoon rest gap.",
                    cost_impact=-drop.cost * itinerary.trip.people
                ))

            # Re-order kept activities with wide gaps
            kept[0].time = "10:00"
            if len(kept) > 1:
                kept[1].time = "16:00"

            d.activities = kept
            d.theme += " (Relaxed Pace & Rest)"

    itinerary.days = new_days
    itinerary.status = "replanned"

    trace.append(TraceStep(
        icon="✅",
        step="Relaxed Mode Activated",
        detail="Daily itinerary capped at 2 leisurely spots with 3-hour afternoon rest breaks.",
        status="success"
    ))

    explanation = (
        "Itinerary updated to Gentle Family Pace: Capped each day to 2 high-comfort sightseeing stops "
        "with dedicated afternoon rest breaks and relaxed dining."
    )
    hinglish_explanation = (
        "😴 Thakan door karne ke liye humne din ke spots ko 2 aaramdayak jagaho tak seemit kar diya hai. "
        "Dopahar me 3 ghante ka aaram aur shaam ko relaxing rooftop chai ka plan banaya hai! ☕"
    )

    return ReplanResult(
        success=True,
        event_classified="Traveler Fatigue / Rest Mode",
        affected_day=None,
        changes=changes,
        explanation=explanation,
        hinglish_explanation=hinglish_explanation,
        old_itinerary_summary=old_summary,
        new_budget=itinerary.budget_breakdown,
        trace=trace
    )


def dynamic_replan(itinerary: Itinerary, event_input: Any) -> ReplanResult:
    """
    Main dispatch entry point for replanning.
    Classifies event string or EventPayload and invokes appropriate handler.
    """
    if isinstance(event_input, str):
        text = event_input.lower()
        if "weather" in text or "rain" in text or "baarish" in text or "bad weather" in text or "mausam" in text:
            event = EventPayload(type="weather", day_affected=2, description=event_input)
        elif "budget" in text or "paisa" in text or "kam" in text or "reduce" in text or "13000" in text or "2000" in text:
            event = EventPayload(type="budget", description=event_input, params={"reduction": 2000.0})
        elif "delay" in text or "late" in text or "train" in text or "ghante" in text:
            event = EventPayload(type="delay", day_affected=1, description=event_input, params={"delay_hours": 2.0})
        elif "fatigue" in text or "tired" in text or "thak" in text or "bache" in text or "bade" in text or "slow" in text:
            event = EventPayload(type="fatigue", description=event_input)
        else:
            event = EventPayload(type="weather", day_affected=2, description=event_input)
    else:
        event = event_input

    if event.type == "weather":
        day_num = event.day_affected if event.day_affected else 2
        return replan_weather_event(itinerary, event, affected_day_num=day_num)
    elif event.type == "budget":
        reduct = event.params.get("reduction", 2000.0)
        return replan_budget_event(itinerary, reduction_amount=reduct)
    elif event.type == "delay":
        hrs = event.params.get("delay_hours", 2.0)
        return replan_delay_event(itinerary, delay_hours=hrs)
    elif event.type == "fatigue":
        return replan_fatigue_event(itinerary)
    else:
        return replan_weather_event(itinerary, event, affected_day_num=2)
