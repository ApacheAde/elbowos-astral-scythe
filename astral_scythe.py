#!/usr/bin/env python3
"""ASTRAL SCYTHE — neon orbital-harvest arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/ASTRAL_SCYTHE_ElbowOS.mp4")
TITLE, HANDLE = "ASTRAL SCYTHE", "x.com/ElbowOS"

VOID = (8, 4, 22)
INK = (18, 8, 42)
AMBER = (255, 176, 36)
GOLD = (255, 220, 110)
TEAL = (40, 230, 210)
MAG = (255, 70, 170)
VIO = (160, 90, 255)
ICE = (200, 230, 255)
WHITE = (250, 248, 255)
ROSE = (255, 80, 90)
LIME = (150, 255, 90)

CX, CY = W // 2, 980
CORE_R = 54


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        self.font_lg = pygame.font.SysFont("DejaVu Sans", 58, bold=True)
        self.font = pygame.font.SysFont("DejaVu Sans", 38, bold=True)
        self.font_sm = pygame.font.SysFont("DejaVu Sans", 26)
        self.clock = pygame.time.Clock()
        self.score = self.combo = self.best = self.t = 0
        self.flash = self.banner = 0
        self.ang = -math.pi / 2
        self.omega = 0.085
        self.rad = 240
        self.slash = 0
        self.sparks, self.rings, self.shards = [], [], []
        self.stars = [[random.randint(0, W), random.randint(0, H),
                       random.uniform(0.4, 1.8), random.choice([VIO, TEAL, MAG, GOLD])]
                      for _ in range(70)]
        for _ in range(8):
            self.spawn_shard()

    def spawn_shard(self):
        kind = random.choices(["ore", "ore", "ore", "thorn"], [4, 4, 4, 2])[0]
        col = ROSE if kind == "thorn" else random.choice([TEAL, GOLD, MAG, VIO])
        ang = random.uniform(0, 6.2832)
        dist = random.uniform(320, 620)
        self.shards.append({
            "x": CX + math.cos(ang) * dist, "y": CY + math.sin(ang) * dist * 0.92,
            "vx": random.uniform(-1.6, 1.6), "vy": random.uniform(-1.2, 1.8),
            "r": random.randint(16, 28), "col": col, "kind": kind,
            "spin": random.uniform(-0.12, 0.12), "a": random.uniform(0, 6.28),
        })

    def burst(self, x, y, col, n=12):
        for _ in range(n):
            a = random.uniform(0, 6.2832)
            sp = random.uniform(2, 12)
            self.sparks.append([x, y, math.cos(a) * sp, math.sin(a) * sp, 16, col])

    def blade(self):
        extra = 70 if self.slash else 0
        r = self.rad + extra
        bx = CX + math.cos(self.ang) * r
        by = CY + math.sin(self.ang) * r
        return bx, by, 38 + extra * 0.18

    def autoplay(self):
        if not self.shards:
            return
        bx, by, _ = self.blade()
        best, target = 1e9, None
        for s in self.shards:
            if s["kind"] == "thorn":
                continue
            d = math.hypot(s["x"] - CX, s["y"] - CY)
            if abs(d - self.rad) < 220:
                dist = math.hypot(s["x"] - bx, s["y"] - by)
                if dist < best:
                    best, target = dist, s
        if target is None:
            target = min(self.shards, key=lambda s: math.hypot(s["x"] - bx, s["y"] - by))
        want = math.atan2(target["y"] - CY, target["x"] - CX)
        diff = (want - self.ang + math.pi) % (2 * math.pi) - math.pi
        self.omega = max(-0.16, min(0.16, diff * 0.18))
        want_r = math.hypot(target["x"] - CX, target["y"] - CY)
        self.rad += max(-10, min(10, (want_r - self.rad) * 0.12))
        self.rad = max(150, min(430, self.rad))
        if best < 140 and target["kind"] != "thorn":
            self.slash = 8

    def tick(self):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.banner = max(0, self.banner - 1)
        self.slash = max(0, self.slash - 1)
        self.ang += self.omega
        self.rad += math.sin(self.t * 0.07) * 0.35
        bx, by, br = self.blade()
        if self.t % 38 == 0 and len(self.shards) < 14:
            self.spawn_shard()
        keep = []
        for s in self.shards:
            s["a"] += s["spin"]
            dx, dy = CX - s["x"], CY - s["y"]
            d = math.hypot(dx, dy) or 1
            pull = 0.085 if d > 90 else -0.4
            s["vx"] += dx / d * pull
            s["vy"] += dy / d * pull + 0.04
            s["vx"] += -dy / d * 0.05
            s["vy"] += dx / d * 0.05
            s["vx"] *= 0.985
            s["vy"] *= 0.985
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            if s["x"] < 40 or s["x"] > W - 40:
                s["vx"] *= -0.8
            if s["y"] < 220 or s["y"] > H - 220:
                s["vy"] *= -0.8
            hit = math.hypot(s["x"] - bx, s["y"] - by) < br + s["r"]
            if hit:
                if s["kind"] == "thorn":
                    self.combo = 0
                    self.score = max(0, self.score - 8)
                    self.burst(s["x"], s["y"], ROSE, 16)
                    self.rings.append([s["x"], s["y"], 6, ROSE])
                    self.flash = 6
                else:
                    self.combo += 1
                    self.best = max(self.best, self.combo)
                    self.score += 10 + self.combo * 2
                    self.burst(s["x"], s["y"], s["col"], 18)
                    self.rings.append([s["x"], s["y"], 8, s["col"]])
                    self.banner = 8
                    self.flash = 4
                continue
            if d < CORE_R + s["r"]:
                self.burst(s["x"], s["y"], GOLD if s["kind"] != "thorn" else ROSE, 8)
                continue
            keep.append(s)
        self.shards = keep
        for sp in self.sparks:
            sp[0] += sp[2]; sp[1] += sp[3]; sp[4] -= 1
        self.sparks = [sp for sp in self.sparks if sp[4] > 0]
        for r in self.rings:
            r[2] += 9
        self.rings = [r for r in self.rings if r[2] < 180]
        for e in self.stars:
            e[1] -= e[2]
            if e[1] < -6:
                e[1] = H + 6
                e[0] = random.randint(0, W)

    def draw(self, surf):
        surf.fill(VOID)
        for e in self.stars:
            pygame.draw.circle(surf, e[3], (int(e[0]), int(e[1])), 2)
        for i, rad in enumerate((160, 250, 340, 430)):
            col = (28 + i * 8, 16, 64 + i * 12)
            pygame.draw.circle(surf, col, (CX, CY), rad, 2)
        pulse = 6 * math.sin(self.t * 0.15)
        pygame.draw.circle(surf, INK, (CX, CY), int(CORE_R + 16 + pulse))
        pygame.draw.circle(surf, AMBER, (CX, CY), int(CORE_R + pulse * 0.4))
        pygame.draw.circle(surf, GOLD, (CX - 10, CY - 12), 16)
        pygame.draw.circle(surf, WHITE, (CX, CY), int(CORE_R + pulse * 0.4), 3)
        pygame.draw.circle(surf, (80, 50, 140), (CX, CY), int(self.rad), 2)
        bx, by, br = self.blade()
        pygame.draw.line(surf, VIO, (CX, CY), (bx, by), 6)
        pygame.draw.circle(surf, AMBER if self.slash else TEAL, (int(bx), int(by)), int(br))
        pygame.draw.circle(surf, WHITE, (int(bx - 8), int(by - 10)), max(6, int(br * 0.28)))
        pygame.draw.circle(surf, GOLD, (int(bx), int(by)), int(br), 3)
        for s in self.shards:
            pts = []
            n = 3 if s["kind"] == "thorn" else 5
            for k in range(n):
                a = s["a"] + k * (6.2832 / n)
                rr = s["r"] if k % 2 == 0 else s["r"] * 0.55
                pts.append((s["x"] + math.cos(a) * rr, s["y"] + math.sin(a) * rr))
            pygame.draw.polygon(surf, s["col"], pts)
            pygame.draw.polygon(surf, WHITE, pts, 2)
        for r in self.rings:
            pygame.draw.circle(surf, r[3], (int(r[0]), int(r[1])), int(r[2]), 3)
        for sp in self.sparks:
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(2, sp[4] // 4))
        if self.flash:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((255, 176, 36, 28) if self.combo else (255, 80, 90, 32))
            surf.blit(ov, (0, 0))
        if self.banner:
            lab = self.font.render("REAP", True, GOLD)
            surf.blit(lab, lab.get_rect(center=(W // 2, 210)))
        title = self.font_lg.render(TITLE, True, AMBER)
        surf.blit(title, title.get_rect(center=(W // 2, 78)))
        sub = self.font_sm.render(HANDLE, True, MAG)
        surf.blit(sub, sub.get_rect(center=(W // 2, 138)))
        sc = self.font.render(f"SCORE  {self.score}", True, WHITE)
        cb = self.font_sm.render(f"COMBO  x{self.combo}   BEST  {self.best}", True, TEAL)
        hint = self.font_sm.render("A/D orbit   W/S radius   SPACE slash", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W // 2, H - 150)))
        surf.blit(cb, cb.get_rect(center=(W // 2, H - 96)))
        surf.blit(hint, hint.get_rect(center=(W // 2, H - 48)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_j):
                    self.slash = 8
            keys = pygame.key.get_pressed()
            self.omega = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.omega = -0.12
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.omega = 0.12
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.rad = min(430, self.rad + 8)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.rad = max(150, self.rad - 8)
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
                if i % 30 == 0:
                    print(f"frame {i}/{frames}", flush=True)
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()


if __name__ == "__main__":
    main()
