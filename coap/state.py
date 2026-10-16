from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import numpy as np


@dataclass
class ObjectState:
    name: str
    position: np.ndarray
    size: Tuple[float, float, float]
    yaw: float
    confidence: float
    error: float
    source: str
    measured_at: int


@dataclass
class Observation:
    rgb: np.ndarray
    joints: np.ndarray
    ee: np.ndarray
    gripper_open: bool
    step: int
    instruction: str
    robot_mask: Optional[np.ndarray] = None
    gripper_width: float = 0.0


@dataclass
class WorldState:
    objects: Dict[str, ObjectState] = field(default_factory=dict)
    joints: np.ndarray = field(default_factory=lambda: np.zeros(3))
    ee: np.ndarray = field(default_factory=lambda: np.zeros(3))
    gripper_open: bool = True
    stage: str = "observe"
    retries: int = 0
    memory: dict = field(default_factory=dict)

    def update(self, observation, measurements):
        self.joints = observation.joints.copy()
        self.ee = observation.ee.copy()
        self.gripper_open = observation.gripper_open
        # Missing detections never erase objects: occlusion preserves memory.
        self.objects.update({m.name: m for m in measurements})
