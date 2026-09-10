"""Kare cikislari (sink): headless PNG dizisi ve canli pygame penceresi.

Ikisi de `sinek.render.render()` ciktisini tuketir, yani gorunum aynidir.
"""

from __future__ import annotations

import os

import numpy as np

from .pngwrite import write_png
from .render import render


class NullSink:
    def emit(self, sim) -> None: ...
    def close(self) -> None: ...
    @property
    def alive(self) -> bool:
        return True


class FrameSink(NullSink):
    """Headless: her N adimda bir PNG kare yazar."""

    def __init__(self, cfg, out_dir: str):
        self.cfg = cfg
        self.every = max(1, int(cfg.get("viz.every", 10)))
        self.max_frames = int(cfg.get("viz.max_frames", 0)) or 10**9
        self.dir = os.path.join(out_dir, str(cfg.get("viz.frames_dir", "frames")))
        os.makedirs(self.dir, exist_ok=True)
        self.count = 0
        self.paths: list[str] = []

    def emit(self, sim) -> None:
        if sim.step_index % self.every or self.count >= self.max_frames:
            return
        path = os.path.join(self.dir, f"frame_{self.count:05d}.png")
        write_png(path, render(sim))
        self.paths.append(path)
        self.count += 1


class PygameSink(NullSink):
    """Canli pencere. pygame kurulu degilse anlasilir bir hata verir."""

    def __init__(self, cfg, out_dir: str):
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise SystemExit(
                "viz.mode: pygame icin pygame gerekli.  pip install pygame\n"
                "Alternatif: viz.mode: frames (ek bagimlilik istemez)."
            ) from exc
        self.pygame = pygame
        self.cfg = cfg
        self.every = max(1, int(cfg.get("viz.every", 1)))
        pygame.init()
        from .render import frame_size

        w, h = frame_size(cfg)
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption("Sinek Evrimi")
        self.clock = pygame.time.Clock()
        self.fps = int(cfg.get("viz.fps", 30))
        self._alive = True
        self.paused = False

    @property
    def alive(self) -> bool:
        return self._alive

    def emit(self, sim) -> None:
        pg = self.pygame
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._alive = False
            elif event.type == pg.KEYDOWN:
                if event.key in (pg.K_ESCAPE, pg.K_q):
                    self._alive = False
                elif event.key == pg.K_SPACE:
                    self.paused = not self.paused
        if sim.step_index % self.every:
            return
        frame = render(sim)                       # (H, W, 3)
        surf = pg.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
        self.screen.blit(surf, (0, 0))
        pg.display.flip()
        self.clock.tick(self.fps)
        while self.paused and self._alive:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._alive = False
                elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    self.paused = False
                elif event.type == pg.KEYDOWN and event.key in (pg.K_ESCAPE, pg.K_q):
                    self._alive = False
            self.clock.tick(20)

    def close(self) -> None:
        self.pygame.quit()


def make_sink(cfg, out_dir: str):
    mode = str(cfg.get("viz.mode", "none")).lower()
    if mode in ("none", "off", ""):
        return NullSink()
    if mode == "frames":
        return FrameSink(cfg, out_dir)
    if mode == "pygame":
        return PygameSink(cfg, out_dir)
    raise ValueError(f"bilinmeyen viz.mode={mode!r} (none | frames | pygame)")
