import sys
from dataclasses import dataclass
from datetime import timedelta

import pygame

from .airspeed import AirspeedIndicator
from .airspeed_little import AirspeedIndicatorLittle
from .altimeter import AltitudeIndicator
from .altimeter_little import AltitudeIndicatorLittle
from .attitude import ArtificalHorizon
from .heading import HeadingIndicator
from .vspeed import VerticalSpeedIndicator
from .vspeed_little import VerticalSpeedIndicatoLittle


# ===============================
# AIRCRAFT STATE
# ===============================
@dataclass
class AircraftState:
    roll: float
    pitch: float
    airspeed: float
    airspeed_cmd: float
    altitude: float
    altitude_cmd: float
    vspeed: float
    heading: float
    heading_cmd: float
    course: float


# ===============================
# PRIMARY FLIGHT DISPLAY
# ===============================
class PrimaryFlightDisplay:
    def __init__(self, resolution: tuple, **kwargs) -> None:
        self.resolution = resolution
        self.surface = pygame.Surface(resolution)
        self.surface_rect = self.surface.get_rect()

        self.game_clock = pygame.time.Clock()
        self.max_fps = kwargs.get("max_fps", None)
        self.fps = 0.0

        self.size = min(self.resolution)
        self.unit = self.size / 16

        # ---------------------------
        # INSTRUMENTS (DRAW TO SURFACE)
        # ---------------------------
        self.artifical_horizon = ArtificalHorizon(self.surface, size=self.size / 2)

        self.airspeed_indicator = AirspeedIndicator(
            self.surface,
            size=self.size / 2,
            position=(self.surface_rect.centerx - self.unit * 5, self.surface_rect.centery),
        )

        self.altitude_indicator = AltitudeIndicator(
            self.surface,
            size=self.size / 2,
            position=(self.surface_rect.centerx + self.unit * 5, self.surface_rect.centery),
        )

        self.vspeed_indicator = VerticalSpeedIndicator(
            self.surface,
            size=self.size / 2.5,
            position=(self.altitude_indicator.background_rect.right + self.size / 100,
                      self.surface_rect.centery),
        )

        self.heading_indicator = HeadingIndicator(
            self.surface,
            size=self.size / 2,
            position=(self.surface_rect.centerx,
                      self.surface_rect.centery + self.unit * 5),
        )

        # ---------------------------
        # MODES
        # ---------------------------
        self.masked = kwargs.get("masked", False)
        self.little = kwargs.get("little", False)

        if self.little:
            self.airspeed_indicator = AirspeedIndicatorLittle(
                self.surface,
                size=self.size / 2,
                position=(self.surface_rect.centerx - self.unit * 5,
                          self.surface_rect.centery),
            )
            self.altitude_indicator = AltitudeIndicatorLittle(
                self.surface,
                size=self.size / 2,
                position=(self.surface_rect.centerx + self.unit * 5,
                          self.surface_rect.centery),
            )
            self.vspeed_indicator = VerticalSpeedIndicatoLittle(
                self.surface,
                size=self.size / 2.5,
                position=(self.altitude_indicator.background_rect.right + self.size / 100,
                          self.surface_rect.centery),
            )

        self.text_color = (255, 255, 255)
        self.real_time = None
        self.sim_time = None

    # ===============================
    # UPDATE
    # ===============================
    def update(self, state: AircraftState, real_time: float = None, sim_time: float = None) -> None:
        self.state = state
        self.artifical_horizon.update(state.roll, state.pitch)
        self.airspeed_indicator.update(state.airspeed, state.airspeed_cmd)
        self.altitude_indicator.update(state.altitude, state.altitude_cmd)
        self.vspeed_indicator.update(state.vspeed)
        self.heading_indicator.update(state.heading, state.course, state.heading_cmd)
        self.real_time = real_time
        self.sim_time = sim_time

    # ===============================
    # DRAW
    # ===============================
    def draw(self, debug: bool = False) -> None:
        self.surface.fill((0, 0, 0))

        self.artifical_horizon.draw()
        self.airspeed_indicator.draw()
        self.vspeed_indicator.draw()
        self.altitude_indicator.draw()
        self.heading_indicator.draw()

        if debug:
            self.artifical_horizon.draw_aux_axis()

        self._draw_fps()
        if self.real_time is not None:
            self._draw_real_time()
        if self.sim_time is not None:
            self._draw_sim_time()

    # ===============================
    # TEXT
    # ===============================
    def _draw_fps(self):
        font = pygame.font.SysFont(None, 24)
        txt = font.render(f"FPS: {self.fps:.0f}", True, self.text_color)
        self.surface.blit(txt, (12, 12))

    def _draw_real_time(self):
        font = pygame.font.SysFont(None, 24)
        txt = font.render(
            "TIME: " + str(timedelta(seconds=self.real_time))[:-4],
            True,
            self.text_color,
        )
        self.surface.blit(txt, (12, 36))

    def _draw_sim_time(self):
        font = pygame.font.SysFont(None, 24)
        txt = font.render(
            "SIM: " + str(timedelta(seconds=self.sim_time))[:-4],
            True,
            self.text_color,
        )
        self.surface.blit(txt, (12, 60))

    # ===============================
    # FPS UPDATE
    # ===============================
    def tick(self):
        if self.max_fps is None:
            self.game_clock.tick()
        else:
            self.game_clock.tick(self.max_fps)
        self.fps = self.game_clock.get_fps()

    # ===============================
    # EXPOSE SURFACE
    # ===============================
    def get_surface(self):
        return self.surface
