import asyncio
import json
import math
import random
import sys
import threading
import time

from functools import lru_cache
from pathlib import Path

import pygame

# Fix relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------
# BACKEND 54D INTEGRATION (ASYNC BRIDGE)
# ---------------------------------------------------------
try:
    from Cosmos.core.quantum_bridge import QuantumEntanglementBridge
    q_bridge = QuantumEntanglementBridge()
    Q_AVAILABLE = True
except Exception as e:
    print(f"Warning: Quantum Bridge not loaded properly. {e}")
    q_bridge = None
    Q_AVAILABLE = False

try:
    from Cosmos.web.server import get_cosmos_swarm
    # Note: CosmosSwarmOrchestrator now has a .chat() method as a proxy.
    swarm_engine = get_cosmos_swarm()
    SWARM_AVAILABLE = True
except Exception as e:
    print(f"Warning: 54D Swarm engine not loaded. Will fallback to Ollama. {e}")
    swarm_engine = None
    SWARM_AVAILABLE = False

SWARM_READY = False

async_loop = asyncio.new_event_loop()

def start_async_loop(loop):
    global SWARM_READY
    asyncio.set_event_loop(loop)
    if SWARM_AVAILABLE and hasattr(swarm_engine, "initialize"):
        try:
            loop.run_until_complete(swarm_engine.initialize())
            SWARM_READY = True
        except Exception as e:
            print(f"Warning: 54D Swarm initialize failed. {e}")
    loop.run_forever()

threading.Thread(target=start_async_loop, args=(async_loop,), daemon=True).start()

# ---------------------------------------------------------
# PYGAME INITIALIZATION
# ---------------------------------------------------------
pygame.init()
WIDTH, HEIGHT = 1280, 820
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("COSMOS - Quantum Flight Deck")
clock = pygame.time.Clock()

AVAILABLE_FONTS = {name.replace(" ", "") for name in pygame.font.get_fonts()}


def choose_font(candidates, size, bold=False):
    for name in candidates:
        if name.replace(" ", "").lower() in AVAILABLE_FONTS:
            return pygame.font.SysFont(name, size, bold=bold)
    return pygame.font.SysFont(None, size, bold=bold)


# --- THEME & FONTS (Lost Cosmos Palette) ---
SPACE_TOP = (2, 4, 12)        # Deeper space
SPACE_BOTTOM = (0, 0, 0)      # Void
TEXT_PRIMARY = (226, 232, 240) # Slate-200
TEXT_MUTED = (148, 163, 184)   # Slate-400
TEXT_SOFT = (100, 116, 139)    # Slate-500
CODE_TEXT = (165, 180, 252)    # Indigo-300
USER_COLOR = (56, 189, 248)    # Cyan-400
COSMOS_COLOR = (129, 140, 248) # Indigo-400
SYSTEM_COLOR = (250, 204, 21)  # Yellow-400
GRID_COLOR = (30, 41, 59)      # Slate-800
RING_COLOR = (56, 189, 248)    # Cyan-400
ACCENT_COLOR = (79, 70, 229)   # Indigo-600

font = choose_font(("bahnschrift", "segoe ui", "trebuchet ms"), 16)
small_font = choose_font(("bahnschrift", "segoe ui", "trebuchet ms"), 13)
large_font = choose_font(("bahnschrift", "segoe ui", "trebuchet ms"), 22, bold=True)
title_font = choose_font(("bahnschrift", "segoe ui", "trebuchet ms"), 30, bold=True)
code_font = choose_font(("cascadia code", "consolas", "courier new"), 14)


def lerp_color(start, end, t):
    return tuple(
        int(start[index] + (end[index] - start[index]) * t)
        for index in range(len(start))
    )


def draw_vertical_gradient(surface, top_color, bottom_color):
    width, height = surface.get_size()
    if height <= 1:
        surface.fill(top_color)
        return
    for y in range(height):
        t = y / (height - 1)
        pygame.draw.line(surface, lerp_color(top_color, bottom_color, t), (0, y), (width, y))


@lru_cache(maxsize=512)
def create_glow_surface(radius, color, alpha):
    radius = max(1, int(radius))
    size = radius * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = radius + 1
    # Ensure color components are valid
    safe_color = tuple(max(0, min(255, int(c))) for c in color)
    for current_radius in range(radius, 0, -1):
        strength = current_radius / radius
        layer_alpha = max(0, min(255, int(alpha * (strength ** 2))))
        pygame.draw.circle(surf, (*safe_color, layer_alpha), (center, center), current_radius)
    return surf


def blit_glow(surface, center, radius, color, alpha=110):
    glow = create_glow_surface(int(radius), tuple(color), int(alpha))
    rect = glow.get_rect(center=(int(center[0]), int(center[1])))
    surface.blit(glow, rect)


def draw_pill(surface, text, x, y, fill, border, text_color, font_use=small_font):
    """Draws a premium pill-shaped badge."""
    text_surface = font_use.render(text, True, text_color)
    rect = pygame.Rect(x, y, text_surface.get_width() + 20, text_surface.get_height() + 10)
    pill = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(pill, (*fill, 230), pill.get_rect(), border_radius=99)
    pygame.draw.rect(pill, (*border, 255), pill.get_rect(), width=1, border_radius=99)
    # Subtle highlight
    pygame.draw.rect(pill, (255, 255, 255, 30), pill.get_rect().inflate(-2, -2), width=1, border_radius=99)
    pill.blit(text_surface, (10, 5))
    surface.blit(pill, rect.topleft)
    return rect


scene_background = None
vignette_surface = None


def rebuild_scene_surfaces():
    global scene_background, vignette_surface

    scene_background = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    draw_vertical_gradient(scene_background, (*SPACE_TOP, 255), (*SPACE_BOTTOM, 255))

    nebula_specs = (
        (0.12, 0.18, 240, (26, 109, 196), 78),
        (0.74, 0.22, 300, (131, 58, 188), 62),
        (0.88, 0.74, 260, (18, 185, 154), 52),
        (0.33, 0.84, 220, (255, 112, 74), 42),
    )
    for x_ratio, y_ratio, radius, color, alpha in nebula_specs:
        blit_glow(scene_background, (WIDTH * x_ratio, HEIGHT * y_ratio), radius, color, alpha)

    # Star Layer (Premium twinkling)
    seed = random.Random(54)
    star_palette = (
        (226, 232, 240), # Slate-200
        (186, 230, 253), # Sky-200
        (221, 214, 254), # Violet-200
        (254, 249, 195), # Yellow-100
    )
    for _ in range(250): # More stars
        star_x = seed.randint(0, WIDTH - 1)
        star_y = seed.randint(0, HEIGHT - 1)
        radius = 1 if seed.random() < 0.85 else 2
        color = star_palette[seed.randrange(len(star_palette))]
        alpha = seed.randint(40, 200)
        pygame.draw.circle(scene_background, (*color, alpha), (star_x, star_y), radius)
        if radius == 2 and seed.random() < 0.4:
            # Subtle spikes
            pygame.draw.line(scene_background, (*color, alpha // 3), (star_x - 5, star_y), (star_x + 5, star_y), 1)
            pygame.draw.line(scene_background, (*color, alpha // 3), (star_x, star_y - 5), (star_x, star_y + 5), 1)

    # Ambient Rings
    arc_origin = (int(WIDTH * 0.05), int(HEIGHT * 1.05))
    for radius in (240, 400, 580, 820):
        pygame.draw.circle(scene_background, (56, 189, 248, 12), arc_origin, radius, 1)

    # CRT Scanlines (very subtle)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(scene_background, (255, 255, 255, 3), (0, y), (WIDTH, y))

    vignette_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    draw_vertical_gradient(vignette_surface, (2, 4, 10, 0), (0, 0, 0, 120))
    for depth in range(28):
        alpha = 8 + depth * 2
        pygame.draw.rect(
            vignette_surface,
            (0, 0, 0, alpha),
            pygame.Rect(depth, depth, WIDTH - depth * 2, HEIGHT - depth * 2),
            1,
            border_radius=32,
        )


# ---------------------------------------------------------
# SPACESHIP & CAMERA
# ---------------------------------------------------------
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0


camera = Camera()


class Spaceship:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.base_speed = 0.5
        self.max_speed = 12.0
        self.friction = 0.96
        self.color = (102, 231, 255)
        self.trail = []

    def update(self, keys):
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.vy -= self.base_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.vy += self.base_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx -= self.base_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx += self.base_speed

        self.vx *= self.friction
        self.vy *= self.friction

        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.max_speed

        self.x += self.vx
        self.y += self.vy

        if speed > 0.5:
            self.angle = math.degrees(math.atan2(-self.vy, self.vx))

        self.trail.append((self.x, self.y))
        if len(self.trail) > 28:
            self.trail.pop(0)

        camera.x += (self.x - camera.x - WIDTH / 2) * 0.1
        camera.y += (self.y - camera.y - HEIGHT / 2) * 0.1

    def draw(self, surface, timestamp):
        screen_x = self.x - camera.x
        screen_y = self.y - camera.y
        speed = math.hypot(self.vx, self.vy)

        trail_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        trail_points = []
        for trail_x, trail_y in self.trail:
            view_x = trail_x - camera.x
            view_y = trail_y - camera.y
            if -60 <= view_x <= WIDTH + 60 and -60 <= view_y <= HEIGHT + 60:
                trail_points.append((view_x, view_y))

        for index in range(1, len(trail_points)):
            progress = index / len(trail_points)
            pygame.draw.line(
                trail_layer,
                (38, 219, 255, int(120 * progress)),
                trail_points[index - 1],
                trail_points[index],
                max(1, int(5 * progress)),
            )
        surface.blit(trail_layer, (0, 0))

        body_length = 28
        wing_width = 16
        rad = math.radians(self.angle)
        nose = (screen_x + math.cos(rad) * body_length, screen_y - math.sin(rad) * body_length)
        left = (screen_x + math.cos(rad + 2.46) * wing_width, screen_y - math.sin(rad + 2.46) * wing_width)
        right = (screen_x + math.cos(rad - 2.46) * wing_width, screen_y - math.sin(rad - 2.46) * wing_width)
        center_back = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)

        pulse = 0.75 + 0.25 * math.sin(timestamp * 3.2)
        blit_glow(surface, (screen_x, screen_y), 38, (58, 208, 255), int(78 * pulse))
        blit_glow(surface, (screen_x, screen_y), 20, (201, 142, 255), 65)

        if speed > 0.25:
            thrust = 10 + min(18, speed * 2.7) + math.sin(timestamp * 18.0) * 2.5
            flame_tip = (
                center_back[0] - math.cos(rad) * thrust,
                center_back[1] + math.sin(rad) * thrust,
            )
            flame_left = (
                center_back[0] + math.cos(rad + math.pi / 2.1) * 5,
                center_back[1] - math.sin(rad + math.pi / 2.1) * 5,
            )
            flame_right = (
                center_back[0] + math.cos(rad - math.pi / 2.1) * 5,
                center_back[1] - math.sin(rad - math.pi / 2.1) * 5,
            )
            blit_glow(surface, center_back, 18, (255, 131, 75), 110)
            pygame.draw.polygon(surface, (255, 147, 91), [flame_left, flame_tip, flame_right])
            pygame.draw.polygon(surface, (255, 225, 170), [center_back, flame_tip, center_back], 1)

        pygame.draw.polygon(surface, (224, 246, 255), [nose, left, right])
        pygame.draw.polygon(surface, (38, 56, 92), [nose, left, right], 2)

        cockpit = (
            (screen_x + math.cos(rad) * 9, screen_y - math.sin(rad) * 9),
            (screen_x + math.cos(rad + 2.2) * 6, screen_y - math.sin(rad + 2.2) * 6),
            (screen_x + math.cos(rad - 2.2) * 6, screen_y - math.sin(rad - 2.2) * 6),
        )
        pygame.draw.polygon(surface, (72, 203, 255), cockpit)
        pygame.draw.line(surface, (255, 255, 255), nose, center_back, 2)


spaceship = Spaceship()

# ---------------------------------------------------------
# L-SYSTEM GENERATIVE FRACTALS (Quantum Nature)
# ---------------------------------------------------------
class QuantumFlora:
    def __init__(self, x, y, angle_mod, depth, color_shift):
        self.x = x
        self.y = y
        self.axiom = "X"
        self.rules = {
            "X": "F+[[X]-X]-F[-FX]+X",
            "F": "FF",
        }
        self.depth = min(depth, 5)
        self.system = self.axiom
        for _ in range(self.depth):
            next_system = ""
            for char in self.system:
                next_system += self.rules.get(char, char)
            self.system = next_system

        self.angle_mod = angle_mod
        self.length = 6 - (self.depth * 0.5)
        self.color = color_shift
        self.surface = self.render_fractal()

    def render_fractal(self):
        surf = pygame.Surface((320, 320), pygame.SRCALPHA)
        start_x, start_y = 160, 292
        curr_angle = -90

        stack = []
        cur_x = start_x
        cur_y = start_y
        glow_color = (*self.color[:3], 26)
        core_color = self.color

        for char in self.system:
            if char == "F":
                rad = math.radians(curr_angle)
                next_x = cur_x + math.cos(rad) * self.length
                next_y = cur_y + math.sin(rad) * self.length
                pygame.draw.line(surf, glow_color, (cur_x, cur_y), (next_x, next_y), max(2, int(self.length)))
                pygame.draw.line(surf, core_color, (cur_x, cur_y), (next_x, next_y), max(1, int(self.length / 2)))
                cur_x, cur_y = next_x, next_y
            elif char == "+":
                curr_angle += self.angle_mod
            elif char == "-":
                curr_angle -= self.angle_mod
            elif char == "[":
                stack.append((cur_x, cur_y, curr_angle))
            elif char == "]" and stack:
                cur_x, cur_y, curr_angle = stack.pop()

        return surf

    def draw(self, screen_surf):
        view_x = self.x - camera.x
        view_y = self.y - camera.y
        if -320 < view_x < WIDTH + 320 and -320 < view_y < HEIGHT + 320:
            blit_glow(screen_surf, (view_x, view_y - 90), 52, self.color[:3], 38)
            screen_surf.blit(self.surface, (view_x - 160, view_y - 292))


flor_objects = []

# ---------------------------------------------------------
# PARTICLES & N-BODY PHYSICS
# ---------------------------------------------------------
class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(-2200, 2200)
        self.y = random.uniform(-2200, 2200)
        self.vx = random.uniform(-0.18, 0.18)
        self.vy = random.uniform(-0.18, 0.18)
        self.layer = random.uniform(0.35, 1.1)
        self.radius = random.uniform(0.7, 2.7)
        self.base_color = list(random.choice(
            (
                (120, 176, 255),
                (166, 210, 255),
                (194, 255, 233),
                (254, 240, 180),
            )
        ))
        self.color = self.base_color.copy()
        self.burst_life = 0.0
        self.twinkle = random.uniform(0.0, math.tau)

    def update(self, burst_intensity, sparks):
        drift = 0.3 + self.layer
        
        # N-Body Gravity Attraction (O(M*N))
        for spark in sparks:
            dx = spark.x - self.x
            dy = spark.y - self.y
            dist_sq = dx*dx + dy*dy + 400 # Softening
            if dist_sq < 250000: # Effective range
                force = (spark.mass * 0.05) / dist_sq
                self.vx += dx * force
                self.vy += dy * force

        self.x += self.vx * (drift + burst_intensity * 9.0)
        self.y += self.vy * (drift + burst_intensity * 9.0)
        self.twinkle += 0.015 + self.layer * 0.01

        # Wrap around with buffer
        if self.x - camera.x < -WIDTH * 1.5: self.x += WIDTH * 3
        elif self.x - camera.x > WIDTH * 1.5: self.x -= WIDTH * 3
        if self.y - camera.y < -HEIGHT * 1.5: self.y += HEIGHT * 3
        elif self.y - camera.y > HEIGHT * 1.5: self.y -= HEIGHT * 3

        if self.burst_life > 0:
            self.burst_life -= 0.015
            t = self.burst_life
            self.color = [
                min(255, int(self.base_color[0] + (255 - self.base_color[0]) * t)),
                min(255, int(self.base_color[1] + (255 - self.base_color[1]) * t)),
                min(255, int(self.base_color[2] + (255 - self.base_color[2]) * t))
            ]
        else:
            self.burst_life = 0
            self.color = self.base_color

    def draw(self, surface):
        view_x = self.x - camera.x
        view_y = self.y - camera.y
        if -20 <= view_x <= WIDTH + 20 and -20 <= view_y <= HEIGHT + 20:
            shimmer = 0.6 + 0.4 * ((math.sin(self.twinkle) + 1) / 2)
            color = tuple(min(255, int(channel * shimmer + 20)) for channel in self.color)
            pygame.draw.circle(surface, color, (int(view_x), int(view_y)), max(1, int(self.radius)))

class QuantumSpark:
    """A high-mass 'life spark' created by quantum jobs."""
    def __init__(self, x, y, mass, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.mass = mass # Gravity strength
        self.color = color
        self.life = 1.0 # Decay over time
        self.trail = []
        self.pulse = 0.0

    def update(self, other_sparks):
        # Interact with other sparks (O(M^2))
        for other in other_sparks:
            if other is self: continue
            dx = other.x - self.x
            dy = other.y - self.y
            dist_sq = dx*dx + dy*dy + 900
            
            # GRAVITATIONAL ACCRETION: If too close, "merge" or steal mass
            if dist_sq < 1600:
                self.mass += other.mass * 0.001
                other.mass *= 0.999
            
            force = (other.mass * 0.15) / dist_sq
            self.vx += dx * force
            self.vy += dy * force

        self.vx *= 0.985 # Deep space friction
        self.vy *= 0.985
        self.x += self.vx
        self.y += self.vy
        
        self.life -= 0.0003 # Longer lived
        self.pulse += 0.08
        
        self.trail.append((self.x, self.y))
        if len(self.trail) > 40:
            self.trail.pop(0)

    def draw(self, surface):
        view_x = self.x - camera.x
        view_y = self.y - camera.y
        if -100 <= view_x <= WIDTH + 100 and -100 <= view_y <= HEIGHT + 100:
            # CORE BLOOM (Concentric circles for soft glow)
            p = (math.sin(self.pulse) + 1) * 0.5
            radius = int(self.mass * 0.15 * (1.0 + 0.2 * p))
            
            # Outer Glow
            glow_radius = radius * 4
            glow_surf = create_glow_surface(glow_radius, self.color[:3], int(40 * self.life))
            surface.blit(glow_surf, (int(view_x - glow_radius), int(view_y - glow_radius)), special_flags=pygame.BLEND_ADD)
            
            # Inner Core
            inner_radius = max(2, radius // 2)
            pygame.draw.circle(surface, self.color, (int(view_x), int(view_y)), radius)
            pygame.draw.circle(surface, (255, 255, 255, 200), (int(view_x), int(view_y)), inner_radius)
            
            # Trail
            if len(self.trail) > 2:
                points = [(tx - camera.x, ty - camera.y) for tx, ty in self.trail]
                pygame.draw.lines(surface, (*self.color[:3], int(100 * self.life)), False, points, 2)

particles = [Particle() for _ in range(600)]
quantum_sparks = []
global_burst = 0.0

# ---------------------------------------------------------
# CHAT LOGIC & OVERLAY
# ---------------------------------------------------------
messages = [
    {
        "role": "system",
        "text": "Genesis Engine relay online. Awaiting first contact.",
    }
]
current_input = ""
is_generating = False
scrolling_offset = 0
ui_visible = True
intro_active = True
active_tab = 0
system_status = "STANDBY"
ai_intention_text = "Awaiting sensory input..."
scanner_active = False
brightness_level = 1.0
ambient_audio_enabled = False
quality_label = "Medium (Realistic)"
filter_label = "Nebula"
view_mode_label = "Spaceship (3rd Person)"
tab_names = ("Controls", "Graphics", "Data Ledger", "Cognitive Core")
stream_order = ("audio", "ml", "loc", "light", "usgs", "apod")
stream_pulses = {name: 0.0 for name in stream_order}
live_log = []
genesis_ledger = []
last_ambient_pulse = 0.0
swarm_history = []
ui_hitboxes = {"tabs": [], "buttons": {}, "blocker_start": None}
active_future = None


def wrap_text_chunks(text, font_use, max_width):
    if not text:
        return [""]
    if max_width <= 12:
        return [text]

    wrapped_lines = []
    for raw_line in text.split("\n"):
        if raw_line == "":
            wrapped_lines.append("")
            continue

        words = raw_line.split(" ")
        current_line = ""
        for word in words:
            candidate = word if not current_line else f"{current_line} {word}"
            if font_use.size(candidate)[0] <= max_width:
                current_line = candidate
                continue

            if current_line:
                wrapped_lines.append(current_line)
                current_line = ""

            chunk = ""
            for char in word:
                test_chunk = chunk + char
                if font_use.size(test_chunk)[0] <= max_width or not chunk:
                    chunk = test_chunk
                else:
                    wrapped_lines.append(chunk)
                    chunk = char
            current_line = chunk

        wrapped_lines.append(current_line)

    return wrapped_lines or [""]


def set_status(value):
    global system_status
    system_status = value


def set_ai_intention(value):
    global ai_intention_text
    ai_intention_text = value


def pulse_stream(name):
    if name in stream_pulses:
        stream_pulses[name] = 1.0


def add_live_log(message, level="info"):
    live_log.insert(0, {"text": message, "level": level})
    del live_log[50:]


def add_ledger(name, value, level="info"):
    genesis_ledger.insert(0, {"name": name, "value": value, "level": level})
    del genesis_ledger[50:]


def clear_ui_hitboxes():
    ui_hitboxes["tabs"] = []
    ui_hitboxes["buttons"] = {}
    ui_hitboxes["blocker_start"] = None


def normalize_swarm_response(response):
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if hasattr(response, "cosmos_synthesis"):
        return getattr(response, "cosmos_synthesis") or ""
    if isinstance(response, dict):
        for key in ("cosmos_synthesis", "response", "content", "text", "message"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return str(response)


async def fetch_local_fallback(prompt, msg_idx):
    import requests

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:3b", "prompt": prompt, "stream": True},
            stream=True,
            timeout=180,
        )
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line).get("response", "")
                    messages[msg_idx]["text"] += chunk
        else:
            messages[msg_idx]["text"] += f"\n[Local fallback HTTP {response.status_code}]"
    except Exception:
        messages[msg_idx]["text"] += "\n[Error: Neural Link Offline]"
        add_live_log("Local relay failed to respond.", "error")


def start_genesis():
    global intro_active
    if not intro_active:
        return
    intro_active = False
    set_status("EXPLORING")
    set_ai_intention("Synthesizing a tranquil cosmos from ambient shell data.")
    add_live_log("Genesis shell unlocked.", "success")
    pulse_stream("audio")
    pulse_stream("loc")


def perform_ui_action(action):
    global ui_visible, active_tab

    if action == "regenerate":
        regenerate_universe()
    elif action == "scan":
        toggle_scanner()
    elif action == "toggle_ui":
        ui_visible = not ui_visible
    elif action == "tab_cycle":
        active_tab = (active_tab + 1) % len(tab_names)


def handle_mouse_click(position):
    global active_tab

    if intro_active and ui_hitboxes.get("blocker_start") and ui_hitboxes["blocker_start"].collidepoint(position):
        start_genesis()
        return

    for tab in ui_hitboxes.get("tabs", []):
        if tab["rect"].collidepoint(position):
            active_tab = tab["index"]
            return

    for action, rect in ui_hitboxes.get("buttons", {}).items():
        if rect.collidepoint(position):
            perform_ui_action(action)
            return


def build_relay_lines(max_width):
    rendered = []
    role_colors = {
        "user": USER_COLOR,
        "cosmos": COSMOS_COLOR,
        "system": SYSTEM_COLOR,
    }
    role_names = {
        "user": "YOU",
        "cosmos": "COSMOS",
        "system": "SYSTEM",
    }
    for message in messages[-18:]:
        role = message["role"]
        prefix = f"> {role_names.get(role, role.upper())}: "
        wrapped_raw = []
        for raw_line in message["text"].replace("\r\n", "\n").split("\n"):
            raw_line = raw_line if raw_line else " "
            wrapped_raw.extend(wrap_text_chunks(raw_line, code_font, max_width - 18))

        for index, line in enumerate(wrapped_raw):
            full_line = f"{prefix}{line}" if index == 0 else f"  {' ' * len(role_names.get(role, role.upper()))}  {line}"
            rendered.append(
                {
                    "surface": code_font.render(full_line, True, role_colors.get(role, TEXT_MUTED)),
                    "height": code_font.get_height() + 4,
                }
            )
    return rendered


def seed_initial_logs():
    add_live_log("Genesis Engine v2.3 Synthesis Complete...", "info")
    add_live_log("Calibrating quantum relay shell.", "data")
    add_ledger("Quantum Bridge", "Online" if Q_AVAILABLE else "Simulator fallback", "success" if Q_AVAILABLE else "warn")
    add_ledger("Swarm Core", "54D online" if SWARM_AVAILABLE else "Local fallback", "success" if SWARM_AVAILABLE else "warn")


seed_initial_logs()


async def fetch_54d_swarm(prompt):
    global SWARM_READY
    msg_idx = len(messages) - 1
    if not SWARM_AVAILABLE:
        await fetch_local_fallback(prompt, msg_idx)
        return

    try:
        if not SWARM_READY and hasattr(swarm_engine, "initialize"):
            await swarm_engine.initialize()
            SWARM_READY = True

        swarm_history.append({"role": "user", "content": prompt})
        response = None

        # Primary: check for the proxy chat method (added in orchestration) or the native ones
        if hasattr(swarm_engine, "chat"):
            response = await swarm_engine.chat(prompt)
        elif hasattr(swarm_engine, "generate_peer_response"):
            response = await swarm_engine.generate_peer_response(
                prompt,
                history=swarm_history[-24:],
            )
        elif hasattr(swarm_engine, "generate"):
            response = await swarm_engine.generate(prompt)
        else:
            raise AttributeError("54D orchestrator exposes no chat-compatible method")

        normalized = normalize_swarm_response(response)
        messages[msg_idx]["text"] = normalized if normalized else "[54D relay returned an empty response]"
        swarm_history.append({"role": "assistant", "content": messages[msg_idx]["text"]})

        if "```python" in messages[msg_idx]["text"]:
            messages.append(
                {
                    "role": "system",
                    "text": "Cosmos injected new Python logic. Code Autonomous Override Ready.",
                }
            )
            add_ledger("Autonomy", "Python override surfaced", "warn")
    except Exception as e:
        add_live_log(f"54D relay error: {e}", "warn")
        add_ledger("54D Relay", f"Fell back after: {type(e).__name__}", "warn")
        await fetch_local_fallback(prompt, msg_idx)


def trigger_quantum_thought(prompt):
    global is_generating, global_burst
    is_generating = True
    set_status("GENERATING")
    set_ai_intention("Synthesizing a tranquil cosmos from user signal.")
    add_live_log("User prompt received. Beginning signal synthesis.", "data")
    add_ledger("Prompt", prompt[:48] + ("..." if len(prompt) > 48 else ""), "info")
    pulse_stream("audio")
    pulse_stream("ml")
    pulse_stream("apod")

    entropy = 0.5
    if Q_AVAILABLE and q_bridge:
        try:
            entropy = q_bridge.get_entropy({"geometric_phase_rad": len(prompt) / 50.0})
        except Exception:
            pass

    global_burst = 0.6 + (entropy * 2.5)
    for particle in particles:
        particle.burst_life = global_burst
        particle.vx += random.uniform(-2, 2) * entropy
        particle.vy += random.uniform(-2, 2) * entropy

    # Dimensional colors derived from entropy
    angle = 20 + int(entropy * 15)
    depth = 3 + int(entropy * 3)
    r = int(100 + entropy * 155)
    g = int(255 - entropy * 100)
    b = int(150 + entropy * 100)

    # SPAWN QUANTUM SPARK (N-Body Heavy Seed)
    spark_mass = 50 + int(entropy * 150)
    spark_color = (r, g, b, 255)
    new_spark = QuantumSpark(spaceship.x, spaceship.y, spark_mass, spark_color)
    new_spark.vx = spaceship.vx * 0.5 + random.uniform(-2, 2)
    new_spark.vy = spaceship.vy * 0.5 + random.uniform(-2, 2)
    quantum_sparks.append(new_spark)
    if len(quantum_sparks) > 12:
        quantum_sparks.pop(0)

    flora = QuantumFlora(spaceship.x, spaceship.y, angle, depth, (r, g, b, 215))
    flor_objects.append(flora)
    if len(flor_objects) > 10:
        flor_objects.pop(0)

    messages.append({"role": "cosmos", "text": f"[Q-Resonance {entropy:.3f}]\n"})
    add_ledger("Q-Resonance", f"{entropy:.3f}", "success")

    global active_future
    active_future = asyncio.run_coroutine_threadsafe(fetch_54d_swarm(prompt), async_loop)
    add_live_log("Relay synthesis initiated...", "info")
    set_ai_intention("Weaving response threads across the relay lattice.")

    set_status("SCANNING" if scanner_active else "EXPLORING")


def draw_navigation_grid(surface):
    grid = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    step = 170
    x_offset = int((-camera.x * 0.18) % step)
    y_offset = int((-camera.y * 0.18) % step)

    for x in range(x_offset - step, WIDTH + step, step):
        pygame.draw.line(grid, (*GRID_COLOR, 22), (x, 0), (x, HEIGHT), 1)
    for y in range(y_offset - step, HEIGHT + step, step):
        pygame.draw.line(grid, (48, 82, 140, 18), (0, y), (WIDTH, y), 1)

    center = (int(spaceship.x - camera.x), int(spaceship.y - camera.y))
    for radius in (100, 200, 320):
        pygame.draw.circle(grid, (*RING_COLOR, 16), center, radius, 1)

    surface.blit(grid, (0, 0))


def create_ui_panel(rect, top_color=(15, 23, 42, 235), bottom_color=(9, 13, 27, 215)):
    """Creates a glassmorphic panel surface with blur-like gradient."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    draw_vertical_gradient(panel, top_color, bottom_color)
    # Outer border
    pygame.draw.rect(panel, (51, 65, 85, 180), panel.get_rect(), width=1, border_radius=18)
    # Inner highlights (fake glass reflection)
    pygame.draw.rect(panel, (255, 255, 255, 12), panel.get_rect().inflate(-4, -4), width=1, border_radius=16)
    return panel


def get_level_color(level):
    return {
        "info": TEXT_MUTED,
        "success": (74, 222, 128),
        "warn": (250, 204, 21),
        "error": (248, 113, 113),
        "data": USER_COLOR,
    }.get(level, TEXT_MUTED)


def draw_button_block(surface, rect, label, fill, border, hint=""):
    """Draws a high-end interactive button block."""
    button = pygame.Surface(rect.size, pygame.SRCALPHA)
    # Premium gradient
    draw_vertical_gradient(button, (*fill, 245), (*fill, 210))
    # Border with glow
    pygame.draw.rect(button, (*border, 255), button.get_rect(), width=1, border_radius=12)
    # Inner bevel
    pygame.draw.rect(button, (255, 255, 255, 25), button.get_rect().inflate(-2, -2), width=1, border_radius=11)
    
    label_surf = font.render(label, True, (255, 255, 255))
    button.blit(label_surf, (16, 11))
    
    if hint:
        hint_text = small_font.render(hint, True, TEXT_MUTED)
        button.blit(hint_text, (rect.width - hint_text.get_width() - 12, 14))
    surface.blit(button, rect.topleft)


def draw_controls_tab(panel, rect, panel_rect):
    actions = (
        ("Regenerate Universe", (51, 65, 85), (100, 116, 139), "[Ctrl+R]"),
        ("Scan for Anomalies", (8, 145, 178), (34, 211, 238), "[Ctrl+G]"),
        ("Shell UI Toggle", (79, 70, 229), (129, 140, 248), "[Ctrl+H]"),
        ("Tab Cycle", (147, 51, 234), (192, 132, 252), "[Ctrl+Tab]"),
    )
    action_ids = ("regenerate", "scan", "toggle_ui", "tab_cycle")
    y = rect.y
    for action_id, (label, fill, border, hint) in zip(action_ids, actions):
        button_rect = pygame.Rect(rect.x, y, rect.w, 40)
        draw_button_block(panel, button_rect, label, fill, border, hint)
        ui_hitboxes["buttons"][action_id] = pygame.Rect(panel_rect.x + button_rect.x, panel_rect.y + button_rect.y, button_rect.w, button_rect.h)
        y += 48
    panel.blit(small_font.render("Use mouse, function keys, or Ctrl shortcuts to navigate.", True, TEXT_MUTED), (rect.x, y + 4))


def draw_graphics_row(panel, x, y, label, value):
    panel.blit(small_font.render(label, True, TEXT_MUTED), (x, y))
    panel.blit(font.render(value, True, TEXT_PRIMARY), (x, y + 14))


def draw_slider(panel, x, y, width, label, value_text, ratio):
    draw_graphics_row(panel, x, y, label, value_text)
    track_rect = pygame.Rect(x, y + 40, width, 4)
    pygame.draw.rect(panel, (51, 65, 85), track_rect, border_radius=4)
    fill_rect = pygame.Rect(x, y + 40, int(width * ratio), 4)
    pygame.draw.rect(panel, (79, 70, 229), fill_rect, border_radius=4)
    knob_x = x + int(width * ratio)
    pygame.draw.circle(panel, (15, 23, 42), (knob_x, y + 42), 8)
    pygame.draw.circle(panel, (99, 102, 241), (knob_x, y + 42), 8, 2)


def draw_toggle(panel, x, y, label, enabled):
    draw_graphics_row(panel, x, y, label, "Enabled" if enabled else "Disabled")
    switch_rect = pygame.Rect(x + 220, y + 14, 34, 20)
    pygame.draw.rect(panel, (79, 70, 229) if enabled else (51, 65, 85), switch_rect, border_radius=20)
    knob_x = switch_rect.right - 10 if enabled else switch_rect.x + 10
    pygame.draw.circle(panel, (255, 255, 255), (knob_x, switch_rect.centery), 6)


def draw_graphics_tab(panel, rect):
    draw_graphics_row(panel, rect.x, rect.y, "View Mode", view_mode_label)
    draw_graphics_row(panel, rect.x, rect.y + 54, "Graphics Style", quality_label)
    draw_graphics_row(panel, rect.x, rect.y + 108, "Color Filter", filter_label)
    draw_slider(panel, rect.x, rect.y + 150, rect.w - 18, "Brightness", f"{brightness_level:.2f}", brightness_level / 2.0)
    draw_toggle(panel, rect.x, rect.y + 220, "Enable Ambient Audio", ambient_audio_enabled)


def draw_data_tab(panel, rect):
    ledger_area = pygame.Rect(rect.x, rect.y, rect.w, rect.h)
    panel.set_clip(ledger_area)
    y = ledger_area.y
    for entry in genesis_ledger[:10]:
        name_surface = code_font.render(f"[{entry['name']}]", True, COSMOS_COLOR)
        value_surface = code_font.render(entry["value"], True, get_level_color(entry["level"]))
        panel.blit(name_surface, (ledger_area.x, y))
        panel.blit(value_surface, (ledger_area.x + name_surface.get_width() + 10, y))
        y += code_font.get_height() + 8
    panel.set_clip(None)


def draw_cognitive_tab(panel, rect):
    viz_rect = pygame.Rect(rect.x, rect.y, rect.w, 80)
    pygame.draw.rect(panel, (0, 0, 0, 60), viz_rect, border_radius=12)
    pygame.draw.rect(panel, (51, 65, 85, 40), viz_rect, width=1, border_radius=12)
    
    column_width = viz_rect.width / len(stream_order)
    for index, stream in enumerate(stream_order):
        pulse = stream_pulses[stream]
        center_x = int(viz_rect.x + column_width * index + column_width / 2)
        center_y = viz_rect.y + 45
        
        # Stream label
        label = small_font.render(stream.upper(), True, TEXT_SOFT)
        panel.blit(label, (center_x - label.get_width() // 2, viz_rect.y + 12))
        
        # Glow based on activity
        color = (56, 189, 248) if pulse > 0.05 else (51, 65, 85)
        alpha = 100 + int(155 * pulse)
        if pulse > 0.1:
            blit_glow(panel, (center_x, center_y), 14, color, alpha // 2)
        
        pygame.draw.circle(panel, color, (center_x, center_y), 6 + int(4 * pulse))
        pygame.draw.circle(panel, (255, 255, 255, int(180 * pulse)), (center_x, center_y), 3 + int(2 * pulse))

    intent_rect = pygame.Rect(rect.x, rect.y + 100, rect.w, 80)
    pygame.draw.rect(panel, (0, 0, 0, 60), intent_rect, border_radius=12)
    pygame.draw.rect(panel, (51, 65, 85, 40), intent_rect, width=1, border_radius=12)
    
    panel.blit(code_font.render("COGNITIVE INTENTION:", True, COSMOS_COLOR), (intent_rect.x + 14, intent_rect.y + 12))
    wrapped = wrap_text_chunks(ai_intention_text, small_font, intent_rect.width - 28)
    for index, line in enumerate(wrapped[:3]):
        panel.blit(small_font.render(line, True, TEXT_PRIMARY), (intent_rect.x + 14, intent_rect.y + 34 + index * 18))


def draw_genesis_panel(surface):
    if not ui_visible:
        return

    panel_width = min(396, max(330, int(WIDTH * 0.31)))
    panel_height = max(320, min(438, HEIGHT - 220))
    panel_rect = pygame.Rect(16, 16, panel_width, panel_height)
    panel = create_ui_panel(panel_rect)

    panel.blit(large_font.render(f"STATUS: {system_status}", True, TEXT_PRIMARY), (16, 14))
    pygame.draw.line(panel, (71, 85, 105, 200), (16, 54), (panel_rect.width - 16, 54), 1)

    x = 12
    tab_y = 62
    for index, tab_name in enumerate(tab_names):
        text_color = TEXT_PRIMARY if index == active_tab else TEXT_MUTED
        tab_surface = font.render(tab_name, True, text_color)
        tab_rect = pygame.Rect(x - 4, tab_y - 2, tab_surface.get_width() + 8, 26)
        panel.blit(tab_surface, (x, tab_y))
        ui_hitboxes["tabs"].append(
            {
                "index": index,
                "rect": pygame.Rect(panel_rect.x + tab_rect.x, panel_rect.y + tab_rect.y, tab_rect.w, tab_rect.h),
            }
        )
        if index == active_tab:
            pygame.draw.line(panel, (79, 70, 229), (x, tab_y + 24), (x + tab_surface.get_width(), tab_y + 24), 2)
        x += tab_surface.get_width() + 18

    content_rect = pygame.Rect(16, 98, panel_rect.width - 32, panel_rect.height - 114)
    if active_tab == 0:
        draw_controls_tab(panel, content_rect, panel_rect)
    elif active_tab == 1:
        draw_graphics_tab(panel, content_rect)
    elif active_tab == 2:
        draw_data_tab(panel, content_rect)
    else:
        draw_cognitive_tab(panel, content_rect)

    surface.blit(panel, panel_rect.topleft)


def draw_log_panel(surface):
    if not ui_visible:
        return

    panel_width = min(396, max(330, int(WIDTH * 0.31)))
    panel_height = max(150, min(190, HEIGHT - 486))
    panel_rect = pygame.Rect(16, HEIGHT - panel_height - 16, panel_width, panel_height)
    panel = create_ui_panel(panel_rect, (12, 18, 34, 220), (8, 12, 24, 205))
    panel.blit(font.render("Genesis Log", True, TEXT_PRIMARY), (16, 12))
    pygame.draw.line(panel, (71, 85, 105, 200), (16, 38), (panel_rect.width - 16, 38), 1)

    y = 50
    for entry in live_log[:8]:
        line_surface = code_font.render(f"> {entry['text']}", True, get_level_color(entry["level"]))
        panel.blit(line_surface, (16, y))
        y += code_font.get_height() + 6

    surface.blit(panel, panel_rect.topleft)


def draw_help_chips(surface):
    if not ui_visible:
        return

    chips = ("Ctrl+H UI", "F1-F4 tabs", "Ctrl+R regenerate", "Ctrl+G scan", "PgUp/PgDn scroll", "Enter relay")
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    x = 16
    y = HEIGHT - 46
    for chip in chips:
        rect = draw_pill(layer, chip, x, y, (11, 16, 32), (70, 98, 152), TEXT_MUTED)
        x = rect.right + 8
    surface.blit(layer, (0, 0))


def draw_relay_panel(surface):
    global scrolling_offset
    if not ui_visible:
        return

    relay_width = min(540, max(400, int(WIDTH * 0.41)))
    panel_rect = pygame.Rect(WIDTH - relay_width - 16, 16, relay_width, HEIGHT - 32)
    # Lost Cosmos Style: Subtle indigo tint in the glass
    panel = create_ui_panel(panel_rect, (12, 18, 42, 230), (7, 10, 24, 215))

    title_surf = large_font.render("Command Relay", True, TEXT_PRIMARY)
    panel.blit(title_surf, (20, 16))
    panel.blit(small_font.render("Genesis shell // live cognitive stream // v4.2", True, TEXT_SOFT), (21, 45))
    
    # Pulse indicator for LIVE status
    pulse_alpha = 180 + int(70 * math.sin(time.time() * 4.0))
    draw_pill(panel, "LIVE", panel_rect.width - 74, 18, (79, 70, 229), (129, 140, 248), (255, 255, 255))

    relay_rect = pygame.Rect(16, 80, panel_rect.width - 32, panel_rect.height - 168)
    # Darker cutout for the message area
    pygame.draw.rect(panel, (0, 0, 0, 60), relay_rect, border_radius=12)
    pygame.draw.rect(panel, (51, 65, 85, 40), relay_rect, width=1, border_radius=12)

    relay_lines = build_relay_lines(relay_rect.width - 20)
    total_height = sum(line["height"] for line in relay_lines) + max(0, len(relay_lines) - 1) * 2
    max_scroll = max(0, total_height - relay_rect.height + 10)
    scrolling_offset = max(0, min(scrolling_offset, max_scroll))

    panel.set_clip(relay_rect)
    y = relay_rect.bottom - 8 + scrolling_offset
    for line in reversed(relay_lines):
        y -= line["height"]
        if y + line["height"] < relay_rect.top:
            break
        panel.blit(line["surface"], (relay_rect.x + 10, y))
        y -= 2
    panel.set_clip(None)

    # Input Box Design
    input_rect = pygame.Rect(16, panel_rect.height - 74, panel_rect.width - 32, 58)
    input_box = pygame.Surface(input_rect.size, pygame.SRCALPHA)
    draw_vertical_gradient(input_box, (15, 25, 48, 245), (10, 15, 32, 225))
    pygame.draw.rect(input_box, ACCENT_COLOR, input_box.get_rect(), width=1, border_radius=14)
    pygame.draw.rect(input_box, (255, 255, 255, 12), input_box.get_rect().inflate(-4, -4), width=1, border_radius=12)

    placeholder = "Transmit into the relay..."
    show_text = current_input if current_input else placeholder
    input_color = TEXT_PRIMARY if current_input else TEXT_SOFT
    
    # Animated cursor
    cursor = "_" if (time.time() % 1.0 < 0.5) else " "
    display_text = show_text + (cursor if current_input else "")
    
    wrapped_input = wrap_text_chunks(display_text, font, input_rect.width - 110)
    input_box.blit(font.render(wrapped_input[-1], True, input_color), (16, 18))
    
    btn_color = (8, 145, 178) if current_input else (51, 65, 85)
    draw_pill(input_box, "ENTER", input_rect.width - 92, 14, btn_color, USER_COLOR, (255, 255, 255))

    if is_generating:
        # Status pulse when thinking
        gen_pulse = 0.5 + 0.5 * math.sin(time.time() * 6.0)
        indicator = small_font.render("Synchronizing swarm consciousness...", True, (255, 180, 140))
        indicator.set_alpha(int(150 + 105 * gen_pulse))
        panel.blit(indicator, (20, panel_rect.height - 98))

    panel.blit(input_box, input_rect.topleft)
    surface.blit(panel, panel_rect.topleft)


def draw_crosshair(surface):
    center = (WIDTH // 2, HEIGHT // 2)
    cross = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    color = (56, 189, 248, 140 if scanner_active or is_generating else 80)
    size = 8 if scanner_active or is_generating else 6
    pygame.draw.line(cross, color, (center[0] - size, center[1]), (center[0] - 2, center[1]), 1)
    pygame.draw.line(cross, color, (center[0] + 2, center[1]), (center[0] + size, center[1]), 1)
    pygame.draw.line(cross, color, (center[0], center[1] - size), (center[0], center[1] - 2), 1)
    pygame.draw.line(cross, color, (center[0], center[1] + 2), (center[0], center[1] + size), 1)
    pygame.draw.circle(cross, color, center, 12 if scanner_active else 9, 1)
    surface.blit(cross, (0, 0))


def draw_blocker(surface):
    if not intro_active:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((2, 4, 12, 240)) # Deeper void for intro
    
    card_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 180, 600, 360)
    card = create_ui_panel(card_rect, (15, 23, 42, 254), (7, 10, 20, 245))
    
    title = title_font.render("Genesis Engine", True, (255, 255, 255))
    subtitle = large_font.render("The Definitive Core", True, TEXT_MUTED)
    
    body_text = (
        "This engine transmutes reality into a digital cosmos. For the full experience, "
        "grant access to sensor arrays when prompted. No data is stored. "
        "Press ENTER or use the interactive button to initiate genesis."
    )
    body_lines = wrap_text_chunks(body_text, font, card_rect.width - 60)
    
    card.blit(title, (card_rect.width // 2 - title.get_width() // 2, 50))
    card.blit(subtitle, (card_rect.width // 2 - subtitle.get_width() // 2, 95))
    
    y_text = 150
    for line in body_lines:
        line_surf = font.render(line, True, TEXT_MUTED)
        card.blit(line_surf, (card_rect.width // 2 - line_surf.get_width() // 2, y_text))
        y_text += 24

    start_rect = pygame.Rect(card_rect.width // 2 - 120, 260, 240, 48)
    # Bright blue start button
    draw_button_block(card, start_rect, "Initiate Genesis", (79, 70, 229), (129, 140, 248), "[ENTER]")
    ui_hitboxes["blocker_start"] = pygame.Rect(card_rect.x + start_rect.x, card_rect.y + start_rect.y, start_rect.w, start_rect.h)
    
    overlay.blit(card, card_rect.topleft)
    surface.blit(overlay, (0, 0))


def regenerate_universe():
    flor_objects.clear()
    for particle in particles:
        particle.x = random.uniform(-2200, 2200)
        particle.y = random.uniform(-2200, 2200)
        particle.twinkle = random.uniform(0.0, math.tau)
    add_live_log("Universe regeneration seeded.", "info")
    add_ledger("Universe", "Regenerated from current shell", "success")
    set_status("EXPLORING")
    set_ai_intention("Reweaving local star memory into a fresh cosmos.")
    pulse_stream("light")
    pulse_stream("apod")


def toggle_scanner():
    global scanner_active
    scanner_active = not scanner_active
    set_status("SCANNING" if scanner_active else "EXPLORING")
    add_live_log(f"Anomaly Scanner {'Activated' if scanner_active else 'Deactivated'}", "info")
    add_ledger("Scanner", "Activated" if scanner_active else "Deactivated", "data")
    set_ai_intention("Tracing hidden echoes through the anomaly lattice." if scanner_active else "Resuming baseline exploration cadence.")
    pulse_stream("ml")
    pulse_stream("usgs")


rebuild_scene_surfaces()

# ---------------------------------------------------------
# RENDER LOOP
# ---------------------------------------------------------
running = True

while running:
    frame_time = time.time()
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            rebuild_scene_surfaces()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif intro_active and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                start_genesis()
            elif event.key == pygame.K_h and (event.mod & pygame.KMOD_CTRL):
                ui_visible = not ui_visible
            elif event.key == pygame.K_TAB and (event.mod & pygame.KMOD_CTRL):
                active_tab = (active_tab + 1) % len(tab_names)
            elif event.key in (pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4):
                active_tab = (event.key - pygame.K_F1) % len(tab_names)
            elif event.key == pygame.K_r and (event.mod & pygame.KMOD_CTRL) and not current_input:
                regenerate_universe()
            elif event.key == pygame.K_g and (event.mod & pygame.KMOD_CTRL) and not current_input:
                toggle_scanner()
            elif event.key == pygame.K_BACKSPACE:
                current_input = current_input[:-1]
            elif event.key == pygame.K_RETURN:
                if current_input.strip() and not is_generating:
                    messages.append({"role": "user", "text": current_input})
                    prompt = current_input
                    current_input = ""
                    threading.Thread(target=trigger_quantum_thought, args=(prompt,), daemon=True).start()
            elif event.key == pygame.K_PAGEUP:
                scrolling_offset += 42
            elif event.key == pygame.K_PAGEDOWN:
                scrolling_offset = max(0, scrolling_offset - 42)
            else:
                if len(event.unicode) > 0 and event.key not in (
                    pygame.K_w,
                    pygame.K_a,
                    pygame.K_s,
                    pygame.K_d,
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                ):
                    current_input += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_mouse_click(event.pos)

        elif event.type == pygame.MOUSEWHEEL:
            scrolling_offset = max(0, scrolling_offset + event.y * 34)

    spaceship.update(keys)
    global_burst = max(0, global_burst - 0.012)
    
    # HANDLE ASYNC SWARM RESPONSE
    if active_future and active_future.done():
        try:
            active_future.result() # Trigger any exceptions
            add_live_log("Relay synthesis complete.", "success")
        except Exception as e:
            messages[-1]["text"] += f"\nError: {e}"
            add_live_log(f"Relay failed: {e}", "error")
        is_generating = False
        active_future = None
    
    # N-BODY PHYSICS UPDATE
    quantum_sparks = [s for s in quantum_sparks if s.life > 0]
    for spark in quantum_sparks:
        spark.update(quantum_sparks)
    
    for particle in particles:
        particle.update(global_burst, quantum_sparks)
        
    for stream in stream_order:
        stream_pulses[stream] = max(0.0, stream_pulses[stream] - 0.025)
    if not intro_active and frame_time - last_ambient_pulse > 1.2:
        pulse_stream(random.choice(stream_order))
        last_ambient_pulse = frame_time

    screen.blit(scene_background, (0, 0))
    draw_navigation_grid(screen)

    for flora in flor_objects:
        flora.draw(screen)

    for spark in quantum_sparks:
        spark.draw(screen)

    for particle in particles:
        particle.draw(screen)

    spaceship.draw(screen, frame_time)

    if is_generating:
        pulse_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pulse_center = (int(spaceship.x - camera.x), int(spaceship.y - camera.y))
        pulse_radius = 52 + int(8 * math.sin(frame_time * 7.0))
        pygame.draw.circle(pulse_layer, (113, 218, 255, 72), pulse_center, pulse_radius, 2)
        pygame.draw.circle(pulse_layer, (192, 122, 255, 38), pulse_center, pulse_radius + 16, 1)
        screen.blit(pulse_layer, (0, 0))

    screen.blit(vignette_surface, (0, 0))
    clear_ui_hitboxes()
    draw_crosshair(screen)
    draw_genesis_panel(screen)
    draw_log_panel(screen)
    draw_relay_panel(screen)
    draw_help_chips(screen)
    draw_blocker(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
