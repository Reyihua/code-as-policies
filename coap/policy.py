from dataclasses import dataclass
import numpy as np
from .state import WorldState
from .motion import transfer_waypoints


@dataclass
class Action:
    kind: str
    target: object = None


class TransferPolicy:
    """Sense, approach, close, lift, verify, carry, release, verify/recover."""
    def __init__(self, perception, targets, max_retries=2, clearance=0.16):
        self.perception, self.targets = perception, targets
        self.max_retries, self.clearance = max_retries, clearance
        self.state = WorldState()
        self.pending = []
        self.active = None
        self.failed = False
        self.trace = []

    def step(self, obs):
        measurements = self.perception.measure(obs)
        self.state.update(obs, measurements)
        s = self.state
        measured = {m.name: m for m in measurements}
        self.trace.append({'step': obs.step, 'stage': s.stage,
                           'visible': list(measured), 'remembered': list(s.objects),
                           'retries': s.retries, 'ee': s.ee.tolist()})
        if self.pending:
            action = self.pending.pop(0)
            s.stage = action.kind
            return action
        if self.active is not None:
            name = self.active
            obj = measured.get(name)
            target = np.asarray(self.targets[name])
            if obj is not None and np.linalg.norm(obj.position[:2]-target[:2]) < 0.018:
                s.memory[name] = 'verified'
                s.retries = 0
                self.active = None
            else:
                s.retries += 1
                if s.retries > self.max_retries:
                    self.failed, s.stage = True, 'failed'
                    return Action('stop')
                s.stage = 'recover'
        remaining = [n for n in self.targets if s.memory.get(n) != 'verified']
        if not remaining:
            s.stage = 'done'
            return Action('stop')
        name = remaining[0]
        # Persisted poses support memory, but stale measurements cannot initiate a grasp.
        if name not in measured:
            return Action('observe')
        self.active = name
        source = measured[name].position.copy()
        points = transfer_waypoints(source, self.targets[name], self.clearance)
        self.pending = [Action('move', points[0]), Action('move', points[1]),
                        Action('close'), Action('move', points[2]), Action('check_hold'),
                        Action('move', points[3]), Action('move', points[4]),
                        Action('open'), Action('move', points[3]), Action('observe')]
        return self.step_without_observation()

    def step_without_observation(self):
        action = self.pending.pop(0)
        self.state.stage = action.kind
        return action

    def hold_result(self, success):
        if not success:
            self.pending = [Action('open'), Action('observe')]
