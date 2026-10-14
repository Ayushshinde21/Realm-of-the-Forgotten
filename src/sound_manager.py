import logging
import os

import pygame

from src import user_settings

log = logging.getLogger("veggiequest.sound")


class SoundManager:
    """Loads sounds and music. Every call is safe when there is no audio
    device or a file is missing - the game simply runs without sound."""

    def __init__(self):
        self.sounds = {}
        prefs = user_settings.load()
        self.music_volume = prefs["music_volume"]
        self.sound_volume = prefs["sound_volume"]

        self.audio_ok = bool(pygame.mixer.get_init())
        if not self.audio_ok:
            try:
                pygame.mixer.init()
                self.audio_ok = True
            except pygame.error:
                log.warning("No audio device available - running without sound")
                return

        sound_folder = os.path.join("assets", "sounds")
        sound_files = {
            "jump": "jump.wav",
            "collect": "collect.wav",
            "checkpoint": "checkpoint.wav",
            "damage": "damage.wav",
            "stomp": "stomp.wav",
            "death": "death.wav",
        }
        for name, filename in sound_files.items():
            path = os.path.join(sound_folder, filename)
            if not os.path.exists(path):
                log.info("Sound file missing, skipping: %s", path)
                continue
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(self.sound_volume)
                self.sounds[name] = snd
            except pygame.error:
                log.exception("Could not load sound %s", path)

    # ---------------- volume ----------------

    def set_sound_volume(self, volume):
        self.sound_volume = max(0.0, min(1.0, volume))
        for snd in self.sounds.values():
            snd.set_volume(self.sound_volume)

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        if not self.audio_ok:
            return
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except pygame.error:
            log.exception("Could not set music volume")

    # ---------------- playback ----------------

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def play_music(self):
        if not self.audio_ok:
            return
        music_path = os.path.join("assets", "music", "background.mp3")
        if not os.path.exists(music_path):
            return
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            log.exception("Music unavailable - continuing without it")

    def stop_music(self):
        if not self.audio_ok:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
