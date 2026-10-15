import logging
import random

import pygame

from src import keybinds, user_settings
from src.settings import (
    WIDTH, HEIGHT, FPS, TITLE, SKY_BLUE, BLACK, FULLSCREEN, MAX_LEVELS, DEFAULT_DIFFICULTY,
)
from src.sound_manager import SoundManager
from src.world.level import Level
from src.ui.login_screen import LoginScreen
from src.ui.main_menu import MainMenu
from src.ui.difficulty_select import DifficultySelect
from src.ui.level_select import LevelSelect
from src.ui.pause_menu import PauseMenu
from src.ui.achievements import Achievements
from src.ui.win_screen import WinScreen
from src.ui.fail_screen import FailScreen
from src.ui.registration_screen import RegistrationScreen
from src.ui.settings_screen import SettingsScreen
from src.ui.controls_screen import ControlsScreen
from src.ui.credits_screen import CreditsScreen
from src.ui.theme import font as theme_font, WHITE
from src.systems.save_system import save_game, load_game, load_progress
from src.systems import session

DEBUG_SHOW_FPS = False

log = logging.getLogger("veggiequest.game")

# Results returned by the menu screens.
PLAY, ACHIEVEMENTS, SETTINGS, LOGOUT, QUIT, BACK = (
    "PLAY", "ACHIEVEMENTS", "SETTINGS", "LOGOUT", "QUIT", "BACK",
)
CONTROLS = "CONTROLS"


class Game:
    def __init__(self):
        pygame.init()
        prefs = user_settings.load()
        keybinds.load_from_settings(prefs)
        self._fullscreen = bool(FULLSCREEN or prefs["fullscreen"])
        display_flags = pygame.SCALED | pygame.DOUBLEBUF
        if self._fullscreen:
            display_flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), display_flags)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.running = True

        # Auth state - the game starts on the login screen, not the menu.
        self.logged_in = False
        self.show_create_account = False

        # In-game state (only relevant once logged_in is True)
        self.game_started = False
        self.difficulty_selected = False
        self.level_selected = False
        self.paused = False
        self.game_over = False
        self.victory_screen = False
        self.achievements_screen = False
        self.settings_open = False
        self.controls_open = False
        self.credits_open = False

        # Chosen on the difficulty screen and passed explicitly to every Level.
        self.difficulty = DEFAULT_DIFFICULTY

        # Screen shake / hit feedback.
        self.shake_frames = 0
        self._prev_flash = 0

        self.font = pygame.font.Font(None, 28)
        self.sound_manager = SoundManager()
        # A Level is only built once the player picks one (see _start_level).
        self.level = None

        self.login_screen = LoginScreen(self.screen)
        self.registration = RegistrationScreen(self.screen)
        self.menu = MainMenu(self.screen)
        self.difficulty_select = DifficultySelect(self.screen)
        self.level_select = LevelSelect(self.screen)
        self.pause_menu = PauseMenu(self.screen)
        self.achievements_menu = Achievements(self.screen)
        self.win_screen = WinScreen(self.screen)
        self.fail_screen = FailScreen(self.screen)
        self.settings_screen = SettingsScreen(
            self.screen, self.sound_manager, self.set_fullscreen, lambda: self._fullscreen
        )
        self.controls_screen = ControlsScreen(self.screen)
        self.credits_screen = CreditsScreen(self.screen)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _should_hide_cursor(self):
        """Hide the mouse cursor only while active gameplay is running."""
        return bool(
            self.logged_in
            and self.game_started
            and self.level_selected
            and self.level is not None
            and not self.paused
            and not self.game_over
            and not self.victory_screen
            and not self.settings_open
            and not self.controls_open
            and not self.credits_open
            and not self.achievements_screen
        )

    def _sync_cursor_visibility(self):
        pygame.mouse.set_visible(not self._should_hide_cursor())

    def set_fullscreen(self, enabled):
        if bool(enabled) != self._fullscreen:
            pygame.display.toggle_fullscreen()
            self._fullscreen = bool(enabled)

    def _start_level(self, level_number):
        self.level = Level(
            level_number=level_number,
            sound_manager=self.sound_manager,
            difficulty=self.difficulty,
        )
        self.level_selected = True
        self.shake_frames = 0
        self._prev_flash = 0

    def _autosave(self):
        """Save the current level's checkpoint (progress is also saved when
        a checkpoint is reached and when a level is completed)."""
        if self.level is None or not self.level_selected or not self.logged_in:
            return
        if self.victory_screen:
            return
        try:
            save_game(self.level)
        except Exception:
            log.exception("Autosave failed")

    def refresh_progress(self):
        """(Re)loads the CURRENTLY LOGGED-IN user's progress into the
        level select and achievements screens. Always resets first so a
        previous user's unlocks/achievements never leak into the next.
        Levels/stars are scoped to the currently selected difficulty, so
        each difficulty has its own independent 1-10 progression."""
        self.level_select.reset()
        self.achievements_menu.reset()
        data = load_progress(difficulty=self.difficulty)
        current = data.get("current", {})
        self.level_select.set_stars(current.get("level_stars", {}))
        for n in current.get("unlocked_levels", [1]):
            self.level_select.unlock_level(int(n))
        self.achievements_menu.set_state(data.get("achievements", {}))

    def _reset_game_state(self):
        """Resets all in-game screen flags. Called on login and logout so
        a fresh session always starts back at the main menu cleanly."""
        self.game_started = False
        self.difficulty_selected = False
        self.level_selected = False
        self.paused = False
        self.game_over = False
        self.victory_screen = False
        self.achievements_screen = False
        self.settings_open = False
        self.controls_open = False
        self.credits_open = False

    def _do_login(self):
        username = self.login_screen.username_field.value
        display_name = self.login_screen.display_name
        session.set_current_user(username, display_name)
        self.logged_in = True
        self._reset_game_state()
        self.refresh_progress()
        self.login_screen.reset()

    def _do_logout(self):
        self._autosave()
        session.logout()
        self.logged_in = False
        self.show_create_account = False
        self._reset_game_state()
        self.login_screen.reset()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.set_fullscreen(not self._fullscreen)
                prefs = user_settings.load()
                prefs["fullscreen"] = self._fullscreen
                user_settings.save(prefs)
                continue

            # ---------------- AUTH SCREENS ----------------
            if not self.logged_in:
                if self.show_create_account:
                    result = self.registration.handle_event(event)
                    if result == "BACK":
                        self.show_create_account = False
                    elif result == "CREATED":
                        created_username = self.registration.created_username
                        self.show_create_account = False
                        self.login_screen.reset(message="Account created successfully! Please log in.", message_ok=True)
                        self.login_screen.prefill_username(created_username)
                else:
                    result = self.login_screen.handle_event(event)
                    if result == "REGISTER":
                        self.registration.reset()
                        self.show_create_account = True
                    elif result == "LOGIN_SUCCESS":
                        self._do_login()
                    elif result == "QUIT":
                        self.running = False
                continue

            # ---------------- LOGGED-IN SCREENS ----------------
            if self.credits_open:
                if self.credits_screen.handle_event(event) == "DONE":
                    self._finish_credits()
                continue

            if self.controls_open:
                if self.controls_screen.handle_event(event) == BACK:
                    self.controls_open = False
                continue

            if self.settings_open:
                result = self.settings_screen.handle_event(event)
                if result == BACK:
                    self.settings_open = False
                elif result == CONTROLS:
                    self.controls_open = True
                continue

            if self.achievements_screen:
                result = self.achievements_menu.handle_event(event)
                if result == "BACK": self.achievements_screen = False
                continue

            if not self.game_started:
                if not self.difficulty_selected:
                    result = self.menu.handle_event(event)
                    if result == PLAY:
                        self.difficulty_selected = True
                    elif result == ACHIEVEMENTS:
                        self.refresh_progress()
                        self.achievements_screen = True
                    elif result == SETTINGS:
                        self.settings_open = True
                    elif result == LOGOUT:
                        self._do_logout()
                    elif result == QUIT:
                        self.running = False
                else:
                    result = self.difficulty_select.handle_event(event)
                    if result in ("easy", "normal", "hard"):
                        self.difficulty = result
                        self.difficulty_selected = False
                        self.game_started = True
                        self.level_selected = False
                        self.refresh_progress()
                        self.sound_manager.play_music()
                    elif result == BACK:
                        self.difficulty_selected = False
                continue

            if not self.level_selected:
                result = self.level_select.handle_event(event)
                if isinstance(result, int) and result > 0:
                    self._start_level(result)
                elif result == BACK:
                    self.game_started = False
                continue

            if self.game_over:
                result = self.fail_screen.handle_event(event)
                if result == "RETRY": self.restart_level()
                elif result == "MENU":
                    self.game_over = False
                    self.level_selected = False
                    self.game_started = False
                continue

            if self.victory_screen:
                result = self.win_screen.handle_event(event)
                if result == "NEXT":
                    next_level = self.level.level_number + 1
                    self.victory_screen = False
                    if next_level <= MAX_LEVELS:
                        self._start_level(next_level)
                    else:
                        # Beat the final level: roll the credits.
                        self.credits_screen.reset()
                        self.credits_open = True
                elif result == "MENU":
                    self.victory_screen = False
                    self.level_selected = False
                    self.game_started = False
                continue

            if self.paused:
                result = self.pause_menu.handle_event(event)
                if result == "RESUME": self.paused = False
                elif result == SETTINGS:
                    self.settings_open = True
                elif result == "MAIN MENU":
                    self._autosave()
                    self.paused = False
                    self.level_selected = False
                    self.game_started = False
                continue

            # Left (1) and right (3) mouse buttons attack. This is the ONLY
            # place an attack starts, so one click can never attack twice.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                self.level.player.start_attack()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.paused = True
                elif event.key == keybinds.get("interact"): self.level.interact_with_npc()
                elif event.key == keybinds.get("jump"):
                    if self.level.player.jump():
                        self.sound_manager.play("jump")
                        self.level.create_particles(self.level.player.rect.centerx, self.level.player.rect.bottom, (220, 220, 220), count=6)

    def _finish_credits(self):
        self.credits_open = False
        self.victory_screen = False
        self.level_selected = False
        self.game_started = False

    def update(self):
        if not self.logged_in:
            return
        if self.credits_open:
            self.credits_screen.update()
            if self.credits_screen.finished():
                self._finish_credits()
            return
        if self.settings_open or self.controls_open:
            return
        if self.victory_screen:
            self.win_screen.update()
            return
        if not self.game_started or not self.level_selected or self.game_over or self.paused:
            return
        self.level.update()

        # Hit feedback: screen shake on damage and a blink while invincible.
        player = self.level.player
        if player.damage_flash_timer > self._prev_flash:
            self.shake_frames = 10
        self._prev_flash = player.damage_flash_timer
        if self.shake_frames > 0:
            self.shake_frames -= 1
        player.invincible_blink = self.level.damage_cooldown > 0 and player.health > 0

        # Wait for the full death animation to finish (death_timer counts
        # back down to 0) before switching to the Fail screen. Without this,
        # the Fail screen popped up the instant health hit 0, cutting the
        # death animation off.
        if getattr(self.level, "fail_requested", False) and self.level.player.death_timer == 0:
            self.game_over = True
            return

        if self.level.level_complete:
            completed_level = self.level.level_number
            # star_rating / star_breakdown are computed in Level itself
            # (see _compute_star_breakdown) from the actual objectives:
            # all enemies killed, no enemy hits, all coins collected,
            # finished within the time limit.
            save_game(self.level, unlock_next=True, completed=True)
            self.refresh_progress()
            self.win_screen.set_result(
                completed_level,
                self.level.score,
                self.level.star_rating,
                self.level.star_breakdown,
            )
            self.victory_screen = True

    def _draw_tutorial(self):
        """Short hints along the start of level 1."""
        if self.level.level_number != 1:
            return
        x = self.level.player.rect.x
        left, right, jump = (keybinds.key_name(a) for a in ("left", "right", "jump"))
        interact = keybinds.key_name("interact")
        if x < 700:
            text = f"Move: {left} / {right} or arrow keys     Jump: {jump}"
        elif x < 1600:
            text = "Attack: left or right mouse button"
        elif x < 2600:
            text = f"Press {interact} to talk to characters     Walk into a checkpoint to save"
        else:
            return
        label = theme_font(26, True).render(text, True, WHITE)
        box = label.get_rect(center=(WIDTH // 2, HEIGHT - 40)).inflate(30, 14)
        shade = pygame.Surface(box.size, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        self.screen.blit(shade, box.topleft)
        self.screen.blit(label, label.get_rect(center=box.center))

    def _apply_shake(self):
        if self.shake_frames <= 0 or self.paused:
            return
        mag = max(1, min(6, self.shake_frames))
        snapshot = self.screen.copy()
        self.screen.fill(BLACK)
        self.screen.blit(snapshot, (random.randint(-mag, mag), random.randint(-mag, mag)))

    def draw(self):
        self._sync_cursor_visibility()
        if not self.logged_in:
            if self.show_create_account:
                self.registration.draw()
            else:
                self.login_screen.draw()
            pygame.display.flip()
            return
        if self.credits_open:
            self.credits_screen.draw()
            pygame.display.flip()
            return
        if self.controls_open:
            self.controls_screen.draw()
            pygame.display.flip()
            return
        if self.settings_open:
            self.settings_screen.draw()
            pygame.display.flip()
            return
        if self.achievements_screen:
            self.achievements_menu.draw()
            pygame.display.flip()
            return
        if not self.game_started:
            if self.difficulty_selected: self.difficulty_select.draw()
            else: self.menu.draw()
            pygame.display.flip()
            return
        if not self.level_selected:
            self.level_select.draw()
            pygame.display.flip()
            return
        if self.victory_screen:
            self.win_screen.draw()
            pygame.display.flip()
            return
        self.screen.fill(SKY_BLUE)
        self.level.draw(self.screen)
        self._draw_tutorial()
        self._apply_shake()
        if DEBUG_SHOW_FPS:
            fps = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, BLACK)
            self.screen.blit(fps, (10, 10))
        if self.paused: self.pause_menu.draw()
        if self.game_over: self.fail_screen.draw()
        pygame.display.flip()

    def restart_level(self):
        self._start_level(self.level.level_number)
        self.game_over = False
        self.victory_screen = False
        self.paused = False

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        self._autosave()
        self.sound_manager.stop_music()
        pygame.quit()
