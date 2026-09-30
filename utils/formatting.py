"""
Formatting and UI presentation helpers for TravelSaarthi.
"""

def format_inr(amount: float) -> str:
    """Format numeric float/int into Indian Rupee style string (e.g. ₹15,000)."""
    try:
        val = int(amount)
        s = str(val)
        if len(s) <= 3:
            return f"₹{s}"
        last3 = s[-3:]
        other = s[:-3]
        groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:])
            other = other[:-2]
        if other:
            groups.insert(0, other)
        return f"₹{','.join(groups)},{last3}"
    except Exception:
        return f"₹{amount:,.0f}"


def get_category_icon(category: str, act_type: str = "outdoor") -> str:
    """Return an intuitive icon for activities."""
    cat = category.lower()
    if "heritage" in cat or "fort" in cat or "palace" in cat:
        return "🏰"
    elif "museum" in cat or "gallery" in cat:
        return "🏛️"
    elif "food" in cat or "restaurant" in cat or "cafe" in cat:
        return "🍛"
    elif "shopping" in cat or "market" in cat or "bazaar" in cat:
        return "🛍️"
    elif "spiritual" in cat or "temple" in cat:
        return "🛕"
    elif "nature" in cat or "lake" in cat or "garden" in cat:
        return "🌿"
    elif "entertainment" in cat or "wax" in cat:
        return "🎭"
    elif act_type == "indoor":
        return "🏢"
    return "📍"


def get_weather_icon(condition: str) -> str:
    """Return weather emoji based on condition text."""
    c = condition.lower()
    if "rain" in c or "shower" in c or "monsoon" in c:
        return "🌧️"
    elif "thunder" in c or "storm" in c:
        return "⛈️"
    elif "cloud" in c:
        return "⛅"
    elif "clear" in c or "sun" in c:
        return "☀️"
    return "🌤️"
