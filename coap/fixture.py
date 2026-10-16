"""A rendered numeric fixture, NOT RoboDojo or a physical dynamics simulator.

Hidden object positions are used only by the renderer, contact fixture and judge.
The policy receives RGB, calibration and robot proprioception only.
"""
import numpy as np
from .perception import Camera, silhouette
from .state import Observation

CATALOG = {
    'red': {'rgb': [210, 45, 45], 'size': [0.04, 0.04, 0.04]},
    'blue': {'rgb': [45, 80, 210], 'size': [0.04, 0.04, 0.04]},
}


class NumericScene:
    def __init__(self, seed=0, slip_once=False):
        rng = np.random.default_rng(seed)
        self.camera = Camera(np.array([[300., 0, 160], [0, 300, 160], [0, 0, 1]]),
                             np.diag([1., -1., -1.]), np.array([0., 0., 1.]))
        self.positions = {name: np.array([rng.uniform(-0.25, -0.08), y, 0.02])
                          for name, y in [('red', -0.13), ('blue', 0.13)]}
        self.yaws = {n: rng.uniform(0, np.pi/2) for n in CATALOG}
        self.targets = {n: np.array([0.2, y, 0.02]) for n, y in [('red', -0.13), ('blue', 0.13)]}
        self.ee = np.array([0., 0., 0.25])
        self.open, self.held, self.step_count = True, None, 0
        self.slip_once, self.slipped = slip_once, False

    def observation(self):
        image = np.full((320, 320, 3), 150, np.uint8)
        for name, pos in self.positions.items():
            # Lifted cuboids rendered by a camera translated by object bottom height.
            cam = Camera(self.camera.K, self.camera.rotation,
                         self.camera.center-np.array([0, 0, pos[2]-0.02]))
            mask = silhouette(cam, pos[:2], CATALOG[name]['size'], self.yaws[name])
            image[mask > 0] = CATALOG[name]['rgb']
        width = 0.04 if self.held else (0.08 if self.open else 0.0)
        return Observation(image, self.ee.copy(), self.ee.copy(), self.open,
                           self.step_count, 'Sort red and blue blocks into target slots.',
                           gripper_width=width)

    def execute(self, action):
        self.step_count += 1
        if action.kind == 'move':
            self.ee = np.asarray(action.target).copy()
            if self.held:
                if self.slip_once and not self.slipped and self.ee[2] > 0.1:
                    self.slipped = True
                    self.positions[self.held][2] = 0.02
                    self.held = None
                else:
                    self.positions[self.held] = self.ee.copy()
        elif action.kind == 'close':
            self.open = False
            for name, pos in self.positions.items():
                if np.linalg.norm(pos-self.ee) < 0.025:
                    self.held = name
                    break
        elif action.kind == 'open':
            if self.held:
                self.positions[self.held][2] = 0.02
            self.open, self.held = True, None
        elif action.kind not in ('observe', 'check_hold', 'stop'):
            raise ValueError(action.kind)

    def judge(self):
        return all(np.linalg.norm(self.positions[n]-t) < 0.018 for n, t in self.targets.items())
