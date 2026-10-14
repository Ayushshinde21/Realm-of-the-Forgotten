import pygame
from src.ui.theme import draw_background, draw_wood_panel, draw_button, font, WHITE, YELLOW, SILVER
from src.ui.widgets import TextField
from src.systems.account_system import register_account

FIELD_COUNT = 3
BUTTON_LABELS = ["CREATE ACCOUNT", "BACK"]


class RegistrationScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.panel = pygame.Rect((self.width - 460) // 2, 15, 460, 490)
        self.close_rect = pygame.Rect(self.panel.right - 44, self.panel.top + 14, 30, 30)

        left = self.panel.left + 45
        field_w = self.panel.width - 90
        top = self.panel.top + 150

        self.username_field = TextField("username", "Username", (left, top, field_w, 44))
        self.password_field = TextField("password", "Password", (left, top + 62, field_w, 44), password=True)
        self.confirm_field = TextField("confirm", "Confirm Password", (left, top + 124, field_w, 44), password=True)
        self.fields = [self.username_field, self.password_field, self.confirm_field]

        self.focused = 0
        self.message = ""
        self.message_ok = False
        self.created_username = None

    def button_rects(self):
        top = self.confirm_field.rect.bottom + 30
        return [pygame.Rect(self.panel.left + 45, top + i * 58, self.panel.width - 90, 46) for i in range(len(BUTTON_LABELS))]

    def reset(self):
        for f in self.fields:
            f.value = ""
        self.focused = 0
        self.message = ""
        self.message_ok = False
        self.created_username = None

    def _move_focus(self, delta):
        total = FIELD_COUNT + len(BUTTON_LABELS)
        self.focused = (self.focused + delta) % total

    def _activate_button(self, index):
        label = BUTTON_LABELS[index]
        if label == "CREATE ACCOUNT":
            return self._try_create()
        if label == "BACK":
            return "BACK"
        return None

    def _try_create(self):
        ok, msg = register_account(
            self.username_field.value, self.password_field.value, self.confirm_field.value
        )
        self.message, self.message_ok = msg, ok
        if ok:
            self.created_username = self.username_field.value.strip()
            return "CREATED"
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "BACK"
            if event.key == pygame.K_TAB:
                self._move_focus(1)
                return None
            if self.focused < FIELD_COUNT:
                if event.key == pygame.K_UP:
                    self._move_focus(-1)
                elif event.key == pygame.K_DOWN:
                    self._move_focus(1)
                elif event.key == pygame.K_RETURN:
                    return self._try_create()
                else:
                    self.fields[self.focused].handle_key(event)
            else:
                button_index = self.focused - FIELD_COUNT
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._move_focus(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_focus(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return self._activate_button(button_index)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                return "BACK"
            for i, f in enumerate(self.fields):
                if f.rect.collidepoint(event.pos):
                    self.focused = i
                    return None
            for i, rect in enumerate(self.button_rects()):
                if rect.collidepoint(event.pos):
                    self.focused = FIELD_COUNT + i
                    return self._activate_button(i)
        return None

    def draw(self):
        draw_background(self.screen)
        draw_wood_panel(self.screen, self.panel, "CREATE ACCOUNT")

        # Close button
        pygame.draw.circle(self.screen, (35, 25, 18), self.close_rect.center, 16)
        pygame.draw.circle(self.screen, SILVER, self.close_rect.center, 16, 2)
        cx, cy = self.close_rect.center
        pygame.draw.line(self.screen, WHITE, (cx - 7, cy - 7), (cx + 7, cy + 7), 2)
        pygame.draw.line(self.screen, WHITE, (cx - 7, cy + 7), (cx + 7, cy - 7), 2)

        for i, f in enumerate(self.fields):
            f.draw(self.screen, i == self.focused)

        for i, (label, rect) in enumerate(zip(BUTTON_LABELS, self.button_rects())):
            draw_button(self.screen, rect, label, selected=(self.focused == FIELD_COUNT + i))

        if self.message:
            color = (120, 220, 120) if self.message_ok else (240, 110, 100)
            msg_s = font(16, True).render(self.message, True, color)
            self.screen.blit(msg_s, msg_s.get_rect(center=(self.width // 2, self.panel.bottom - 14)))

        hint = font(14, True).render("TAB / ARROWS Navigate     ENTER / SPACE Select     ESC Back", True, YELLOW)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.panel.bottom + 20)))
