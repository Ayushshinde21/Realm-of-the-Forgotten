"""Regression tests for the Easy-only Level 5 / Level 10 boss arenas."""
import pytest

pygame = pytest.importorskip("pygame")

from src.world.level import Level
from src.world.level_data import LEVELS


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    yield
    pygame.quit()


def _new_level(number, difficulty="easy", seed=81273):
    return Level(seed=seed, level_number=number, difficulty=difficulty)


def test_easy_level_5_is_a_single_orc_boss_arena():
    level = _new_level(5)
    assert level.is_boss_level
    assert level.boss_kind == "orc"
    assert level.level_name == "Orc Boss Fight"
    assert level.width == 1050
    assert level.world_width == 1050
    assert len(level.platforms) == 5
    assert level.platforms[0] is level.ground
    assert len(level.platforms[1:]) == 4
    assert len(level.enemies) == 1
    assert level.enemies[0] is level.boss
    assert level.boss.variant in {"orc_berserk", "orc_shaman", "orc_warrior"}
    assert level.boss.max_hit_points in {10, 15, 20}
    assert level.boss.rect.height == 165
    assert level.player.jump_strength == pytest.approx(-17.0)
    assert not level.checkpoints
    assert not level.collectibles
    assert not level.moving_platforms
    assert not level.pits


def test_easy_level_10_is_a_single_yokai_boss_arena():
    level = _new_level(10)
    assert level.is_boss_level
    assert level.boss_kind == "yokai"
    assert level.level_name == "Yokai Boss Fight"
    assert level.width == 1050
    assert level.world_width == 1050
    assert len(level.platforms) == 5
    assert level.platforms[0] is level.ground
    assert len(level.platforms[1:]) == 4
    assert len(level.enemies) == 1
    assert level.enemies[0] is level.boss
    assert level.boss.variant in {"karasu_tengu", "kitsune", "yamabushi_tengu"}
    assert level.boss.max_hit_points in {32, 35, 38}
    assert level.boss.max_hit_points > 25
    assert level.boss.rect.height == 205
    assert level.player.jump_strength == pytest.approx(-17.0)
    assert not level.checkpoints
    assert not level.collectibles
    assert not level.moving_platforms
    assert not level.pits


@pytest.mark.parametrize("number", [5, 10])
def test_boss_floor_has_side_platforms_clear_of_the_boss(number):
    level = _new_level(number)
    boss = level.boss
    elevated = level.platforms[1:]

    assert level.width == 1050
    assert len(elevated) == 4
    assert all(platform.rect.height == 24 for platform in elevated)
    assert all(platform.rect.top < level.ground.rect.top for platform in elevated)

    platforms = sorted(elevated, key=lambda platform: platform.rect.left)
    assert [platform.rect.left for platform in platforms] == [20, 260, 700, 950]
    assert platforms[1].rect.left - platforms[0].rect.right == 160
    assert platforms[3].rect.left - platforms[2].rect.right == 160
    assert platforms[1].rect.right < platforms[2].rect.left
    assert abs(platforms[0].rect.top - platforms[1].rect.top) == 140

    for facing in (-1, 1):
        boss.facing = facing
        for x in (
            boss.left_limit + boss.body_rect.width / 2,
            boss.right_limit - boss.body_rect.width / 2,
        ):
            boss.pos_x = x
            boss._sync_position()
            assert all(not platform.rect.colliderect(boss.body_rect) for platform in elevated)
            assert all(not platform.rect.colliderect(boss.rect) for platform in elevated)

    assert level.player.rect.left >= 100
    assert level.player.rect.centerx < boss.body_rect.centerx
    assert not level.collectibles
    assert not level.checkpoints
    assert not level.moving_platforms
    assert not level.pits
    assert len(level.enemies) == 1
    assert level.enemies[0] is boss


def test_boss_hp_decreases_once_per_attack_id_and_defeat_completes_level():
    level = _new_level(5, seed=12345)
    boss = level.boss
    initial_hp = boss.hit_points

    boss.take_hit(9001)
    assert boss.hit_points == initial_hp - 1
    boss.take_hit(9001)
    assert boss.hit_points == initial_hp - 1

    next_attack_id = 9002
    while boss.alive:
        boss.take_hit(next_attack_id)
        next_attack_id += 1

    for _ in range(500):
        boss.update(None, level)
        if boss.finished_dying:
            break

    assert boss.finished_dying
    level.check_level_completion()
    assert level.level_complete


@pytest.mark.parametrize("difficulty", ["normal", "hard"])
@pytest.mark.parametrize("number", [5, 10])
def test_boss_levels_do_not_change_normal_or_hard(difficulty, number):
    level = _new_level(number, difficulty=difficulty, seed=81273)
    assert not level.is_boss_level
    assert level.boss is None
    assert level.level_name != "Orc Boss Fight"
    assert level.level_name != "Yokai Boss Fight"
    assert level.world_width == LEVELS[difficulty][number]["world_width"]
    assert level.player.jump_strength == pytest.approx(-14)
    assert len(level.platforms) > 1


def test_player_update_supports_custom_width_for_boss_arenas():
    import inspect
    from src.entities.player import Player

    assert "world_width" in inspect.signature(Player.update).parameters
    source = inspect.getsource(Player.update)
    assert "movement_world_width = WORLD_WIDTH if world_width is None else int(world_width)" in source


def _new_boss(variant="orc_berserk", kind="orc", center_x=1500):
    from src.entities.boss import Boss

    return Boss(
        boss_kind=kind,
        variant=variant,
        center_x=center_x,
        floor_y=600,
        left_limit=140,
        right_limit=2860,
        hit_points=20,
        target_height=165 if kind == "orc" else 205,
    )


def _dummy_player(rect):
    from types import SimpleNamespace

    return SimpleNamespace(rect=rect)


def test_boss_facing_does_not_flicker_when_player_is_overhead():
    boss = _new_boss()
    boss.facing = 1
    boss.direction = 1
    boss._sync_position()
    player_rect = pygame.Rect(boss.body_rect.centerx - 25, boss.body_rect.centery - 300, 50, 80)
    player = _dummy_player(player_rect)

    for _ in range(20):
        player.rect.centerx = boss.body_rect.centerx
        boss.update(player)
        assert boss.facing == 1
        assert boss.direction == 1


def test_boss_float_position_uses_configured_speed_without_rounding():
    boss = _new_boss(center_x=1200)
    player = _dummy_player(pygame.Rect(2000, boss.body_rect.top, 50, 80))
    before = boss.pos_x

    boss.update(player)

    assert boss.state == "run"
    assert boss.pos_x - before == pytest.approx(boss.speed)
    assert boss.speed > 5
    assert abs(boss.body_rect.centerx - boss.pos_x) <= 1


def test_boss_facing_is_locked_while_attack_animation_runs():
    boss = _new_boss()
    boss.facing = 1
    boss.direction = 1
    boss.state = "attack"
    boss._set_animation("attack")
    boss._sync_position()
    player = _dummy_player(pygame.Rect(boss.body_rect.centerx - 500, boss.body_rect.top, 50, 80))

    boss.update(player)

    assert boss.state == "attack"
    assert boss.facing == 1
    assert boss.direction == 1


def test_boss_attack_finishes_and_cooldown_prevents_instant_reattack():
    boss = _new_boss()
    boss.state = "attack"
    boss._set_animation("attack")
    player = _dummy_player(pygame.Rect(2500, boss.body_rect.top, 50, 80))

    boss.update(player)
    assert boss.state == "attack"

    for _ in range(len(boss.anims["attack"]) * boss.anim_speed + 2):
        boss.update(player)
        if boss.state != "attack":
            break

    assert boss.state == "idle"
    assert boss.attack_cooldown_timer == boss.attack_cooldown_max
    boss.update(player)
    assert boss.state == "run"


def test_boss_uses_tight_body_hitbox_and_keeps_it_anchored_when_flipped():
    boss = _new_boss(variant="kitsune", kind="yokai")
    original_center = boss.body_rect.centerx

    assert boss.body_rect.width < boss.rect.width
    boss.facing = 1
    boss._sync_position()
    facing_right_center = boss.body_rect.centerx
    boss.facing = -1
    boss._sync_position()

    assert abs(facing_right_center - original_center) <= 1
    assert abs(boss.body_rect.centerx - original_center) <= 1
    assert boss.rect.bottom == boss.floor_y


def test_variant_hit_frames_and_final_animation_frame_timing():
    boss = _new_boss(variant="kitsune", kind="yokai")
    assert boss.hit_frame == 6
    boss._set_animation("attack")
    frame_count = len(boss.anims["attack"])
    ticks = 0

    while not boss._advance(loop=False):
        ticks += 1
        assert ticks < frame_count * boss.anim_speed + 1
    ticks += 1

    assert ticks == frame_count * boss.anim_speed
    assert boss.anim_frame == frame_count - 1


def test_boss_speeds_are_reduced_but_still_exceed_player_run_speed():
    orc = _new_boss(variant="orc_berserk", kind="orc")
    yokai = _new_boss(variant="karasu_tengu", kind="yokai")

    assert orc.speed == pytest.approx(5.1)
    assert yokai.speed == pytest.approx(5.7)
    assert 5 < orc.speed < yokai.speed


def test_boss_floor_jump_has_more_airtime_and_range_than_regular_jump():
    from src.settings import PLAYER_GRAVITY, PLAYER_JUMP_STRENGTH, PLAYER_SPEED

    level = _new_level(5)
    boss_jump = abs(level.player.jump_strength)
    regular_airtime = 2 * abs(PLAYER_JUMP_STRENGTH) / PLAYER_GRAVITY
    boss_airtime = 2 * boss_jump / PLAYER_GRAVITY

    assert boss_jump > abs(PLAYER_JUMP_STRENGTH)
    assert boss_airtime > regular_airtime
    assert PLAYER_SPEED * boss_airtime > PLAYER_SPEED * regular_airtime


def test_level_attack_collision_paths_use_boss_body_rect():
    import inspect

    player_attack_source = inspect.getsource(Level.handle_player_attack)
    enemy_attack_source = inspect.getsource(Level.handle_enemy_attack)

    assert 'getattr(enemy, "body_rect", enemy.rect)' in player_attack_source
    assert 'getattr(enemy, "body_rect", enemy.rect)' in enemy_attack_source
    assert "enemy_body.right" in enemy_attack_source
    assert "enemy_body.left" in enemy_attack_source

@pytest.mark.parametrize(
    ("kind", "expected_range", "expected_vertical_range"),
    [("orc", 42, 72), ("yokai", 48, 80)],
)
def test_boss_damage_hitbox_is_shorter_than_player_sword_reach(
    kind, expected_range, expected_vertical_range
):
    boss = _new_boss(variant="orc_berserk" if kind == "orc" else "karasu_tengu", kind=kind)

    assert boss.attack_range == expected_range
    assert boss.attack_vertical_range == expected_vertical_range
    assert boss.attack_range + 6 < 62
    assert boss.attack_vertical_range < 100


def test_boss_attack_event_uses_the_reduced_hitbox():
    boss = _new_boss()
    boss.facing = 1
    boss.state = "attack"
    boss._set_animation("attack")
    boss._sync_position()
    player = _dummy_player(
        pygame.Rect(boss.body_rect.right + 12, boss.floor_y - 80, 50, 80)
    )

    attack = None
    for _ in range((boss.hit_frame + 2) * boss.anim_speed + 2):
        boss.update(player)
        if boss.pending_attack is not None:
            attack = boss.pending_attack
            break

    assert attack is not None
    assert attack["range"] == 42
    assert attack["vertical_range"] == 72

