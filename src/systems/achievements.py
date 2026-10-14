from src.settings import MAX_LEVELS

ACHIEVEMENTS = [
    {"id": "first_steps", "name": "First Steps", "description": "Complete Level 1", "unlocked": False, "icon_color": (245, 190, 45)},
    {"id": "collector", "name": "Collector", "description": "Collect 50 items total", "unlocked": False, "icon_color": (70, 150, 235)},
    {"id": "no_damage", "name": "No Damage", "description": "Complete a level without taking damage", "unlocked": False, "icon_color": (90, 200, 110)},
    {"id": "speed_run", "name": "Speed Run", "description": "Complete a level in under 90 seconds", "unlocked": False, "icon_color": (175, 180, 185)},
    {"id": "all_stars", "name": "All Stars", "description": "Get 3 stars on all levels", "unlocked": False, "icon_color": (200, 90, 220)},
]


def default_state():
    return {a["id"]: False for a in ACHIEVEMENTS}


def evaluate(level, data):
    state = dict(default_state())
    state.update(data.get("achievements", {}))
    if level.level_number == 1:
        state["first_steps"] = True
    if data.get("total_collectibles", 0) >= 50:
        state["collector"] = True
    if not getattr(level, "damage_taken", False):
        state["no_damage"] = True
    if getattr(level, "elapsed_seconds", 9999) < 90:
        state["speed_run"] = True
    stars = data.get("level_stars", {})
    if all(int(stars.get(str(i), stars.get(i, 0))) >= 3 for i in range(1, MAX_LEVELS + 1)):
        state["all_stars"] = True
    return state
