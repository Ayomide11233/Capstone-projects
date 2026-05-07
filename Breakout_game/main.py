import pygame
import math
import random
import sys

# ── window
W, H = 480, 560
FPS  = 60

# ── colours
BG      = (15,  15,  19)
PADDLE  = (200, 198, 190)
BALL_C  = (245, 243, 237)
TEXT_C  = (200, 198, 190)
DIM_C   = (120, 118, 112)
ROW_COLS = [
    (212,  83, 126),   # pink
    (216,  90,  48),   # coral
    (186, 117,  23),   # amber
    ( 55, 139, 221),   # blue
    ( 29, 158, 117),   # teal
    ( 83,  74, 183),   # purple
]
ROW_DARK = [
    (153,  37,  78),
    (153,  60,  29),
    (133,  80,  11),
    ( 24,  95, 165),
    ( 15, 110,  86),
    ( 60,  52, 137),
]

# ── layout
COLS_N, ROWS_N = 10, 6
BW, BH, BGAP   = 40, 16, 2
BOFF_X = (W - (COLS_N * (BW + BGAP) - BGAP)) // 2
BOFF_Y = 60
PW, PH = 72, 10
BALL_R = 7
PADDLE_Y = H - 50


class Brick:
    def __init__(self, col, row, hp):
        self.col   = col
        self.row   = row
        self.hp    = hp
        self.max_hp = hp
        self.alive = True

    @property
    def rect(self):
        x = BOFF_X + self.col * (BW + BGAP)
        y = BOFF_Y + self.row * (BH + BGAP)
        return pygame.Rect(x, y, BW, BH)

    def color(self):
        return ROW_DARK[self.row] if self.hp < self.max_hp else ROW_COLS[self.row]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Breakout")
        self.clock  = pygame.font.SysFont(None, 20)
        self.font_m = pygame.font.SysFont(None, 28)
        self.font_l = pygame.font.SysFont(None, 40)
        self.tk     = pygame.time.Clock()
        self.level  = 1
        self.score  = 0
        self.lives  = 3
        self.reset_level()

    # ── set up ball and bricks for current level
    def reset_level(self):
        self.px = W // 2 - PW // 2          # paddle x
        speed   = 3.5 + self.level * 0.4
        angle   = -math.pi / 2 + (random.random() - 0.5) * 0.6
        self.bx  = float(W // 2)            # ball x
        self.by  = float(PADDLE_Y - BALL_R - 2)  # ball y
        self.vx  = math.cos(angle) * speed
        self.vy  = math.sin(angle) * speed
        self.bricks   = self._make_bricks()
        self.launched = False
        self.over     = False
        self.won      = False
        self.message  = "Press SPACE or click to launch"

    def _make_bricks(self):
        bricks = []
        for r in range(ROWS_N):
            for c in range(COLS_N):
                hp = 2 if (self.level >= 2 and r < 2) else 1
                bricks.append(Brick(c, r, hp))
        return bricks

    # ── AABB circle collision
    # Returns ('x'|'y', push) or None
    def _ball_vs_rect(self, rect):
        near_x = max(rect.left, min(self.bx, rect.right))
        near_y = max(rect.top,  min(self.by, rect.bottom))
        dx = self.bx - near_x
        dy = self.by - near_y
        if dx*dx + dy*dy > BALL_R * BALL_R:
            return None
        ox = (rect.left - self.bx - BALL_R) if self.bx < rect.centerx else (rect.right - self.bx + BALL_R)
        oy = (rect.top  - self.by - BALL_R) if self.by < rect.centery else (rect.bottom - self.by + BALL_R)
        if abs(ox) < abs(oy):
            return ('x', ox)
        return ('y', oy)

    def update(self):
        if not self.launched or self.over:
            return

        self.bx += self.vx
        self.by += self.vy

        # wall bounces
        if self.bx - BALL_R < 0:
            self.bx = BALL_R;  self.vx = abs(self.vx)
        if self.bx + BALL_R > W:
            self.bx = W - BALL_R; self.vx = -abs(self.vx)
        if self.by - BALL_R < 0:
            self.by = BALL_R;  self.vy = abs(self.vy)

        # ball lost
        if self.by > H + 20:
            self.lives -= 1
            if self.lives <= 0:
                self.over = True
                self.message = f"Game over!  Score: {self.score}"
                return
            self.launched = False
            self.bx = self.px + PW / 2
            self.by = PADDLE_Y - BALL_R - 2
            speed = 3.5 + self.level * 0.4
            angle = -math.pi / 2 + (random.random() - 0.5) * 0.6
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.message = "Press SPACE or click to continue"
            return

        # paddle collision — angle steered by hit position
        paddle_rect = pygame.Rect(self.px, PADDLE_Y, PW, PH)
        hit = self._ball_vs_rect(paddle_rect)
        if hit and self.vy > 0:
            axis, _ = hit
            if axis == 'y':
                hit_pos = (self.bx - (self.px + PW / 2)) / (PW / 2)  # -1..1
                speed   = math.hypot(self.vx, self.vy)
                angle   = hit_pos * (math.pi / 3)
                self.vx = math.sin(angle) * speed
                self.vy = -abs(math.cos(angle) * speed)
            else:
                self.vx *= -1

        # brick collisions
        alive = 0
        for b in self.bricks:
            if not b.alive:
                continue
            alive += 1
            hit = self._ball_vs_rect(b.rect)
            if not hit:
                continue
            b.hp -= 1
            if b.hp <= 0:
                b.alive = False
                alive  -= 1
                self.score += (b.row + 1) * 10 * self.level
            axis, _ = hit
            if axis == 'x':
                self.vx *= -1
            else:
                self.vy *= -1
            break  # one brick per frame

        if alive == 0:
            self._next_level()

    def _next_level(self):
        self.level += 1
        self.reset_level()
        self.message = f"Level {self.level}!  Press SPACE or click to launch"

    # ── draw
    def draw(self):
        self.screen.fill(BG)

        # bricks
        for b in self.bricks:
            if not b.alive:
                continue
            r = b.rect
            pygame.draw.rect(self.screen, b.color(), r, border_radius=3)
            if b.max_hp > 1:
                surf = self.clock.render(str(b.hp), True, (255,255,255,80))
                self.screen.blit(surf, (r.centerx - surf.get_width()//2, r.bottom - surf.get_height() - 1))

        # paddle
        pygame.draw.rect(self.screen, PADDLE,
                         (self.px, PADDLE_Y, PW, PH), border_radius=PH//2)

        # ball
        pygame.draw.circle(self.screen, BALL_C,
                           (int(self.bx), int(self.by)), BALL_R)

        # guide dash when not launched
        if not self.launched:
            for i in range(0, 50, 10):
                pygame.draw.line(self.screen, DIM_C,
                                 (int(self.bx), int(self.by) - i),
                                 (int(self.bx), int(self.by) - i - 5), 1)

        # HUD
        hud = self.font_m.render(
            f"Score: {self.score}    Level: {self.level}    Lives: {self.lives}",
            True, TEXT_C)
        self.screen.blit(hud, (W//2 - hud.get_width()//2, 16))

        # message
        if self.message:
            surf = self.font_m.render(self.message, True, TEXT_C)
            self.screen.blit(surf, (W//2 - surf.get_width()//2, H - 24))

        # game-over overlay
        if self.over:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))
            msg  = self.font_l.render(self.message, True, TEXT_C)
            sub  = self.font_m.render("Press R to play again  |  ESC to quit", True, DIM_C)
            self.screen.blit(msg, (W//2 - msg.get_width()//2, H//2 - 30))
            self.screen.blit(sub, (W//2 - sub.get_width()//2, H//2 + 20))

        pygame.display.flip()

    # ── main loop
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_SPACE:
                        if self.over:
                            self.score = 0; self.lives = 3; self.level = 1
                            self.reset_level()
                        else:
                            self.launched = True
                            self.message  = ""
                    if event.key == pygame.K_r and self.over:
                        self.score = 0; self.lives = 3; self.level = 1
                        self.reset_level()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.over:
                        self.score = 0; self.lives = 3; self.level = 1
                        self.reset_level()
                    else:
                        self.launched = True
                        self.message  = ""

            # paddle follows mouse
            mx, _ = pygame.mouse.get_pos()
            if not self.over:
                self.px = max(0, min(W - PW, mx - PW // 2))
                if not self.launched:
                    self.bx = self.px + PW / 2

            self.update()
            self.draw()
            self.tk.tick(FPS)


if __name__ == "__main__":
    Game().run()