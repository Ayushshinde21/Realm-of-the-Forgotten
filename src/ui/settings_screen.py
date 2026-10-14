"""Settings: music volume, sound volume, fullscreen toggle, link to controls."""
from __future__ import annotations

import pygame

from src import user_settings
from src.ui.theme import (
    draw_background, draw_wood_panel, draw_button, font,
    WHITE, YELLOW, WOOD_DARK, SILVER, ORANGE, ORANGE_LIGHT,
)

STEP = 0.1
ROWS = ["MUSIC", "SOUND", "FULLSCREEN", "CONTROLS", "BACK"]


class SettingsScreen:
    def __init__(self, screen, sound_manager, set_fullscreen, is_fullscreen):
        """`set_fullscreen(bool)` / `is_fullscreen()` are supplied by Game so
        this screen never touches the display directly."""
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.sound_manager = sound_manager
        self.set_fullscreen = set_fullscreen
        self.is_fullscreen = is_fullscreen
        self.panel = pygame.Rect(190, 30, 580, 480)
        self.selected = 0
        self._dragging = None  # "MUSIC" / "SOUND" while the mouse drags a slider

    # ---------------- layout ----------------

    def row_rect(self, index):
        return pygame.Rect(240, 135 + index * 66, 480, 52)

    def slider_track(self, index):
        r = self.row_rect(index)
        return pygame.Rect(r.left + 190, r.centery - 5, r.width - 215, 10)

    # ---------------- values ----------------

    def _get(self, name):
        return self.sound_manager.music_volume if name == "MUSIC" else self.sound_manager.sound_volume

    def _set(self, name, value):
        value = max(0.0, min(1.0, round(value, 3)))
        if name == "MUSIC":
            self.sound_manager.set_music_volume(value)
        else:
            self.sound_manager.set_sound_volume(value)
            self.sound_manager.play("collect")  # audible preview
        self._persist()

    def _persist(self):
        data = user_settings.load()
        data["music_volume"] = self.sound_manager.music_volume
        data["sound_volume"] = self.sound_manager.sound_volume
        data["fullscreen"] = self.is_fullscreen()
        user_settings.save(data)

    def _toggle_fullscreen(self):
        self.set_fullscreen(not self.is_fullscreen())
        self._persist()

    # ---------------- events ----------------

    def _activate(self, name):
        if name == "FULLSCREEN":
            self._toggle_fullscreen()
        elif name == "CONTROLS":
            return "CONTROLS"
        elif name == "BACK":
            return "BACK"
        return None

    def _value_from_mouse(self, index, x):
        track = self.slider_track(index)
        return (x - track.left) / max(1, track.width)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            name = ROWS[self.selected]
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(ROWS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(ROWS)
            elif event.key in (pygame.K_LEFT, pygame.K_a) and name in ("MUSIC", "SOUND"):
                self._set(name, self._get(name) - STEP)
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and name in ("MUSIC", "SOUND"):
                self._set(name, self._get(name) + STEP)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._activate(name)
            elif event.key == pygame.K_ESCAPE:
                return "BACK"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, name in enumerate(ROWS):
                if not self.row_rect(i).collidepoint(event.pos):
                    continue
                self.selected = i
                if name in ("MUSIC", "SOUND"):
                    self._dragging = name
                    self._set(name, self._value_from_mouse(i, event.pos[0]))
                else:
                    return self._activate(name)
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            i = ROWS.index(self._dragging)
            self._set(self._dragging, self._value_from_mouse(i, event.pos[0]))
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = None
        return None

    # ---------------- drawing ----------------

    def _draw_slider(self, index, label, value):
        rect = self.row_rect(index)
        selected = index == self.selected
        pygame.draw.rect(self.screen, ORANGE if selected else WOOD_DARK, rect, border_radius=10)
        text = font(28, True).render(label, True, WHITE)
        self.screen.blit(text, (rect.left + 16, rect.centery - text.get_height() // 2))
        track = self.slider_track(index)
        pygame.draw.rect(self.screen, (30, 22, 16), track, border_radius=5)
        fill = track.copy()
        fill.width = int(track.width * value)
        pygame.draw.rect(self.screen, YELLOW, fill, border_radius=5)
        knob_x = track.left + int(track.width * value)
        pygame.draw.circle(self.screen, WHITE, (knob_x, track.centery), 11)
        pygame.draw.circle(self.screen, SILVER, (knob_x, track.centery), 11, 2)
        pct = font(22, True).render(f"{int(round(value * 100))}%", True, WHITE)
        self.screen.blit(pct, (rect.right - pct.get_width() - 6, rect.top + 2))

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "SETTINGS")
        self._draw_slider(0, "Music", self.sound_manager.music_volume)
        self._draw_slider(1, "Sound", self.sound_manager.sound_volume)
        draw_button(
            self.screen, self.row_rect(2),
            f"FULLSCREEN: {'ON' if self.is_fullscreen() else 'OFF'}",
            self.selected == 2, small=True,
        )
        draw_button(self.screen, self.row_rect(3), "CONTROLS", self.selected == 3, small=True)
        draw_button(self.screen, self.row_rect(4), "BACK", self.selected == 4, small=True)
        hint = font(18, True).render(
            "UP / DOWN Select    LEFT / RIGHT Adjust    ENTER Choose    ESC Back", True, YELLOW
        )
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, 495)))
