"""
Comprehensive Test Suite for TravelSaarthi.
Tests 5+ end-to-end demo flows, tools, validators, and replanning scenarios.
"""
import unittest
from models import TripRequest, UserPreferences, EventPayload
from agent.orchestrator import TravelSaarthiOrchestrator
from tools.weather import get_weather
from tools.places import search_places
from tools.transport import estimate_transport, estimate_local_travel
from tools.stay import estimate_stay
from tools.validators import validate_entire_itinerary, calculate_budget


class TestTravelSaarthi(unittest.TestCase):

    def setUp(self):
        self.orchestrator = TravelSaarthiOrchestrator()
        self.sample_trip = TripRequest(
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

    def test_01_hinglish_intent_parsing(self):
        """Test Hinglish natural language parsing and parameter extraction."""
        query = "3 din, ₹15,000, Delhi se Jaipur, family trip, 4 log."
        trip, missing, clar = self.orchestrator.parse_user_input(query)

        self.assertEqual(trip.days, 3)
        self.assertEqual(trip.budget, 15000.0)
        self.assertEqual(trip.origin, "Delhi")
        self.assertEqual(trip.destination, "Jaipur")
        self.assertEqual(trip.people, 4)
        self.assertEqual(trip.trip_type, "family")
        self.assertTrue(trip.preferences.elders)

    def test_02_tools_execution(self):
        """Verify all underlying tools execute and return valid structures."""
        # Weather
        weather = get_weather("Jaipur", 3)
        self.assertEqual(len(weather), 3)

        # Places
        places = search_places("Jaipur", family_friendly=True)
        self.assertGreater(len(places), 5)

        # Transport
        trans = estimate_transport("Delhi", "Jaipur", "train", 4)
        self.assertGreater(trans["total_round_trip_cost"], 0)

        # Stay
        stay = estimate_stay("Jaipur", "budget", 2, 4)
        self.assertEqual(stay["rooms_needed"], 2)
        self.assertGreater(stay["total_stay_cost"], 0)

    def test_03_initial_itinerary_generation(self):
        """Verify initial plan synthesis, budget constraint, and validator."""
        itin, trace = self.orchestrator.generate_itinerary(self.sample_trip)

        self.assertEqual(len(itin.days), 3)
        self.assertEqual(itin.status, "valid")
        self.assertFalse(itin.budget_breakdown.overrun)
        self.assertLessEqual(itin.budget_breakdown.total, 15000.0)
        self.assertGreater(len(trace), 5)

        is_valid, issues = validate_entire_itinerary(itin)
        self.assertTrue(is_valid, f"Validation failed with issues: {issues}")

    def test_04_weather_replanning(self):
        """Verify Day 2 Rain event replaces outdoor Amber Fort with indoor museums."""
        itin, _ = self.orchestrator.generate_itinerary(self.sample_trip)
        event = EventPayload(type="weather", day_affected=2, description="Day 2 ka weather kharab hai.")

        result = self.orchestrator.handle_replan_event(itin, event)

        self.assertTrue(result.success)
        self.assertIn("Weather", result.event_classified)
        self.assertGreater(len(result.changes), 0)
        self.assertIn("Amber Fort", str(result.changes))

        # Ensure Day 2 no longer contains rain conflicts
        day2 = [d for d in itin.days if d.day == 2][0]
        self.assertTrue(day2.weather.is_rainy)
        for act in day2.activities:
            # Indoor cultural venues allowed
            self.assertIn(act.type, ["indoor", "heritage", "food", "museum"])

    def test_05_budget_reduction_replanning(self):
        """Verify budget cut from ₹15,000 to ₹13,000 stays within guardrails."""
        itin, _ = self.orchestrator.generate_itinerary(self.sample_trip)
        event = EventPayload(type="budget", description="Budget ₹2,000 kam ho gaya.", params={"reduction": 2000.0})

        result = self.orchestrator.handle_replan_event(itin, event)

        self.assertTrue(result.success)
        self.assertEqual(itin.trip.budget, 13000.0)
        self.assertFalse(itin.budget_breakdown.overrun)
        self.assertLessEqual(itin.budget_breakdown.total, 13000.0)

    def test_06_train_delay_replanning(self):
        """Verify 2-hour train delay shifts Day 1 start time smoothly."""
        itin, _ = self.orchestrator.generate_itinerary(self.sample_trip)
        event = EventPayload(type="delay", day_affected=1, description="Train 2 ghante late hai.", params={"delay_hours": 2.0})

        result = self.orchestrator.handle_replan_event(itin, event)

        self.assertTrue(result.success)
        day1 = [d for d in itin.days if d.day == 1][0]
        self.assertEqual(day1.activities[0].time, "11:30")

    def test_07_traveler_fatigue_replanning(self):
        """Verify fatigue triggers relaxed pace with max 2 spots per day."""
        itin, _ = self.orchestrator.generate_itinerary(self.sample_trip)
        event = EventPayload(type="fatigue", description="Parents thak gaye hain.")

        result = self.orchestrator.handle_replan_event(itin, event)

        self.assertTrue(result.success)
        for d in itin.days:
            self.assertLessEqual(len(d.activities), 2)


if __name__ == "__main__":
    unittest.main()
