import sys
import pygame
import numpy as np
from time import time
from pfd import AircraftState, PrimaryFlightDisplay

# ===============================
# SCREEN & LAYOUT
# ===============================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
PFD_WIDTH = 800
PANEL_WIDTH = SCREEN_WIDTH - PFD_WIDTH

# ===============================
# FLIGHT CONSTANTS
# ===============================
VS_CLIMB = 700.0
VS_DESCENT = -600.0
PITCH_CLIMB = 7.0
PITCH_DESCENT = -4.0
ALT_CAPTURE_BAND = 80.0
TURN_GAIN = 3.0
MAX_TURN_RATE = 6.0

# ===============================
# INIT PYGAME
# ===============================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Primary Flight Display Simulator (Project CATC Student)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

# ===============================
# CREATE PFD
# ===============================
PFD = PrimaryFlightDisplay(
    (PFD_WIDTH, SCREEN_HEIGHT),
    masked=True,
    max_fps=60
)

# ===============================
# BUTTONS
# ===============================
MODES = ["CLIMB", "DESCENT", "CRUISE", "ROLLS"]
buttons = {}
for i, mode in enumerate(MODES):
    buttons[mode] = pygame.Rect(PFD_WIDTH + 50, 100 + i * 80, 300, 60)

ALT_UP = pygame.Rect(PFD_WIDTH + 100, 460, 100, 40)
ALT_DN = pygame.Rect(PFD_WIDTH + 210, 460, 100, 40)
IAS_UP = pygame.Rect(PFD_WIDTH + 120, 560, 80, 40)
IAS_DN = pygame.Rect(PFD_WIDTH + 210, 560, 80, 40)
TURN_UP = pygame.Rect(PFD_WIDTH + 100, 660, 90, 40)
TURN_DN = pygame.Rect(PFD_WIDTH + 210, 660, 90, 40)

BANK_OPTIONS = [-65, -60, -45, -30, 0, 30, 45, 60, 65]
bank_angle = 0

# ===============================
# STATE VARIABLES
# ===============================
mode = "CRUISE"
prev_mode = mode
t0 = time()

ALTITUDE_CMD = 1000.0
IAS_CMD = 100.0

roll = 0.0
pitch = 0.0
heading = 0.0
airspeed = IAS_CMD
altitude = ALTITUDE_CMD
vspeed = 0.0

g_factor = 1.0

# ===============================
# HELPERS
# ===============================
def smooth(v, t, r, dt):
    return v + (t - v) * r * dt

def update_airspeed(ias, pitch, target, dt):
    return smooth(ias, target - pitch * 0.4, 0.8, dt)

def compute_g(bank):
    return 1.0 / max(0.01, np.cos(np.radians(bank)))

# ===============================
# MAIN LOOP
# ===============================
running = True
while running:
    dt = clock.tick(60) / 1000
    sim_time = time() - t0

    # ---------------------------
    # EVENTS
    # ---------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Flight mode buttons
            for m, rect in buttons.items():
                if rect.collidepoint(event.pos):
                    prev_mode = mode
                    mode = m

            # ALT knob
            if ALT_UP.collidepoint(event.pos):
                ALTITUDE_CMD += 100
                if mode == "CRUISE":
                    mode = "CLIMB"
            if ALT_DN.collidepoint(event.pos):
                ALTITUDE_CMD -= 100
                if mode == "CRUISE":
                    mode = "DESCENT"

            # IAS knob
            if IAS_UP.collidepoint(event.pos):
                IAS_CMD += 5
            if IAS_DN.collidepoint(event.pos):
                IAS_CMD -= 5

            # TURN knob
            if TURN_UP.collidepoint(event.pos):
                idx = BANK_OPTIONS.index(bank_angle)
                if idx < len(BANK_OPTIONS) - 1:
                    bank_angle = BANK_OPTIONS[idx + 1]
            if TURN_DN.collidepoint(event.pos):
                idx = BANK_OPTIONS.index(bank_angle)
                if idx > 0:
                    bank_angle = BANK_OPTIONS[idx - 1]

    # ===============================
    # FLIGHT LOGIC
    # ===============================
    if mode == "CLIMB":
        roll = smooth(roll, 0.0, 2.0, dt)
        pitch = smooth(pitch, PITCH_CLIMB, 1.5, dt)
        vspeed = smooth(vspeed, VS_CLIMB, 1.5, dt)
        altitude += vspeed / 60 * dt
        airspeed = update_airspeed(airspeed, pitch, IAS_CMD - 10, dt)
        if altitude >= ALTITUDE_CMD - ALT_CAPTURE_BAND:
            mode = "ALT_CAPTURE"

    elif mode == "DESCENT":
        roll = smooth(roll, 0.0, 2.0, dt)
        pitch = smooth(pitch, PITCH_DESCENT, 1.5, dt)
        vspeed = smooth(vspeed, VS_DESCENT, 1.5, dt)
        altitude += vspeed / 60 * dt
        airspeed = update_airspeed(airspeed, pitch, IAS_CMD + 5, dt)
        if altitude <= ALTITUDE_CMD + ALT_CAPTURE_BAND:
            mode = "ALT_CAPTURE"

    elif mode == "ALT_CAPTURE":
        roll = smooth(roll, 0.0, 2.5, dt)
        error = ALTITUDE_CMD - altitude
        vs_cmd = np.clip(error * 5.0, -500, 500)
        vspeed = smooth(vspeed, vs_cmd, 2.0, dt)
        pitch = smooth(pitch, vs_cmd / 150.0, 2.0, dt)
        altitude += vspeed / 25 * dt
        airspeed = update_airspeed(airspeed, pitch, IAS_CMD, dt)
        if abs(error) < 5:
            altitude = ALTITUDE_CMD
            airspeed = IAS_CMD
            pitch = 0.0
            vspeed = 0.0
            mode = "CRUISE"

    elif mode == "CRUISE":
        roll = smooth(roll, 0.0, 3.0, dt)
        pitch = smooth(pitch, 0.0, 3.0, dt)
        vspeed = smooth(vspeed, 0.0, 3.0, dt)
        airspeed = smooth(airspeed, IAS_CMD, 1.2, dt)

    elif mode == "ROLLS":
        roll = smooth(roll, bank_angle, 1.5, dt)
        g_target = compute_g(abs(roll))
        g_factor = smooth(g_factor, g_target, 3.0, dt)
        pitch = smooth(pitch, 3 + (g_factor - 1) * 3, 1.5, dt)
        airspeed = update_airspeed(airspeed, pitch, IAS_CMD - 5, dt)

    if mode != "ROLLS":
        g_factor = smooth(g_factor, 1.0, 2.5, dt)

    # ===============================
    # HEADING DYNAMICS (REALISTIC)
    # ===============================
    if abs(roll) > 1.0 and airspeed > 30:
        turn_rate = (1091 * np.tan(np.radians(roll))) / max(airspeed, 1)
        heading = (heading + turn_rate * dt) % 360

    # ===============================
    # AIRCRAFT STATE
    # ===============================
    state = AircraftState(
        pitch=pitch,
        roll=roll,
        airspeed=airspeed,
        airspeed_cmd=IAS_CMD,
        vspeed=vspeed,
        altitude=altitude,
        altitude_cmd=ALTITUDE_CMD,
        heading=heading,
        heading_cmd=None,
        course=heading
    )

    # ===============================
    # DRAW EVERYTHING
    # ===============================
    screen.fill((0, 0, 0))  # Clear screen

    # Draw PFD
    # Draw PFD
    PFD.tick()
    PFD.update(state, real_time=sim_time)
    PFD.draw()
    screen.blit(PFD.get_surface(), (0, 0))


    # Draw side panel
    panel = pygame.Rect(PFD_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, (28, 28, 28), panel)

    # Flight Modes Title
    screen.blit(font.render("        FLIGHT MODES      ", True, (255, 255, 255)),
                (PFD_WIDTH + 80, 50))

    # Flight Mode Buttons
    for m, rect in buttons.items():
        color = (255, 180, 0) if m == mode else (80, 80, 80)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        text_surf = font.render(m, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    # ALT Knob
    pygame.draw.rect(screen, (0,200,0), ALT_UP, border_radius=8)
    pygame.draw.rect(screen, (220,50,50), ALT_DN, border_radius=8)
    screen.blit(font.render("ALT +100", True, (0, 0, 0)), ALT_UP.move(5, 10))
    screen.blit(font.render("ALT -100", True, (0, 0, 0)), ALT_DN.move(5, 10))

    # IAS Knob
    pygame.draw.rect(screen, (0,200,0), IAS_UP, border_radius=8)
    pygame.draw.rect(screen, (220,50,50), IAS_DN, border_radius=8)
    screen.blit(font.render("IAS +5", True, (0, 0, 0)), IAS_UP.move(5, 10))
    screen.blit(font.render("IAS -5", True, (0, 0, 0)), IAS_DN.move(5, 10))

    # Turn Knob
    pygame.draw.rect(screen, (0,200,0), TURN_UP, border_radius=8)
    pygame.draw.rect(screen, (220,50,50), TURN_DN, border_radius=8)
    screen.blit(font.render("TURN +", True, (0,0,0)), TURN_UP.move(10,10))
    screen.blit(font.render("TURN -", True, (0,0,0)), TURN_DN.move(10,10))

    # Readouts
    screen.blit(font.render(f"     SEL ALT => {int(ALTITUDE_CMD)} ft", True, (255, 255, 255)),
                (PFD_WIDTH + 90, 420))
    screen.blit(font.render(f"     SEL IAS => {int(IAS_CMD)} kt", True, (255, 255, 255)),
                (PFD_WIDTH + 90, 520))
    screen.blit(font.render(f"     BANK ANGLE : {bank_angle}°", True, (255,255,255)),
                (PFD_WIDTH + 90, 625))
    
    # G LOAD (TOP LEFT)
    if mode == "ROLLS":
        if g_factor >= 2.0:
            g_color = (255, 0, 0)       # Red warning
        elif g_factor >= 1.5:
            g_color = (255, 176, 0)     # Amber caution
        else:
            g_color = (0, 255, 0)       # Green normal

        screen.blit(
        font.render(f"G LOAD: {g_factor:.2f} G", True, g_color),
        (20, 70)
        )


    pygame.display.flip()

pygame.quit()
sys.exit()
