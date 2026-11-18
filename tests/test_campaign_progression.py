from src.settings import MAX_LEVELS, WORLD_LEVEL_COUNT, WORLD_NAMES
from src.world.level_data import LEVELS, campaign_progress, world_for_level


def test_campaign_contains_two_named_worlds_and_twenty_global_levels():
    assert MAX_LEVELS == 20
    assert WORLD_LEVEL_COUNT == 10
    assert WORLD_NAMES == {
        1: "Snackland Meadows",
        2: "Greenwild Frontier",
    }
    assert tuple(LEVELS["easy"]) == tuple(range(1, 11))
    assert tuple(LEVELS["normal"]) == tuple(range(1, 11))


def test_global_level_number_automatically_selects_its_world_profile():
    assert world_for_level(1) == (1, 1, "easy")
    assert world_for_level(10) == (1, 10, "easy")
    assert world_for_level(11) == (2, 1, "normal")
    assert world_for_level(20) == (2, 10, "normal")
    assert world_for_level(21) == world_for_level(20)


def test_difficulty_ramp_increases_continuously_across_the_campaign():
    values = [campaign_progress(level) for level in range(1, MAX_LEVELS + 1)]
    assert values[0] == 0.0
    assert values[-1] == 1.0
    assert all(left < right for left, right in zip(values, values[1:]))
